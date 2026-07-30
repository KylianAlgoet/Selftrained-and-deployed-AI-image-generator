"""Prototype 1 base-model benchmark runner (RQ2, RQ8) - inference only.

Runs ONE model per process invocation, on purpose: VRAM is only reliably
released when the process exits, so the orchestrator (`run_benchmarks.py`)
spawns a fresh subprocess per candidate rather than trusting in-process cleanup.

Two tracks, reported separately and never merged:
  Track A - every candidate at 512x512 with identical settings. The controlled
            feasibility comparison (speed, VRAM, reliability).
  Track B - each candidate at the resolution it was designed for (SDXL 1024).
            The fair basis for visual-quality judgement.
Track B coincides with Track A for the two 512-native candidates; that is a
finding about those models, not a gap in the method.

Honesty rules enforced in code, not just prose:
  * Settings are never silently changed after a failure. A deeper memory tier is
    entered only after a failure has been recorded as its own result row, and the
    tier travels with every subsequent row.
  * Failures and timeouts are written as rows (status=failed/timeout), so they
    cannot quietly disappear from the results table.
  * Model revisions are pinned to an immutable commit SHA resolved at run time;
    a moving `main` branch is never benchmarked.
  * This module produces measurements only. It renders no quality verdict -
    rubric scoring happens at the human-review gate.

Run:
    .venv/Scripts/python.exe -m ml.inference.benchmark --model sd15 --exp EXP-002
"""

import argparse
import hashlib
import json
import sys
import threading
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from ml.evaluation import prompt_kit
from ml.inference.bench_schema import (
    MEMORY_TIERS,
    MODELS,
    STATUS_FAILED,
    STATUS_OK,
    STATUS_TIMEOUT,
    ModelSpec,
    ResultRow,
    append_jsonl,
    build_output_filename,
    next_tier,
    read_jsonl,
    render_summary_markdown,
    summarize,
    write_csv,
)

REPO = Path(__file__).resolve().parents[2]
OUTPUTS = REPO / "outputs"
EVIDENCE = REPO / "docs" / "evidence"

GENERATION_TIMEOUT_SECONDS = 300.0
SAMPLE_INTERVAL_SECONDS = 0.5
MIB = 1024**2


class GenerationTimeout(RuntimeError):
    """Raised from the step callback when a single generation exceeds its budget."""


# --- resource sampling -------------------------------------------------------


class ResourceSampler(threading.Thread):
    """Samples device-level VRAM and process RSS while a generation runs.

    Device-level usage (total - free) is what nvidia-smi reports as memory.used;
    it includes the CUDA context that the torch allocator cannot see. Sampled
    in-process because spawning nvidia-smi every interval would cost more than
    the measurement is worth.
    """

    def __init__(self, torch, psutil_process, interval: float = SAMPLE_INTERVAL_SECONDS):
        super().__init__(daemon=True)
        self._torch = torch
        self._process = psutil_process
        self._interval = interval
        # NOT `self._stop`: that name shadows threading.Thread._stop(), an internal
        # method join() calls, and every join() then dies with
        # "'Event' object is not callable". Found by the one-image smoke test.
        self._stop_event = threading.Event()
        self.peak_device_used_mb = 0.0
        self.peak_process_rss_mb = 0.0

    def run(self) -> None:
        while not self._stop_event.is_set():
            self._sample()
            self._stop_event.wait(self._interval)
        self._sample()  # final sample so short runs are never left at zero

    def _sample(self) -> None:
        try:
            free, total = self._torch.cuda.mem_get_info()
            self.peak_device_used_mb = max(self.peak_device_used_mb, (total - free) / MIB)
        except Exception:  # noqa: BLE001 - sampling must never break a benchmark
            pass
        try:
            self.peak_process_rss_mb = max(self.peak_process_rss_mb, self._process.memory_info().rss / MIB)
        except Exception:  # noqa: BLE001
            pass

    def stop(self) -> None:
        """Never raises. It is called from a `finally`, so an exception here would
        destroy the result row for a run that actually succeeded - which is how
        the shadowed-attribute bug above first manifested."""
        try:
            self._stop_event.set()
            self.join(timeout=5)
        except Exception as err:  # noqa: BLE001
            print(f"  (resource sampler teardown failed, measurements may be partial: {err!r})")


# --- pipeline construction ---------------------------------------------------


def resolve_revision(repo_id: str) -> str:
    """Pin to an immutable commit SHA so 'reproducible' means something."""
    from huggingface_hub import HfApi

    info = HfApi().model_info(repo_id)
    if not info.sha:
        raise RuntimeError(f"could not resolve a commit SHA for {repo_id}")
    return info.sha


def apply_memory_tier(pipe, tier: int) -> None:
    """Tiers are cumulative. Called only after a recorded failure at a lower tier."""
    if tier >= 1:
        pipe.enable_attention_slicing()
    if tier >= 2:
        pipe.enable_vae_slicing()
        if hasattr(pipe, "enable_vae_tiling"):
            pipe.enable_vae_tiling()
    if tier >= 3:
        pipe.enable_model_cpu_offload()
    if tier >= 4:
        pipe.enable_sequential_cpu_offload()


def load_pipeline(spec: ModelSpec, revision: str, tier: int, dtype_name: str):
    """Returns (pipe, load_seconds, safety_present, safety_enabled, vae_variant)."""
    import torch
    from diffusers import AutoPipelineForText2Image, DPMSolverMultistepScheduler

    dtype = getattr(torch, dtype_name)
    start = time.perf_counter()
    pipe = AutoPipelineForText2Image.from_pretrained(
        spec.repo_id,
        revision=revision,
        torch_dtype=dtype,
        use_safetensors=True,
    )

    # Same scheduler for every candidate, constructed explicitly, so the sampler
    # is a controlled constant instead of three different pipeline defaults.
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

    # Safety-checker policy: disabled uniformly for EVERY candidate that ships
    # one, never for some and not others. Local research only, no public
    # endpoint in M3, no NSFW prompts, licence-verified art dataset. Both
    # presence and enablement are recorded, because lower VRAM from lacking an
    # auxiliary checker must never be read as base-model efficiency.
    safety_present = "safety_checker" in getattr(pipe, "components", {})
    safety_enabled = False
    if safety_present:
        pipe.safety_checker = None
        if hasattr(pipe, "feature_extractor"):
            pipe.feature_extractor = None

    vae_variant = "pipeline default"

    if tier >= 3:
        # Offload helpers move modules themselves; calling .to("cuda") as well
        # would defeat them.
        apply_memory_tier(pipe, tier)
    else:
        pipe = pipe.to("cuda")
        apply_memory_tier(pipe, tier)

    pipe.set_progress_bar_config(disable=True)
    load_seconds = round(time.perf_counter() - start, 3)
    return pipe, load_seconds, safety_present, safety_enabled, vae_variant


# --- a single measured run ---------------------------------------------------


def generate_once(pipe, torch, prompt_text: str, seed: int, width: int, height: int) -> tuple:
    """Returns (image, generate_seconds). Timing is synchronised on both sides -
    CUDA is asynchronous, so unsynchronised timing would be fiction."""
    generator = torch.Generator(device="cuda").manual_seed(seed)
    deadline = time.perf_counter() + GENERATION_TIMEOUT_SECONDS

    def on_step_end(pipeline, step, timestep, callback_kwargs):
        if time.perf_counter() > deadline:
            raise GenerationTimeout(
                f"generation exceeded {GENERATION_TIMEOUT_SECONDS:.0f}s budget at step {step}"
            )
        return callback_kwargs

    torch.cuda.synchronize()
    start = time.perf_counter()
    result = pipe(
        prompt=prompt_text,
        negative_prompt=prompt_kit.NEGATIVE_PROMPT,
        num_inference_steps=prompt_kit.STEPS,
        guidance_scale=prompt_kit.GUIDANCE_SCALE,
        width=width,
        height=height,
        generator=generator,
        callback_on_step_end=on_step_end,
    )
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    return result.images[0], round(elapsed, 3)


def sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_track(
    spec: ModelSpec,
    exp_id: str,
    track: str,
    resolution: tuple[int, int],
    dtype_name: str,
    revision: str,
    jsonl_path: Path,
    warmup: bool = True,
    prompts: tuple = (),
    seeds: tuple = (),
) -> list[ResultRow]:
    """Benchmark one (model, track, resolution). Escalates memory tiers only
    after recording the failure that justified the escalation."""
    import psutil
    import torch
    from diffusers import __version__ as diffusers_version

    width, height = resolution
    prompts = prompts or prompt_kit.PROMPTS
    seeds = seeds or prompt_kit.SEEDS
    process = psutil.Process()
    gpu_name = torch.cuda.get_device_name(0)
    out_dir = OUTPUTS / exp_id
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[ResultRow] = []
    tier = 0
    pipe = None
    load_seconds: float | str = "not measured"
    safety_present = safety_enabled = False
    vae_variant = "pipeline default"

    def base_row(**overrides) -> ResultRow:
        defaults = dict(
            exp_id=exp_id,
            track=track,
            timestamp_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            model_repo_id=spec.repo_id,
            model_revision_sha=revision,
            torch_version=torch.__version__,
            torch_cuda_version=str(torch.version.cuda),
            diffusers_version=diffusers_version,
            gpu_name=gpu_name,
            dtype=dtype_name,
            scheduler=prompt_kit.SCHEDULER,
            prompt_id="",
            prompt_sha256="",
            negative_prompt_sha256=prompt_kit.text_sha256(prompt_kit.NEGATIVE_PROMPT),
            seed=0,
            width=width,
            height=height,
            steps=prompt_kit.STEPS,
            guidance_scale=prompt_kit.GUIDANCE_SCALE,
            memory_tier=tier,
            safety_checker_present=safety_present,
            safety_checker_enabled=safety_enabled,
            vae_variant=vae_variant,
            load_seconds=load_seconds,
            generate_seconds="not measured",
            peak_vram_allocated_mb="not measured",
            peak_vram_reserved_mb="not measured",
            peak_device_used_mb="not measured",
            peak_process_rss_mb="not measured",
            output_sha256="",
            status=STATUS_OK,
        )
        defaults.update(overrides)
        return ResultRow(**defaults)

    while pipe is None:
        try:
            print(f"  loading {spec.repo_id} at tier {tier} ({MEMORY_TIERS[tier]})")
            pipe, load_seconds, safety_present, safety_enabled, vae_variant = load_pipeline(
                spec, revision, tier, dtype_name
            )
        except Exception as err:  # noqa: BLE001
            row = base_row(
                status=STATUS_FAILED,
                error_type=type(err).__name__,
                error_message=str(err).splitlines()[0][:400],
                prompt_id="(load)",
            )
            rows.append(row)
            append_jsonl(row, jsonl_path)
            print(f"  LOAD FAILED at tier {tier}: {type(err).__name__}: {str(err).splitlines()[0][:200]}")
            escalated = next_tier(tier)
            if escalated is None:
                print("  no comparable memory tier remains - model declared infeasible here")
                return rows
            tier = escalated
            continue

    if warmup:
        # Discarded: the first generation includes kernel autotuning and would
        # inflate the measurement. Load time is recorded separately above.
        print(f"  warm-up at {width}x{height} (discarded)")
        try:
            generate_once(pipe, torch, prompt_kit.PROMPTS[0].text, prompt_kit.SEEDS[0], width, height)
        except Exception as err:  # noqa: BLE001
            print(f"  warm-up failed ({type(err).__name__}) - continuing to measured runs")

    for prompt in prompts:
        for seed in seeds:
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.synchronize()
            sampler = ResourceSampler(torch, process)
            sampler.start()
            status, error_type, error_message = STATUS_OK, "", ""
            generate_seconds: float | str = "not measured"
            output_sha, output_path = "", ""

            try:
                image, generate_seconds = generate_once(pipe, torch, prompt.text, seed, width, height)
                filename = build_output_filename(
                    exp_id, spec.slug, track, prompt.id, width, height, seed, prompt_kit.STEPS,
                    prompt_kit.GUIDANCE_SCALE, tier,
                )
                destination = out_dir / filename
                image.save(destination)
                output_sha = sha256_bytes(destination)
                output_path = str(destination.relative_to(REPO)).replace("\\", "/")
            except GenerationTimeout as err:
                status, error_type, error_message = STATUS_TIMEOUT, type(err).__name__, str(err)[:400]
            except Exception as err:  # noqa: BLE001
                status, error_type, error_message = STATUS_FAILED, type(err).__name__, str(err).splitlines()[0][:400]
            finally:
                sampler.stop()

            row = base_row(
                prompt_id=prompt.id,
                prompt_sha256=prompt_kit.text_sha256(prompt.text),
                seed=seed,
                memory_tier=tier,
                safety_checker_present=safety_present,
                safety_checker_enabled=safety_enabled,
                vae_variant=vae_variant,
                load_seconds=load_seconds,
                generate_seconds=generate_seconds,
                peak_vram_allocated_mb=round(torch.cuda.max_memory_allocated() / MIB, 2),
                peak_vram_reserved_mb=round(torch.cuda.max_memory_reserved() / MIB, 2),
                peak_device_used_mb=round(sampler.peak_device_used_mb, 2),
                peak_process_rss_mb=round(sampler.peak_process_rss_mb, 2),
                output_sha256=output_sha,
                status=status,
                error_type=error_type,
                error_message=error_message,
                output_path=output_path,
            )
            rows.append(row)
            append_jsonl(row, jsonl_path)
            marker = "ok" if status == STATUS_OK else status.upper()
            print(
                f"  [{marker}] {prompt.id} seed={seed} {width}x{height} "
                f"{generate_seconds}s alloc={row.peak_vram_allocated_mb}MiB "
                f"device={row.peak_device_used_mb}MiB"
                + (f" :: {error_type}: {error_message[:120]}" if error_type else "")
            )

    del pipe
    torch.cuda.empty_cache()
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prototype 1 base-model benchmark (inference only)")
    parser.add_argument("--model", required=True, choices=sorted(MODELS), help="candidate key")
    parser.add_argument("--exp", required=True, help="experiment id, e.g. EXP-002")
    parser.add_argument("--dtype", default="float16", choices=["float16", "bfloat16", "float32"])
    parser.add_argument("--tracks", default="A,B", help="comma-separated tracks to run (A,B)")
    parser.add_argument("--probes", action="store_true", help="also run supplementary out-of-distribution probes")
    parser.add_argument("--no-warmup", action="store_true", help="skip the discarded warm-up generation")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="one prompt, one seed, Track A only: proves download/cache/pipeline/VAE/output "
        "before committing to a long run (research-process rule)",
    )
    args = parser.parse_args(argv)

    import torch

    if not torch.cuda.is_available():
        print("CUDA is not available - refusing to run. Fix the EXP-001 gate first.", file=sys.stderr)
        return 2

    spec = MODELS[args.model]
    evidence_dir = EVIDENCE / args.exp
    evidence_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = evidence_dir / f"results-{spec.slug}.jsonl"
    if jsonl_path.exists():
        jsonl_path.unlink()  # a re-run replaces its own results rather than appending twice

    revision = resolve_revision(spec.repo_id)
    print(f"\n=== {args.exp} :: {spec.repo_id} ===")
    print(f"pinned revision: {revision}")
    print(f"kit fingerprint: {prompt_kit.kit_fingerprint()}")

    requested = [t.strip().upper() for t in args.tracks.split(",") if t.strip()]
    plan: list[tuple[str, tuple[int, int]]] = []
    prompts: tuple = ()
    seeds: tuple = ()
    if args.smoke:
        plan = [("A", prompt_kit.TRACK_A_RESOLUTION)]
        prompts = (prompt_kit.PROMPTS[0],)
        seeds = (prompt_kit.SEEDS[0],)
        print("SMOKE MODE: one prompt, one seed, Track A only")
    else:
        if "A" in requested:
            plan.append(("A", prompt_kit.TRACK_A_RESOLUTION))
        if "B" in requested:
            plan.append(("B", spec.track_b_resolution))
        if args.probes:
            plan.extend(("probe", resolution) for resolution in spec.probe_resolutions)

    all_rows: list[ResultRow] = []
    for track, resolution in plan:
        if track == "B" and resolution == prompt_kit.TRACK_A_RESOLUTION and any(t == "A" for t, _ in plan):
            print(
                f"\n-- Track B for {spec.slug} is {resolution[0]}x{resolution[1]}, identical to Track A. "
                "Recorded as a property of this candidate; not re-run."
            )
            continue
        print(f"\n-- Track {track} @ {resolution[0]}x{resolution[1]} --")
        all_rows += run_track(
            spec, args.exp, track, resolution, args.dtype, revision, jsonl_path,
            warmup=not args.no_warmup, prompts=prompts, seeds=seeds,
        )

    rows = read_jsonl(jsonl_path)
    write_csv(rows, evidence_dir / f"results-{spec.slug}.csv")
    summaries = summarize(rows)
    (evidence_dir / f"summary-{spec.slug}.md").write_text(
        render_summary_markdown(summaries, f"{args.exp} measurements - {spec.repo_id}"), encoding="utf-8"
    )
    (evidence_dir / f"revision-{spec.slug}.json").write_text(
        json.dumps(
            {
                "repo_id": spec.repo_id,
                "revision_sha": revision,
                "licence": spec.licence,
                "note": spec.note,
                "kit_fingerprint": prompt_kit.kit_fingerprint(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    ok = sum(1 for r in rows if r["status"] == STATUS_OK)
    print(f"\n{ok}/{len(rows)} runs ok. Results: {jsonl_path.parent}")
    for summary in summaries:
        print(f"  {summary.track} {summary.width}x{summary.height} tier{summary.memory_tier}: {asdict(summary)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
