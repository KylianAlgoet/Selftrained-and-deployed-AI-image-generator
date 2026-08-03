"""EXP-018 Phase 1 - reload a trained LoRA into a FRESH SD 1.5 process and generate.

Phase 1 only: this module generates images and records what it can read back from
the live pipeline. It computes NO similarity indicator and imports no metric
encoder - that is Phase 2 (`scripts/evaluate_lora_effect.py`), for the same
reason M4 kept them apart: a 2.35 GiB CLIP encoder resident in a generation
process would inflate exactly the VRAM figures being reported.

One arm per OS process:

    baseline   no adapter loaded at all - the text-only reference
    weight0    adapter loaded, scale 0.0 - the lower-bound DIAGNOSTIC
    weight1    adapter loaded, scale 1.0 - the changed-output test

Byte equality between `baseline` and `weight0` is a strong positive result but is
NOT a pass condition: loading an inactive adapter may legitimately alter the
execution graph or numerical path. Divergence is recorded honestly and quantified
in Phase 2.

Generation settings come from the frozen evaluation kit (fingerprint c40749bc...),
so these images are directly comparable with the Prototype 1 and 2 baselines.
"""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ml.evaluation import prompt_kit  # noqa: E402
from ml.training import smoke_kit  # noqa: E402
from ml.training.lora_schema import BASE_MODEL_REPO_ID, BASE_MODEL_REVISION  # noqa: E402

MIB = 1024**2

ARM_BASELINE = "baseline"
ARM_WEIGHT0 = "weight0"
ARM_WEIGHT1 = "weight1"
ARMS = (ARM_BASELINE, ARM_WEIGHT0, ARM_WEIGHT1)

ARM_WEIGHTS = {
    ARM_BASELINE: None,
    ARM_WEIGHT0: smoke_kit.LORA_WEIGHT_LOWER_BOUND,
    ARM_WEIGHT1: smoke_kit.LORA_WEIGHT_ACTIVE,
}

OUTPUT_ROOT = REPO / "outputs" / "EXP-018"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def count_lora_modules(unet) -> int:
    """Read back from the LIVE UNet, not inferred from a call returning without
    error - the standard EXP-007 set for the IP-Adapter environment gate."""
    return sum(1 for _, module in unet.named_modules() if hasattr(module, "lora_A"))


def count_active_lora_layers(unet) -> int:
    """Modules whose LoRA layer dict is actually populated."""
    total = 0
    for _, module in unet.named_modules():
        layers = getattr(module, "lora_A", None)
        if layers is not None and len(layers) > 0:
            total += 1
    return total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", required=True, choices=ARMS)
    parser.add_argument("--adapter-dir", help="directory holding the trained .safetensors")
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--results", default="docs/evidence/EXP-018/generations.jsonl")
    args = parser.parse_args(argv)

    import psutil
    import torch
    from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline

    from ml.inference.benchmark import ResourceSampler

    import diffusers
    import peft as peft_pkg

    weight = ARM_WEIGHTS[args.arm]
    if args.arm != ARM_BASELINE and not args.adapter_dir:
        print("--adapter-dir is required for the weight0 and weight1 arms")
        return 2

    print(f"EXP-018 [{args.arm}] {args.width}x{args.height} lora_weight={weight}")

    process = psutil.Process()
    sampler = ResourceSampler(torch, process)
    results_path = REPO / args.results
    results_path.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    sampler.start()
    started = time.perf_counter()

    pipe = StableDiffusionPipeline.from_pretrained(
        BASE_MODEL_REPO_ID,
        revision=BASE_MODEL_REVISION,
        torch_dtype=torch.float16,
        safety_checker=None,
        requires_safety_checker=False,
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to("cuda")
    pipe.set_progress_bar_config(disable=True)

    adapter_sha = ""
    adapter_rel = ""
    modules_before = count_lora_modules(pipe.unet)
    if args.arm != ARM_BASELINE:
        adapter_dir = Path(args.adapter_dir)
        if not adapter_dir.is_absolute():
            adapter_dir = REPO / adapter_dir
        weights = sorted(adapter_dir.glob("*.safetensors"))
        if not weights:
            print(f"no .safetensors in {adapter_dir}")
            return 2
        adapter_path = weights[0]
        adapter_sha = hashlib.sha256(adapter_path.read_bytes()).hexdigest()
        adapter_rel = str(adapter_path.relative_to(REPO)).replace("\\", "/")
        pipe.load_lora_weights(str(adapter_dir), weight_name=adapter_path.name)
        print(f"  loaded adapter {adapter_rel}")
        print(f"  sha256 {adapter_sha}")

    modules_after = count_lora_modules(pipe.unet)
    active_layers = count_active_lora_layers(pipe.unet)
    print(f"  live UNet LoRA modules: {modules_before} before load -> {modules_after} after")
    print(f"  live UNet populated LoRA layers: {active_layers}")

    torch.cuda.synchronize()
    post_load_allocated = round(torch.cuda.max_memory_allocated() / MIB, 2)
    free, total = torch.cuda.mem_get_info()
    print(f"  post-load {post_load_allocated} MiB allocated, {(total - free) / MIB:.2f} MiB device")

    rows = []
    for case in smoke_kit.VALIDATION_CASES:
        spec = prompt_kit.prompt_by_id(case.prompt_id)
        for seed in smoke_kit.VALIDATION_SEEDS:
            generator = torch.Generator(device="cuda").manual_seed(seed)
            kwargs = {}
            if args.arm != ARM_BASELINE:
                kwargs["cross_attention_kwargs"] = {"scale": weight}
            gen_started = time.perf_counter()
            image = pipe(
                prompt=spec.text,
                negative_prompt=prompt_kit.NEGATIVE_PROMPT,
                num_inference_steps=prompt_kit.STEPS,
                guidance_scale=prompt_kit.GUIDANCE_SCALE,
                width=args.width,
                height=args.height,
                generator=generator,
                **kwargs,
            ).images[0]
            gen_seconds = round(time.perf_counter() - gen_started, 3)

            name = f"EXP-018__{args.arm}__{case.id}__{case.prompt_id}__{args.width}x{args.height}__seed{seed}.png"
            out_path = OUTPUT_ROOT / name
            image.save(out_path)
            sha = hashlib.sha256(out_path.read_bytes()).hexdigest()

            rows.append(
                {
                    "exp_id": "EXP-018",
                    "arm": args.arm,
                    "lora_weight": weight,
                    "timestamp_utc": utc_now(),
                    "case_id": case.id,
                    "prompt_id": case.prompt_id,
                    "prompt_sha256": prompt_kit.text_sha256(spec.text),
                    "seed": seed,
                    "width": args.width,
                    "height": args.height,
                    "steps": prompt_kit.STEPS,
                    "guidance_scale": prompt_kit.GUIDANCE_SCALE,
                    "scheduler": prompt_kit.SCHEDULER,
                    "base_model_repo_id": BASE_MODEL_REPO_ID,
                    "base_model_revision_sha": BASE_MODEL_REVISION,
                    "adapter_path": adapter_rel,
                    "adapter_sha256": adapter_sha,
                    "live_lora_modules": modules_after,
                    "live_active_lora_layers": active_layers,
                    "torch_version": torch.__version__,
                    "diffusers_version": diffusers.__version__,
                    "peft_version": peft_pkg.__version__,
                    "generate_seconds": gen_seconds,
                    "output_path": f"outputs/EXP-018/{name}",
                    "output_sha256": sha,
                    "status": "ok",
                }
            )
            print(f"  {case.id} seed {seed}: {gen_seconds}s  sha {sha[:16]}...")

    sampler.stop()
    wall = round(time.perf_counter() - started, 3)
    peak_allocated = round(torch.cuda.max_memory_allocated() / MIB, 2)
    for row in rows:
        row["post_load_allocated_mb"] = post_load_allocated
        row["peak_allocated_mb"] = peak_allocated
        row["peak_device_used_mb"] = round(sampler.peak_device_used_mb, 2)
        row["peak_process_rss_mb"] = round(sampler.peak_process_rss_mb, 2)
        row["arm_wall_seconds"] = wall

    with results_path.open("a", encoding="utf-8", newline="") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    print()
    print(f"  peak {peak_allocated} MiB allocated · {sampler.peak_device_used_mb:.2f} MiB device · {wall}s")
    print(f"  {len(rows)} generations -> {results_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
