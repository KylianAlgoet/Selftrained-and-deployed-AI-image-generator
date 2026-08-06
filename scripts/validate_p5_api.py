"""Prototype 5 end-to-end validation against a REAL uvicorn process.

Not a test-client run. This starts the service the way the demo starts it -
`--workers 1`, no reload - and drives it over HTTP, so what is recorded is the
behaviour of the thing that ships.

Three phases, each with a declared expectation:

  A. Serving       - 6 generations: prompt-only and reference-conditioned for
                     each of the three production styles.
  B. Integrity     - a DELIBERATELY CORRUPTED COPY of one adapter must be
                     refused with 503, and the service must then serve a
                     different style successfully WITHOUT a restart. The real
                     checkpoints are never touched: R14 makes them
                     unregenerable, so they are copied, and the copy is damaged.
  C. Deadline      - a server whose deadline is shorter than a real generation
                     must return 504 having ACTUALLY stopped the denoising loop,
                     and must release the busy lock afterwards.

GPU cost: 6 (A) + 1 (B recovery) + 2 (C, both aborted early) = 9 generations.

Phases can be run selectively. That exists for a reason rather than for
convenience: M7 declared a hard cap of 25 real generations before any of them
ran, and re-running an already-passed phase to correct a measurement in another
would spend that budget on nothing. Rows for unselected phases are preserved.

Run:
    .venv/Scripts/python.exe scripts/validate_p5_api.py
    .venv/Scripts/python.exe scripts/validate_p5_api.py --phases C
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import httpx  # noqa: E402

from apps.api.styles import PRODUCTION_STYLES, production_style  # noqa: E402
from ml.inference.reference_schema import REFERENCES  # noqa: E402

HOST = "127.0.0.1"
SUBJECT = "a mountain and a rising sun"
SEED = 42
REFERENCE_ID = "R2"

EVIDENCE_DIR = REPO / "docs" / "evidence" / "prototype-5"
OUTPUT_DIR = REPO / "outputs" / "prototype-5"
RESULTS_PATH = EVIDENCE_DIR / "api-validation.jsonl"

rows: list[dict] = []
failures: list[str] = []


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record(**fields) -> None:
    rows.append({"timestamp_utc": utc_now(), **fields})


def fail(message: str) -> None:
    failures.append(message)


@contextmanager
def api_server(port: int, env_overrides: dict[str, str] | None = None, boot_timeout: float = 180.0):
    """Start the real server on `port`, yield its base URL, always stop it."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env.update(env_overrides or {})

    command = [
        sys.executable, "-m", "uvicorn", "apps.api.main:app",
        "--host", HOST, "--port", str(port), "--workers", "1",
        "--log-level", "warning",
    ]
    process = subprocess.Popen(command, cwd=REPO, env=env)
    base = f"http://{HOST}:{port}"
    try:
        deadline = time.perf_counter() + boot_timeout
        while True:
            if process.poll() is not None:
                raise RuntimeError(f"the server exited during start-up with code {process.returncode}")
            try:
                if httpx.get(f"{base}/api/health", timeout=5.0).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if time.perf_counter() > deadline:
                raise TimeoutError("the server did not become healthy in time")
            time.sleep(0.5)
        yield base
    finally:
        process.terminate()
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:  # pragma: no cover - defensive
            process.kill()


def post_generate(base: str, style: str, reference: Path | None, timeout: float) -> httpx.Response:
    data = {
        "prompt": SUBJECT,
        "style": style,
        "seed": str(SEED),
        "lora_weight": "0.7",
        "ip_adapter_scale": "0.55",
    }
    if reference is None:
        return httpx.post(f"{base}/api/generate", data=data, timeout=timeout)
    with reference.open("rb") as handle:
        files = {"reference_image": (reference.name, handle, "image/png")}
        return httpx.post(f"{base}/api/generate", data=data, files=files, timeout=timeout)


def phase_a(reference_path: Path) -> None:
    """Six real generations over HTTP: every style, with and without a reference."""
    print("Phase A - serving, 6 generations over HTTP")
    with api_server(8021) as base:
        health = httpx.get(f"{base}/api/health", timeout=10).json()
        print(f"  health: pid {health['pid']}, cuda {health['cuda_available']}, "
              f"pipeline_loaded {health['pipeline_loaded']}, guard {health['single_worker_guard']}")
        record(phase="A", check="health", response=health)

        styles = httpx.get(f"{base}/api/styles", timeout=10).json()
        record(phase="A", check="styles", count=len(styles["styles"]))
        if [s["key"] for s in styles["styles"]] != [s.key for s in PRODUCTION_STYLES]:
            fail("A: /api/styles did not list the three production styles")

        for style in PRODUCTION_STYLES:
            for reference in (None, reference_path):
                kind = "reference" if reference else "prompt-only"
                started = time.perf_counter()
                response = post_generate(base, style.key, reference, timeout=300)
                elapsed = round(time.perf_counter() - started, 2)

                if response.status_code != 200:
                    fail(f"A: {style.key} {kind} returned {response.status_code}")
                    record(phase="A", style=style.key, kind=kind,
                           status=response.status_code, body=response.text[:300])
                    continue

                body = response.json()
                meta = body["metadata"]
                image = httpx.get(f"{base}{body['image_url']}", timeout=60)
                name = f"P5__{style.key}__{'ref' if reference else 'promptonly'}__seed{SEED}.png"
                (OUTPUT_DIR / name).write_bytes(image.content)

                ok = (
                    meta["active_adapters"] == [style.key]
                    and meta["lora_run_id"] == style.run_id
                    and meta["lora_checkpoint_step"] == style.checkpoint_step
                    and meta["reference_present"] is (reference is not None)
                    and image.status_code == 200
                    and image.headers["content-type"] == "image/png"
                )
                if not ok:
                    fail(f"A: {style.key} {kind} metadata or image did not check out")

                print(f"  {style.key:<18} {kind:<11} {elapsed:>6.2f}s  "
                      f"adapters {meta['active_adapters']}  "
                      f"scale {meta['ip_adapter_scale']}  "
                      f"spare {meta['spare_device_mb']} MiB  "
                      f"warnings {len(body['warnings'])}")

                record(phase="A", style=style.key, kind=kind, status=200,
                       wall_seconds=elapsed, output=f"outputs/prototype-5/{name}",
                       image_bytes=len(image.content), metadata=meta,
                       warnings=body["warnings"], checks_passed=ok)


def phase_b() -> None:
    """The integrity gate, proved against a corrupted COPY."""
    print()
    print("Phase B - integrity gate against a corrupted copy (real checkpoints untouched)")
    sandbox = REPO / "outputs" / "p5-integrity-sandbox"
    if sandbox.exists():
        shutil.rmtree(sandbox)
    try:
        damaged = production_style("retro-poster")
        for style in PRODUCTION_STYLES:
            target = style.adapter_path(sandbox)
            target.parent.mkdir(parents=True, exist_ok=True)
            if style.key == damaged.key:
                # Same SIZE, different CONTENT: this proves the sha256 check is
                # what rejects it, not the length check in front of it.
                target.write_bytes(b"\x00" * style.size_bytes)
            else:
                shutil.copy2(style.adapter_path(REPO), target)

        with api_server(8022, {"CHECKPOINT_ROOT": str(sandbox)}) as base:
            response = post_generate(base, damaged.key, None, timeout=300)
            body = response.json()
            print(f"  corrupted {damaged.key}: HTTP {response.status_code} -> {body.get('error')}")
            if response.status_code != 503:
                fail(f"B: corrupted adapter returned {response.status_code}, expected 503")
            if ".safetensors" in response.text or "outputs" in response.text:
                fail("B: the error response leaked a path")
            record(phase="B", check="corrupted_adapter", style=damaged.key,
                   status=response.status_code, body=body)

            health = httpx.get(f"{base}/api/health", timeout=10).json()
            if health["generation_in_progress"]:
                fail("B: the lock was still held after the failure")

            # Recovery WITHOUT a restart: a different, intact style must serve.
            recovery = post_generate(base, "minimal-geometric", None, timeout=300)
            print(f"  recovery minimal-geometric: HTTP {recovery.status_code}")
            if recovery.status_code != 200:
                fail(f"B: recovery returned {recovery.status_code}, expected 200")
            record(phase="B", check="recovery_without_restart", style="minimal-geometric",
                   status=recovery.status_code,
                   metadata=recovery.json().get("metadata") if recovery.status_code == 200 else None)
    finally:
        if sandbox.exists():
            shutil.rmtree(sandbox)


def phase_c() -> None:
    """The deadline must stop real GPU work, not just answer early."""
    print()
    print("Phase C - deadline abort on real GPU work")
    with api_server(8023, {"GENERATION_TIMEOUT_SECONDS": "5"}) as base:
        # The FIRST request to a cold server spends most of its wall clock
        # loading ~5 GB of weights, which says nothing about whether the
        # denoising loop stopped early. It warms the pipeline and is recorded as
        # such; the SECOND request is the measured one.
        warm_started = time.perf_counter()
        warm = post_generate(base, "minimal-geometric", None, timeout=300)
        warm_elapsed = round(time.perf_counter() - warm_started, 2)
        print(f"  warm-up (cold load + abort): HTTP {warm.status_code} after {warm_elapsed}s")
        record(phase="C", check="deadline_abort_cold", status=warm.status_code,
               wall_seconds=warm_elapsed, body=warm.json(),
               note="wall clock includes the one-off model load, so it is not an abort measurement")

        started = time.perf_counter()
        response = post_generate(base, "minimal-geometric", None, timeout=300)
        elapsed = round(time.perf_counter() - started, 2)
        body = response.json()
        print(f"  warmed: HTTP {response.status_code} after {elapsed}s -> {body.get('detail')}")

        if response.status_code != 504:
            fail(f"C: expected 504, got {response.status_code}")

        # Two independent pieces of evidence that the work actually stopped: the
        # reported step count, and the wall clock of a warmed request.
        detail = body.get("detail", "")
        numbers = [int(token) for token in detail.replace(".", " ").split() if token.isdigit()]
        steps_run = numbers[0] if len(numbers) > 0 else None
        steps_total = numbers[1] if len(numbers) > 1 else None
        if steps_run is None or steps_total is None or steps_run >= steps_total:
            fail(f"C: the response does not evidence an early stop: {detail!r}")
        else:
            print(f"  stopped after {steps_run} of {steps_total} denoising steps")

        if elapsed > 12:
            fail(f"C: the warmed abort took {elapsed}s, which is not an early stop")

        health = httpx.get(f"{base}/api/health", timeout=10).json()
        if health["generation_in_progress"]:
            fail("C: the lock was still held after the deadline abort")
        print(f"  lock released: {not health['generation_in_progress']}")

        record(phase="C", check="deadline_abort", status=response.status_code,
               wall_seconds=elapsed, body=body, steps_run=steps_run, steps_total=steps_total,
               lock_released=not health["generation_in_progress"])


def merge_and_write(selected: set[str]) -> int:
    """Replace rows for the phases just run; keep rows for the phases that were not."""
    preserved: list[dict] = []
    if RESULTS_PATH.is_file():
        for line in RESULTS_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            previous = json.loads(line)
            if previous.get("phase") not in selected:
                preserved.append(previous)

    merged = preserved + rows
    with RESULTS_PATH.open("w", encoding="utf-8", newline="") as handle:
        for row in merged:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    return len(merged)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phases", default="ABC", help="which phases to run, e.g. 'C'")
    args = parser.parse_args()
    selected = {character.upper() for character in args.phases}

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    reference_path = REPO / REFERENCES[REFERENCE_ID].repo_path
    if not reference_path.is_file():
        print(f"reference {REFERENCE_ID} missing")
        return 2

    if "A" in selected:
        phase_a(reference_path)
    if "B" in selected:
        phase_b()
    if "C" in selected:
        phase_c()

    total = merge_and_write(selected)
    print()
    print(f"  ran phases {sorted(selected)}; {len(rows)} new rows, {total} total "
          f"-> {RESULTS_PATH.relative_to(REPO)}")
    if failures:
        print(f"  VALIDATION FAILED - {len(failures)} problem(s):")
        for failure in failures:
            print(f"    - {failure}")
        return 1
    print(f"  PHASES {''.join(sorted(selected))} PASSED on every declared expectation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
