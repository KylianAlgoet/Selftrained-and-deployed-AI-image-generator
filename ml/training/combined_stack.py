"""EXP-019 - the mandatory R12 combined-stack smoke test.

SD 1.5 + trained LoRA + standard IP-Adapter, at 512x512 first and only then at the
DR-007 deck format 512x1536. This is the acceptance item risk R12 set for this
milestone, and DR-008 set for Prototypes 3/4.

Why it matters, stated in the measured terms rather than softened: IP-Adapter
ALONE at 512x1536 already peaked at **7965.5 MiB of 8187.5 MiB physical - about
222 MiB spare** (EXP-013). A LoRA had not been added on top. Whatever this run
reports is reported as a number against that ceiling; it is never described as
comfortable headroom.

Rules this module will not bend:

* **Geometry is never silently reduced to make a run pass.** A reduced geometry
  would be a separate, explicitly labelled deviation row, not this experiment.
* **512x512 runs first.** The deck-format arm only follows a successful one.
* Every element of the stack is frozen and RECORDED: LoRA checkpoint path and
  sha256, LoRA weight, IP-Adapter revision and scale, reference image, prompt,
  negative prompt, seed, scheduler and steps.
* IP-Adapter attachment reuses `ml.inference.reference_conditioning.attach_ip_adapter`
  unchanged, including the pinned-image-encoder workaround, so these figures are
  directly comparable with EXP-009 and EXP-013.
* No evaluation model is imported here.
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
from ml.inference.reference_schema import (  # noqa: E402
    IP_ADAPTER_REPO,
    IP_ADAPTER_REVISION,
    IP_ADAPTER_SUBFOLDER,
    REFERENCES,
)
from ml.training.lora_schema import BASE_MODEL_REPO_ID, BASE_MODEL_REVISION  # noqa: E402

MIB = 1024**2
DEVICE_TOTAL_MB = 8187.5

# DR-008: standard IP-Adapter, default scale 0.55, user range 0.40-0.60.
IP_ADAPTER_WEIGHT_NAME = "ip-adapter_sd15.safetensors"
IP_ADAPTER_SCALE = 0.55

# R2: minimal-geometric, project-original, natively 512x1536 so it needs no crop
# at the deck format, and drawn from the HOLDOUT split - so the LoRA never saw it.
REFERENCE_ID = "R2"
PROMPT_ID = "P2-geo"
SEED = 42
LORA_WEIGHT = 1.0

OUTPUT_ROOT = REPO / "outputs" / "EXP-019"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exp-id", required=True)
    parser.add_argument("--adapter-dir", required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--tier", type=int, default=0)
    parser.add_argument("--results", default="docs/evidence/EXP-019/combined-stack.jsonl")
    args = parser.parse_args(argv)

    import psutil
    import torch
    from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline
    from PIL import Image

    from ml.inference.benchmark import ResourceSampler
    from ml.inference.reference_conditioning import (
        adapter_attention_processors,
        attach_ip_adapter,
        preprocess_for_adapter,
    )
    from ml.inference.reference_schema import MethodSpec

    import diffusers
    import peft as peft_pkg

    reference = REFERENCES[REFERENCE_ID]
    prompt = prompt_kit.prompt_by_id(PROMPT_ID)
    ref_path = REPO / reference.repo_path

    print(f"{args.exp_id}: SD 1.5 + LoRA + IP-Adapter @ {args.width}x{args.height}, tier {args.tier}")
    print(f"  physical VRAM {DEVICE_TOTAL_MB} MiB")

    process = psutil.Process()
    sampler = ResourceSampler(torch, process)
    results_path = REPO / args.results
    results_path.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    row = {
        "exp_id": args.exp_id,
        "timestamp_utc": utc_now(),
        "process_config_key": f"{args.exp_id}__{args.width}x{args.height}__tier{args.tier}",
        "width": args.width,
        "height": args.height,
        "memory_tier": args.tier,
        "base_model_repo_id": BASE_MODEL_REPO_ID,
        "base_model_revision_sha": BASE_MODEL_REVISION,
        "ip_adapter_repo_id": IP_ADAPTER_REPO,
        "ip_adapter_revision_sha": IP_ADAPTER_REVISION,
        "ip_adapter_weight_name": IP_ADAPTER_WEIGHT_NAME,
        "ip_adapter_scale": IP_ADAPTER_SCALE,
        "lora_weight": LORA_WEIGHT,
        "reference_id": reference.id,
        "reference_path": reference.repo_path,
        "reference_width": reference.width,
        "reference_height": reference.height,
        "prompt_id": PROMPT_ID,
        "prompt_sha256": prompt_kit.text_sha256(prompt.text),
        "negative_prompt_sha256": prompt_kit.text_sha256(prompt_kit.NEGATIVE_PROMPT),
        "seed": SEED,
        "steps": prompt_kit.STEPS,
        "guidance_scale": prompt_kit.GUIDANCE_SCALE,
        "scheduler": prompt_kit.SCHEDULER,
        "device_total_mb": DEVICE_TOTAL_MB,
        "torch_version": torch.__version__,
        "diffusers_version": diffusers.__version__,
        "peft_version": peft_pkg.__version__,
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "no cuda device",
        "status": "ok",
        "error_type": "",
        "error_message": "",
    }

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    sampler.start()
    started = time.perf_counter()

    try:
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

        adapter_dir = Path(args.adapter_dir)
        if not adapter_dir.is_absolute():
            adapter_dir = REPO / adapter_dir
        weights = sorted(adapter_dir.glob("*.safetensors"))
        if not weights:
            raise RuntimeError(f"no .safetensors in {adapter_dir}")
        lora_path = weights[0]
        row["lora_path"] = str(lora_path.relative_to(REPO)).replace("\\", "/")
        row["lora_sha256"] = hashlib.sha256(lora_path.read_bytes()).hexdigest()
        pipe.load_lora_weights(str(adapter_dir), weight_name=lora_path.name)
        row["live_lora_modules"] = sum(
            1 for _, m in pipe.unet.named_modules() if hasattr(m, "lora_A")
        )
        print(f"  LoRA loaded: {row['live_lora_modules']} live modules, sha {row['lora_sha256'][:16]}...")

        torch.cuda.synchronize()
        row["after_lora_allocated_mb"] = round(torch.cuda.memory_allocated() / MIB, 2)

        method = MethodSpec(
            key="ip-adapter",
            label="IP-Adapter",
            slug="ip-adapter",
            repo_id=IP_ADAPTER_REPO,
            subfolder=IP_ADAPTER_SUBFOLDER,
            weight_name=IP_ADAPTER_WEIGHT_NAME,
            strength_param_name="scale",
            strength_inverted=False,
            loads_image_encoder=True,
            note="EXP-019 combined stack",
        )
        row["ip_adapter_image_encoder_revision"] = attach_ip_adapter(pipe, method, "float16")
        processors = adapter_attention_processors(pipe)
        if not processors:
            raise RuntimeError("load_ip_adapter installed no IP-Adapter attention processor")
        row["ip_adapter_processors"] = ",".join(processors)
        row["ip_adapter_processor_count"] = sum(
            1 for p in pipe.unet.attn_processors.values() if "IPAdapter" in type(p).__name__
        )
        pipe.set_ip_adapter_scale(IP_ADAPTER_SCALE)
        print(
            f"  IP-Adapter loaded: {row['ip_adapter_processor_count']} attention processors, "
            f"scale {IP_ADAPTER_SCALE}"
        )
        # Both adapters must be live at once - that is the whole point of R12.
        if row["live_lora_modules"] == 0:
            raise RuntimeError("LoRA modules vanished after loading IP-Adapter")

        torch.cuda.synchronize()
        row["post_load_allocated_mb"] = round(torch.cuda.memory_allocated() / MIB, 2)
        free, total = torch.cuda.mem_get_info()
        row["post_load_device_used_mb"] = round((total - free) / MIB, 2)
        print(
            f"  post-load {row['post_load_allocated_mb']} MiB allocated, "
            f"{row['post_load_device_used_mb']} MiB device"
        )

        # Returns (image, note). The note records exactly what was done to the
        # reference, and travels with the row so the preprocessing can never be
        # reconstructed incorrectly later.
        with Image.open(ref_path) as raw:
            ref_image, ref_note = preprocess_for_adapter(raw.convert("RGB"))
        row["reference_preprocessing"] = ref_note
        row["reference_sha256"] = hashlib.sha256(ref_path.read_bytes()).hexdigest()

        generator = torch.Generator(device="cuda").manual_seed(SEED)
        gen_started = time.perf_counter()
        image = pipe(
            prompt=prompt.text,
            negative_prompt=prompt_kit.NEGATIVE_PROMPT,
            ip_adapter_image=ref_image,
            num_inference_steps=prompt_kit.STEPS,
            guidance_scale=prompt_kit.GUIDANCE_SCALE,
            width=args.width,
            height=args.height,
            generator=generator,
            cross_attention_kwargs={"scale": LORA_WEIGHT},
        ).images[0]
        row["generate_seconds"] = round(time.perf_counter() - gen_started, 3)

        name = f"{args.exp_id}__lora+ipadapter__{PROMPT_ID}__{REFERENCE_ID}__{args.width}x{args.height}__seed{SEED}__tier{args.tier}.png"
        out_path = OUTPUT_ROOT / name
        image.save(out_path)
        row["output_path"] = f"outputs/EXP-019/{name}"
        row["output_sha256"] = hashlib.sha256(out_path.read_bytes()).hexdigest()

    except torch.cuda.OutOfMemoryError as err:
        row["status"] = "oom"
        row["error_type"] = "torch.cuda.OutOfMemoryError"
        row["error_message"] = str(err).strip().splitlines()[0][:400]
        print(f"  OOM: {row['error_message']}")
    except Exception as err:  # noqa: BLE001 - a failed run is a recorded result
        row["status"] = "failed"
        row["error_type"] = type(err).__name__
        row["error_message"] = str(err).strip().splitlines()[0][:400]
        print(f"  FAILED: {row['error_type']}: {row['error_message']}")
    finally:
        sampler.stop()
        row["wall_seconds"] = round(time.perf_counter() - started, 3)
        row["peak_allocated_mb"] = round(torch.cuda.max_memory_allocated() / MIB, 2)
        row["peak_reserved_mb"] = round(torch.cuda.max_memory_reserved() / MIB, 2)
        row["peak_device_used_mb"] = round(sampler.peak_device_used_mb, 2)
        row["peak_process_rss_mb"] = round(sampler.peak_process_rss_mb, 2)
        row["spare_device_mb"] = round(DEVICE_TOTAL_MB - row["peak_device_used_mb"], 2)

    with results_path.open("a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")

    print()
    print(f"  status: {row['status']}")
    print(
        f"  peak {row['peak_allocated_mb']} MiB allocated · "
        f"{row['peak_device_used_mb']} MiB device of {DEVICE_TOTAL_MB} · "
        f"{row['spare_device_mb']} MiB spare"
    )
    print(f"  results -> {results_path}")
    return 0 if row["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
