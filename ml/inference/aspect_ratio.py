"""EXP-005: deck aspect-ratio handling (RQ8) - inference only.

A skateboard deck is roughly 8 x 32 inches, about 1:4; the project documents the
target as ~1:3.6. Latent diffusion models are trained on square-ish crops, so
generating far outside that distribution is expected to degrade composition.

Compares three strategies for producing a tall deck graphic:

  direct-1x1   512x512   baseline, in-distribution
  direct-1x2   512x1024  moderately out of distribution
  direct-1x3   512x1536  approximates the deck ratio (1:3 vs the true ~1:3.6,
                         stated as an approximation rather than fudged; all
                         dimensions stay multiples of 64 as the VAE requires)
  square-crop  512x512 generated, then the centre vertical 1:3 strip taken

The square-crop strategy deliberately records its *usable* output resolution,
because that is its real cost: cropping a 1:3 strip out of a 512x512 image
yields roughly 170x512 px, far below what a deck print needs. Outpainting - the
other obvious route - is Prototype 5 scope and is not implemented here.

Reuses the frozen prompt kit, the same synchronised timing, the same VRAM
instrumentation, and the same per-run failure rows as the model benchmark.

Run:
    .venv/Scripts/python.exe -m ml.inference.aspect_ratio --model sd15
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ml.evaluation import prompt_kit
from ml.inference.bench_schema import (
    MODELS,
    STATUS_FAILED,
    STATUS_OK,
    STATUS_TIMEOUT,
    ResultRow,
    append_jsonl,
    read_jsonl,
    render_summary_markdown,
    summarize,
    write_csv,
)
from ml.inference.benchmark import (
    GenerationTimeout,
    ResourceSampler,
    generate_once,
    load_pipeline,
    resolve_revision,
    sha256_bytes,
)

REPO = Path(__file__).resolve().parents[2]
OUTPUTS = REPO / "outputs"
EVIDENCE = REPO / "docs" / "evidence"
MIB = 1024**2

EXP_ID = "EXP-005"

# Deck geometry: ~8 x 32 in => ~1:4; the project's documented target is ~1:3.6.
# 1:3 (512x1536) is the closest multiple-of-64 approximation tested here.
DECK_RATIO_TARGET = 3.6

STRATEGIES: list[tuple[str, tuple[int, int]]] = [
    ("direct-1x1", (512, 512)),
    ("direct-1x2", (512, 1024)),
    ("direct-1x3", (512, 1536)),
    ("square-crop", (512, 512)),
]

# The two prompts most relevant to composition: the tall-format probe and one
# style prompt. Kept small on purpose - this experiment varies geometry, not style.
PROMPT_IDS = ("P4-deck", "P1-poster")


def crop_centre_strip(image, ratio: float = 3.0):
    """Take the centre vertical strip at 1:ratio (width:height)."""
    width, height = image.size
    target_width = max(1, int(round(height / ratio)))
    target_width -= target_width % 2
    left = (width - target_width) // 2
    return image.crop((left, 0, left + target_width, height))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EXP-005 deck aspect-ratio comparison (RQ8)")
    parser.add_argument("--model", default="sd15", choices=sorted(MODELS))
    parser.add_argument("--dtype", default="float16", choices=["float16", "bfloat16", "float32"])
    parser.add_argument("--seeds", default="", help="comma-separated seeds (default: the frozen kit seeds)")
    parser.add_argument(
        "--strategy",
        default="",
        choices=["", *[name for name, _ in STRATEGIES]],
        help="run a SINGLE strategy in this process. Required for clean numbers: running "
        "several geometries in one process contaminates both timing and the reserved/device "
        "memory figures, because the caching allocator retains the pool grown by the largest "
        "geometry. scripts/run_aspect_ratio.py spawns one process per strategy.",
    )
    parser.add_argument("--append", action="store_true", help="append to the existing results file")
    args = parser.parse_args(argv)

    import psutil
    import torch
    from diffusers import __version__ as diffusers_version

    if not torch.cuda.is_available():
        print("CUDA unavailable - fix the EXP-001 gate first", file=sys.stderr)
        return 2

    spec = MODELS[args.model]
    seeds = tuple(int(s) for s in args.seeds.split(",") if s.strip()) or prompt_kit.SEEDS
    evidence_dir = EVIDENCE / EXP_ID
    evidence_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = evidence_dir / f"results-{spec.slug}.jsonl"
    if jsonl_path.exists() and not args.append:
        jsonl_path.unlink()
    strategies = [s for s in STRATEGIES if not args.strategy or s[0] == args.strategy]
    out_dir = OUTPUTS / EXP_ID
    out_dir.mkdir(parents=True, exist_ok=True)

    revision = resolve_revision(spec.repo_id)
    print(f"\n=== {EXP_ID} :: aspect-ratio comparison on {spec.repo_id} ===")
    print(f"pinned revision: {revision}")
    print(f"kit fingerprint: {prompt_kit.kit_fingerprint()}")
    print(f"deck target ratio ~1:{DECK_RATIO_TARGET}; 1:3 (512x1536) is the tested approximation\n")

    process = psutil.Process()
    gpu_name = torch.cuda.get_device_name(0)
    tier = 0
    pipe, load_seconds, safety_present, safety_enabled, vae_variant = load_pipeline(
        spec, revision, tier, args.dtype
    )
    print(f"loaded in {load_seconds}s\n")

    crop_notes: list[dict] = []

    for strategy, (width, height) in strategies:
        print(f"-- {strategy} @ {width}x{height} --")
        # Warm-up per geometry: a new resolution triggers fresh kernel autotuning.
        try:
            generate_once(pipe, torch, prompt_kit.prompt_by_id(PROMPT_IDS[0]).text, seeds[0], width, height)
        except Exception as err:  # noqa: BLE001
            print(f"  warm-up failed ({type(err).__name__}) - continuing")

        for prompt_id in PROMPT_IDS:
            prompt = prompt_kit.prompt_by_id(prompt_id)
            for seed in seeds:
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.synchronize()
                sampler = ResourceSampler(torch, process)
                sampler.start()
                status, error_type, error_message = STATUS_OK, "", ""
                generate_seconds: float | str = "not measured"
                output_sha, output_path = "", ""
                final_w, final_h = width, height

                try:
                    image, generate_seconds = generate_once(pipe, torch, prompt.text, seed, width, height)
                    if strategy == "square-crop":
                        image = crop_centre_strip(image, ratio=3.0)
                        final_w, final_h = image.size
                        crop_notes.append(
                            {
                                "prompt_id": prompt_id,
                                "seed": seed,
                                "generated": f"{width}x{height}",
                                "usable_after_crop": f"{final_w}x{final_h}",
                            }
                        )
                    name = (
                        f"{EXP_ID}__{spec.slug}__{strategy}__{prompt_id}__{final_w}x{final_h}"
                        f"__seed{seed}__st{prompt_kit.STEPS}__tier{tier}.png"
                    )
                    destination = out_dir / name
                    image.save(destination)
                    output_sha = sha256_bytes(destination)
                    output_path = str(destination.relative_to(REPO)).replace("\\", "/")
                except GenerationTimeout as err:
                    status, error_type, error_message = STATUS_TIMEOUT, type(err).__name__, str(err)[:400]
                except Exception as err:  # noqa: BLE001
                    status, error_type, error_message = (
                        STATUS_FAILED, type(err).__name__, str(err).splitlines()[0][:400],
                    )
                finally:
                    sampler.stop()

                row = ResultRow(
                    exp_id=EXP_ID,
                    # The strategy occupies the `track` column so the same schema,
                    # aggregation, and summary rendering are reused unchanged.
                    track=strategy,
                    timestamp_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    model_repo_id=spec.repo_id,
                    model_revision_sha=revision,
                    torch_version=torch.__version__,
                    torch_cuda_version=str(torch.version.cuda),
                    diffusers_version=diffusers_version,
                    gpu_name=gpu_name,
                    dtype=args.dtype,
                    scheduler=prompt_kit.SCHEDULER,
                    prompt_id=prompt_id,
                    prompt_sha256=prompt_kit.text_sha256(prompt.text),
                    negative_prompt_sha256=prompt_kit.text_sha256(prompt_kit.NEGATIVE_PROMPT),
                    seed=seed,
                    width=final_w,
                    height=final_h,
                    steps=prompt_kit.STEPS,
                    guidance_scale=prompt_kit.GUIDANCE_SCALE,
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
                append_jsonl(row, jsonl_path)
                marker = "ok" if status == STATUS_OK else status.upper()
                print(
                    f"  [{marker}] {prompt_id} seed={seed} -> {final_w}x{final_h} "
                    f"{generate_seconds}s alloc={row.peak_vram_allocated_mb}MiB "
                    f"dev={row.peak_device_used_mb}MiB"
                    + (f" :: {error_type}" if error_type else "")
                )

    rows = read_jsonl(jsonl_path)
    write_csv(rows, evidence_dir / f"results-{spec.slug}.csv")
    (evidence_dir / f"summary-{spec.slug}.md").write_text(
        render_summary_markdown(
            summarize(rows), f"{EXP_ID} aspect-ratio measurements - {spec.repo_id} (UNSCORED)"
        ),
        encoding="utf-8",
    )
    if crop_notes:
        (evidence_dir / "square-crop-resolution-cost.json").write_text(
            json.dumps(
                {
                    "strategy": "square-crop",
                    "explanation": (
                        "Generate 512x512 in-distribution, then take the centre vertical 1:3 strip. "
                        "The usable resolution after cropping is the real cost of this strategy."
                    ),
                    "deck_ratio_target": DECK_RATIO_TARGET,
                    "samples": crop_notes,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    ok = sum(1 for r in rows if r["status"] == STATUS_OK)
    print(f"\n{ok}/{len(rows)} runs ok. Evidence: {evidence_dir}")
    print("Measurements only - composition quality is judged by the student at the review gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
