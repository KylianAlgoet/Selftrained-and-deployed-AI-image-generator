"""EXP-034 - does the production stack survive as a long-lived service?

THE QUESTION. Every VRAM figure this project owns was measured under a rule
adopted after a real contamination incident: ONE CONFIGURATION PER OS PROCESS
(see docs/evidence/EXP-005/measurement-methodology-correction.md). The API is the
exact opposite of that rule - one process, resident for hours, swapping between
three LoRA adapters and between reference-conditioned and prompt-only requests.
EXP-019b and EXP-032 measured the stack at 7985.5 MiB of 8187.5 MiB physical,
leaving 202.0 MiB. Nothing has measured what repeated switching does to it.

THIS RUN DELIBERATELY BREAKS THE ONE-CONFIG-PER-PROCESS RULE. That is the point,
and it is the reason its numbers are SERVICE-RESIDENCY FIGURES that are NOT
comparable with the per-process benchmarks in EXP-016..EXP-032. They answer a
different question and must never be tabled beside them as if they did not.

THE MATRIX IS FROZEN BEFORE EXECUTION: six cases, run twice, identical inputs in
both cycles. It exercises repeated LoRA switching, reference-present ->
reference-absent and absent -> present transitions, a return to every style, and
therefore stale adapter state, stale IP-Adapter scale and stale reference state,
across a persistent process.

PASS CRITERIA ARE DECLARED BELOW, BEFORE ANY RESULT EXISTS. A repeated-output
mismatch is recorded as a FAILURE REQUIRING INVESTIGATION - it is NOT reported as
proof of adapter residue, because nondeterminism or any other state defect would
produce the same symptom, and telling those apart is the investigation, not the
conclusion.

Run (one process, no reload, nothing else on the GPU):
    .venv/Scripts/python.exe scripts/measure_service_residency.py
    .venv/Scripts/python.exe scripts/measure_service_residency.py --smoke
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from apps.api.pipeline import DEVICE_TOTAL_MB, ResidentPipeline  # noqa: E402
from apps.api.styles import (  # noqa: E402
    DEFAULT_IP_ADAPTER_SCALE,
    DEFAULT_LORA_WEIGHT,
)
from ml.inference.reference_schema import REFERENCES  # noqa: E402

EXP_ID = "EXP-034"

# --- Frozen inputs -----------------------------------------------------------

# One subject for all twelve requests. FP2-shared in the M6 final matrix, chosen
# there precisely because an identical subject across styles attributes the
# difference to the adapter rather than to the prompt.
SUBJECT = "a mountain and a rising sun"
SEED = 42
LORA_WEIGHT = DEFAULT_LORA_WEIGHT          # 0.7, DR-010
IP_ADAPTER_SCALE = DEFAULT_IP_ADAPTER_SCALE  # 0.55, DR-008

# R2: project-original, natively 512x1536 so it needs no crop at the deck format,
# and from the HOLDOUT split - no LoRA in this project has ever seen it.
REFERENCE_ID = "R2"

OUTPUT_ROOT = REPO / "outputs" / EXP_ID
RESULTS_PATH = REPO / "docs" / "evidence" / EXP_ID / "service-residency.jsonl"


@dataclass(frozen=True)
class Case:
    index: int
    style: str
    reference: bool


# Six cases. The ordering is what does the work: every adjacent pair changes the
# style, and the reference flag alternates, so both transition directions are
# covered and no style is ever followed by itself.
CASES: tuple[Case, ...] = (
    Case(1, "minimal-geometric", False),
    Case(2, "ukiyo-e", True),
    Case(3, "retro-poster", False),
    Case(4, "minimal-geometric", True),
    Case(5, "ukiyo-e", False),
    Case(6, "retro-poster", True),
)
CYCLES = 2
TOTAL_REQUESTS = len(CASES) * CYCLES  # 12

# --- Pass criteria, declared before execution --------------------------------

CRITERIA = {
    "all_requests_complete": f"{TOTAL_REQUESTS}/{TOTAL_REQUESTS} requests complete, no OOM",
    "one_adapter_per_request": "exactly one style LoRA active per request",
    "no_previous_adapter": "no previous style adapter remains active",
    "no_stale_reference": "prompt-only requests apply IP-Adapter scale 0.0",
    "repeat_byte_identical": "each case's cycle-2 output is byte-identical to its cycle-1 output",
    "allocated_growth_within_64mb": "same-case allocated VRAM grows by <= 64 MiB between cycles",
    "device_ceiling_respected": f"physical device use never exceeds {DEVICE_TOTAL_MB} MiB",
    "no_monotonic_growth": "allocated VRAM after generation does not rise monotonically",
}
ALLOCATED_GROWTH_LIMIT_MB = 64.0


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def evaluate(rows: list[dict]) -> dict:
    """Apply the declared criteria. Returns a verdict per criterion plus detail."""
    verdict: dict[str, object] = {}
    failures: list[str] = []

    completed = [r for r in rows if r["status"] == "ok"]
    verdict["all_requests_complete"] = len(completed) == TOTAL_REQUESTS

    verdict["one_adapter_per_request"] = all(
        len(r["active_adapters"]) == 1 for r in completed
    )
    verdict["no_previous_adapter"] = all(
        r["active_adapters"] == [r["style"]] for r in completed
    )
    verdict["no_stale_reference"] = all(
        (r["ip_adapter_scale_applied"] == 0.0) != r["reference_present"] for r in completed
    )

    by_case: dict[int, list[dict]] = {}
    for row in completed:
        by_case.setdefault(row["case"], []).append(row)

    repeat_ok = True
    repeat_detail = []
    growth_ok = True
    growth_detail = []
    for case_index, case_rows in sorted(by_case.items()):
        if len(case_rows) < 2:
            continue
        first, second = case_rows[0], case_rows[1]
        identical = first["image_sha256"] == second["image_sha256"]
        repeat_ok = repeat_ok and identical
        repeat_detail.append(
            {
                "case": case_index,
                "style": first["style"],
                "reference_present": first["reference_present"],
                "identical": identical,
                "cycle1_sha256": first["image_sha256"],
                "cycle2_sha256": second["image_sha256"],
            }
        )
        growth = round(second["allocated_after_mb"] - first["allocated_after_mb"], 2)
        within = growth <= ALLOCATED_GROWTH_LIMIT_MB
        growth_ok = growth_ok and within
        growth_detail.append({"case": case_index, "allocated_growth_mb": growth, "within": within})

    verdict["repeat_byte_identical"] = repeat_ok
    verdict["allocated_growth_within_64mb"] = growth_ok
    verdict["device_ceiling_respected"] = all(
        r["device_used_mb"] <= DEVICE_TOTAL_MB for r in completed
    )

    after = [r["allocated_after_mb"] for r in completed]
    strictly_rising = len(after) > 1 and all(b > a for a, b in zip(after, after[1:]))
    verdict["no_monotonic_growth"] = not strictly_rising

    for key, description in CRITERIA.items():
        if not verdict.get(key):
            failures.append(f"{key}: {description}")

    return {
        "verdict": verdict,
        "failures": failures,
        "repeat_detail": repeat_detail,
        "growth_detail": growth_detail,
        "passed": not failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="run only the first case, to prove the path end-to-end before the full matrix",
    )
    args = parser.parse_args(argv)

    from PIL import Image

    reference_spec = REFERENCES[REFERENCE_ID]
    reference_path = REPO / reference_spec.repo_path
    if not reference_path.is_file():
        print(f"reference {REFERENCE_ID} missing at {reference_spec.repo_path}")
        return 2

    plan = [(1, CASES[0])] if args.smoke else [
        (cycle, case) for cycle in range(1, CYCLES + 1) for case in CASES
    ]

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"{EXP_ID}: resident-service residency, {len(plan)} request(s)")
    print(f"  subject   {SUBJECT!r}  seed {SEED}  weight {LORA_WEIGHT}  scale {IP_ADAPTER_SCALE}")
    print(f"  reference {REFERENCE_ID} ({reference_spec.width}x{reference_spec.height})")
    print(f"  ceiling   {DEVICE_TOTAL_MB} MiB physical")
    print()

    pipeline = ResidentPipeline(REPO)
    rows: list[dict] = []
    started_all = time.perf_counter()

    for cycle, case in plan:
        label = f"cycle {cycle} case {case.index} {case.style}"
        label += " + reference" if case.reference else " prompt-only"
        print(f"  {label} ... ", end="", flush=True)

        reference_image = None
        if case.reference:
            with Image.open(reference_path) as raw:
                reference_image = raw.convert("RGB")

        row = {
            "exp_id": EXP_ID,
            "timestamp_utc": utc_now(),
            "cycle": cycle,
            "case": case.index,
            "style": case.style,
            "reference_present": case.reference,
            "reference_id": REFERENCE_ID if case.reference else "",
            "subject": SUBJECT,
            "seed": SEED,
            "lora_weight": LORA_WEIGHT,
            "ip_adapter_scale_requested": IP_ADAPTER_SCALE if case.reference else 0.0,
            "status": "ok",
            "error_type": "",
            "error_message": "",
        }

        try:
            outcome = pipeline.generate(
                style_key=case.style,
                subject_prompt=SUBJECT,
                seed=SEED,
                lora_weight=LORA_WEIGHT,
                ip_adapter_scale=IP_ADAPTER_SCALE,
                reference_image=reference_image,
                deadline_seconds=None,  # no deadline: this measures cost, not timeout
            )
        except Exception as err:  # noqa: BLE001 - a failed run is a recorded result
            row["status"] = "failed"
            row["error_type"] = type(err).__name__
            row["error_message"] = str(err).strip().splitlines()[0][:400] if str(err) else ""
            rows.append(row)
            print(f"FAILED {row['error_type']}: {row['error_message']}")
            continue

        name = (
            f"{EXP_ID}__cycle{cycle}__case{case.index}__{case.style}"
            f"__{'ref' if case.reference else 'promptonly'}__seed{SEED}.png"
        )
        (OUTPUT_ROOT / name).write_bytes(outcome.image_png)

        row.update(
            {
                "active_adapters": list(outcome.active_adapters),
                "loaded_adapter_count": len(outcome.active_adapters),
                "live_lora_modules": outcome.live_lora_modules,
                "ip_adapter_scale_applied": outcome.ip_adapter_scale_applied,
                "adapter_sha256": outcome.adapter_sha256,
                "prompt": outcome.prompt,
                "image_sha256": outcome.image_sha256,
                "output_path": f"outputs/{EXP_ID}/{name}",
                "allocated_before_mb": outcome.allocated_before_mb,
                "allocated_after_mb": outcome.allocated_after_mb,
                "reserved_before_mb": outcome.reserved_before_mb,
                "reserved_after_mb": outcome.reserved_after_mb,
                "peak_allocated_mb": outcome.peak_allocated_mb,
                "peak_reserved_mb": outcome.peak_reserved_mb,
                "device_used_mb": outcome.device_used_mb,
                "spare_device_mb": round(DEVICE_TOTAL_MB - outcome.device_used_mb, 2),
                "process_rss_mb": outcome.process_rss_mb,
                "generate_seconds": outcome.generate_seconds,
                "steps_run": outcome.steps_run,
            }
        )
        rows.append(row)
        print(
            f"ok  {outcome.generate_seconds}s  "
            f"alloc {outcome.allocated_after_mb} MiB  "
            f"device {outcome.device_used_mb} MiB  "
            f"adapters {list(outcome.active_adapters)}  "
            f"sha {outcome.image_sha256[:12]}"
        )

    wall = round(time.perf_counter() - started_all, 2)

    with RESULTS_PATH.open("a", encoding="utf-8", newline="") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    print()
    print(f"  {len(rows)} row(s) in {wall}s -> {RESULTS_PATH.relative_to(REPO)}")

    if args.smoke:
        ok = all(r["status"] == "ok" for r in rows)
        print("  SMOKE " + ("PASS" if ok else "FAIL"))
        return 0 if ok else 1

    report = evaluate(rows)
    print()
    print("  Declared criteria:")
    for key, description in CRITERIA.items():
        mark = "PASS" if report["verdict"].get(key) else "FAIL"
        print(f"    [{mark}] {description}")

    print()
    print("  Repeated-case outputs (cycle 1 vs cycle 2):")
    for detail in report["repeat_detail"]:
        mark = "identical" if detail["identical"] else "DIFFERENT"
        print(
            f"    case {detail['case']} {detail['style']:<18} "
            f"{'ref' if detail['reference_present'] else 'prompt-only':<11} {mark}"
        )

    print()
    if report["passed"]:
        print(f"  {EXP_ID}: PASS on every declared criterion")
    else:
        print(f"  {EXP_ID}: FAILED - {len(report['failures'])} criterion/criteria")
        for failure in report["failures"]:
            print(f"    - {failure}")
        print()
        print("  A repeated-output mismatch is a failure REQUIRING INVESTIGATION.")
        print("  It does not by itself prove adapter residue: nondeterminism or another")
        print("  state defect would look the same. Stop and report rather than concluding.")

    verdict_path = RESULTS_PATH.parent / "service-residency-verdict.json"
    verdict_path.write_text(
        json.dumps(
            {
                "exp_id": EXP_ID,
                "timestamp_utc": utc_now(),
                "requests": len(rows),
                "wall_seconds": wall,
                "criteria": CRITERIA,
                **report,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(f"  verdict -> {verdict_path.relative_to(REPO)}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
