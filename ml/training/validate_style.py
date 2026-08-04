"""EXP-025 Phase 1 - the Prototype 4 PILOT REVIEW MATRIX (generation only).

Deliberately small. This matrix exists to support ONE human decision at gate 1 -
which checkpoint and step count to take forward - not to pre-empt the final
comparison. Its size is capped in `style_kit.PILOT_MATRIX_MAX_GENERATIONS`.

    512x512 only . LoRA alone . checkpoints 150 and 300 . weights 0.7 and 1.0
    2 fixed prompts . 2 fixed seeds        =  8 images per checkpoint

Phase 1 only: this module generates images and records what it can read back from
the live pipeline. It computes NO similarity indicator and imports no metric
encoder - that is Phase 2 (`scripts/evaluate_p4_memorisation.py`), for the reason
M4 established.

The prompt templates carry the style's trigger, so the base SD 1.5 arm is run on
the IDENTICAL prompt text with no adapter loaded. That is the correct control: the
only difference is the adapter, not the words.

**No visual-quality judgement is made here or anywhere else in Phase A.**
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

from ml.dataset.captions import STYLE_PHRASES  # noqa: E402
from ml.evaluation import prompt_kit  # noqa: E402
from ml.training import style_kit  # noqa: E402
from ml.training.lora_schema import BASE_MODEL_REPO_ID, BASE_MODEL_REVISION  # noqa: E402

MIB = 1024**2
OUTPUT_ROOT = REPO / "outputs" / "EXP-025"
RESULTS = REPO / "docs" / "evidence" / "EXP-025" / "pilot-matrix.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_prompt(style: str, template: str) -> str:
    spec = style_kit.style_by_key(style)
    return template.format(trigger=spec.trigger, phrase=STYLE_PHRASES[style])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", required=True, help="arm id, e.g. EXP-020 or BASE")
    parser.add_argument("--style", required=True, choices=list(style_kit.STYLE_ORDER))
    parser.add_argument("--checkpoint-dir", default="", help="omit for the base SD 1.5 arm")
    parser.add_argument("--checkpoint-step", type=int, default=0)
    args = parser.parse_args(argv)

    import psutil
    import torch
    from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline

    from ml.inference.benchmark import ResourceSampler

    is_base = not args.checkpoint_dir
    weights = (None,) if is_base else style_kit.PILOT_LORA_WEIGHTS

    print(f"EXP-025 [{args.arm}] style={args.style} checkpoint={args.checkpoint_step or 'none (base)'}")

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    process = psutil.Process()
    sampler = ResourceSampler(torch, process)
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
    if not is_base:
        ck_dir = Path(args.checkpoint_dir)
        if not ck_dir.is_absolute():
            ck_dir = REPO / ck_dir
        files = sorted(ck_dir.glob("*.safetensors"))
        if not files:
            print(f"no .safetensors in {ck_dir}")
            return 2
        adapter_sha = hashlib.sha256(files[0].read_bytes()).hexdigest()
        adapter_rel = str(files[0].relative_to(REPO)).replace("\\", "/")
        pipe.load_lora_weights(str(ck_dir), weight_name=files[0].name)
        print(f"  adapter {adapter_rel}  sha {adapter_sha[:16]}...")

    live_modules = sum(1 for _, m in pipe.unet.named_modules() if hasattr(m, "lora_A"))
    print(f"  live UNet LoRA modules: {live_modules}")

    rows = []
    for prompt_spec in style_kit.PILOT_PROMPTS:
        text = build_prompt(args.style, prompt_spec.template)
        for seed in style_kit.PILOT_SEEDS:
            for weight in weights:
                generator = torch.Generator(device="cuda").manual_seed(seed)
                kwargs = {}
                if weight is not None:
                    kwargs["cross_attention_kwargs"] = {"scale": weight}
                t0 = time.perf_counter()
                image = pipe(
                    prompt=text,
                    negative_prompt=prompt_kit.NEGATIVE_PROMPT,
                    num_inference_steps=prompt_kit.STEPS,
                    guidance_scale=prompt_kit.GUIDANCE_SCALE,
                    width=512,
                    height=512,
                    generator=generator,
                    **kwargs,
                ).images[0]
                seconds = round(time.perf_counter() - t0, 3)

                wtag = "base" if weight is None else f"w{weight:g}".replace(".", "p")
                name = (
                    f"EXP-025__{args.arm}__{args.style}__ck{args.checkpoint_step:05d}"
                    f"__{prompt_spec.id}__seed{seed}__{wtag}.png"
                )
                path = OUTPUT_ROOT / name
                image.save(path)
                rows.append(
                    {
                        "exp_id": "EXP-025",
                        "arm": args.arm,
                        "style": args.style,
                        "checkpoint_step": args.checkpoint_step,
                        "adapter_path": adapter_rel,
                        "adapter_sha256": adapter_sha,
                        "live_lora_modules": live_modules,
                        "prompt_id": prompt_spec.id,
                        "prompt_role": prompt_spec.role,
                        "prompt_text": text,
                        "prompt_sha256": prompt_kit.text_sha256(text),
                        "seed": seed,
                        "lora_weight": weight,
                        "width": 512,
                        "height": 512,
                        "steps": prompt_kit.STEPS,
                        "guidance_scale": prompt_kit.GUIDANCE_SCALE,
                        "scheduler": prompt_kit.SCHEDULER,
                        "generate_seconds": seconds,
                        "output_path": f"outputs/EXP-025/{name}",
                        "output_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "timestamp_utc": utc_now(),
                        "status": "ok",
                    }
                )

    sampler.stop()
    wall = round(time.perf_counter() - started, 3)
    peak = round(torch.cuda.max_memory_allocated() / MIB, 2)
    for row in rows:
        row["peak_allocated_mb"] = peak
        row["peak_device_used_mb"] = round(sampler.peak_device_used_mb, 2)
        row["arm_wall_seconds"] = wall

    with RESULTS.open("a", encoding="utf-8", newline="") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    print(f"  {len(rows)} images, peak {peak} MiB, {wall}s -> {RESULTS.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
