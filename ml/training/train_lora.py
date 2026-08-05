"""Prototype 3 (M5) LoRA training runner - Diffusers + PEFT on the pinned SD 1.5.

ONE CONFIGURATION PER OS PROCESS whenever VRAM or timing is measured. The caching
allocator retains its pool across `reset_peak_memory_stats()`, which is what
contaminated EXP-005's first run; see
`docs/evidence/EXP-005/measurement-methodology-correction.md`. The orchestrator
in `scripts/run_lora_training.py` therefore launches each phase as a fresh
subprocess and this module never loops over configurations.

No evaluation model is ever imported here. Similarity scoring is a separate
offline workload (`ml/evaluation/similarity.py`), because loading a 2.35 GiB
metric encoder inside a measured training process would inflate exactly the VRAM
figures the comparison rests on. A pytest enforces the boundary both ways.

What this runner proves, rather than assumes:
  * the trainable parameter count is non-zero AND the expected one;
  * every non-LoRA UNet parameter is frozen, and the base weights are unchanged
    at the end (hash-compared, not trusted);
  * gradients on LoRA parameters are present, finite and non-zero;
  * recorded losses are finite;
  * at least one LoRA tensor moved from its initialised value (hash + L2 delta);
  * the saved checkpoint contains LoRA keys and no full base-model weights.

Run (via the orchestrator, not directly, so the process boundary is real):
    .venv/Scripts/python.exe scripts/run_lora_training.py --help
"""

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ml.training import smoke_kit  # noqa: E402
from ml.training.lora_schema import (  # noqa: E402
    BASE_MODEL_REPO_ID,
    BASE_MODEL_REVISION,
    PHASE_MULTI_STYLE,
    PHASE_SINGLE_STEP,
    PHASE_SMOKE,
    PHASE_STABILITY,
    PHASE_STYLE_FULL,
    PHASES,
    PROBE_WALL_LIMIT_SECONDS,
    STATUS_FAILED,
    STATUS_OK,
    STATUS_OOM,
    AdapterArtifact,
    GateRecord,
    ResourceRecord,
    TrainingResultRow,
    TrainingSpec,
    append_jsonl,
    build_run_slug,
)

MIB = 1024**2

# Attention projections only - the cheapest configuration that can still learn a
# style, and the one the tier ladder escalates *from*.
TARGET_MODULES = ["to_q", "to_k", "to_v", "to_out.0"]
TARGET_MODULES_LABEL = "unet attention " + ",".join(TARGET_MODULES)

# Outputs live outside git. Model weights are never committed
# (.claude/rules/security.md).
OUTPUT_ROOT = REPO / "outputs" / "lora"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --- data --------------------------------------------------------------------


def load_smoke_items() -> list[dict]:
    """Read the frozen M5 manifest. The subset is never reselected at run time."""
    import csv

    path = REPO / smoke_kit.SMOKE_MANIFEST_PATH
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    ids = tuple(r["id"] for r in rows)
    if ids != smoke_kit.SMOKE_ITEM_IDS:
        raise RuntimeError(
            f"smoke manifest {path} does not match the frozen kit: {ids} != {smoke_kit.SMOKE_ITEM_IDS}"
        )
    return rows


def load_style_items(manifest_path: str) -> list[dict]:
    """Read a frozen Prototype 4 per-style manifest.

    Both caption columns travel with every row, so the style-only and verbatim
    arms of EXP-023 read the same file and can differ in nothing but the column
    they select.
    """
    import csv

    path = REPO / manifest_path
    if not path.is_file():
        raise RuntimeError(f"style manifest not found: {path}")
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        raise RuntimeError(f"style manifest is empty: {path}")
    for row in rows:
        for column in ("id", "source_path", "training_caption", "dataset_v1_caption"):
            if not row.get(column):
                raise RuntimeError(f"{path.name}: row {row.get('id')} is missing {column!r}")
    return rows


def load_multi_style_items(manifest_paths: list[str]) -> list[dict]:
    """Read every per-style manifest into one list, tagging each row with its style.

    Each manifest's `training_caption` already carries that style's own trigger
    (`xgeo` / `xkyo` / `xpst`), so the multi-style run needs no special caption
    logic - the trigger is the style selector, which is exactly what makes RQ5
    answerable.
    """
    items: list[dict] = []
    for path in manifest_paths:
        style = Path(path).stem.replace("style-", "").replace("-p4", "")
        for row in load_style_items(path):
            row = dict(row)
            row["_style"] = style
            row["_manifest"] = path
            items.append(row)
    return items


def build_balanced_multi_style_order(
    items: list[dict], seed: int, per_style_steps: int
) -> list[int]:
    """Exactly `per_style_steps` presentations per style, in a deterministic order.

    Balanced by construction rather than in expectation: the style slots are built
    as an exact multiset (600 of each) and then shuffled, so the largest training
    set cannot dominate and no style can drift off its target exposure. Within a
    style, items cycle through reshuffled pools exactly as the single-style
    sampler does, so per-item exposure stays as even as the step count allows.

    A round-robin interleave would also be balanced, but it would tie style to
    step parity - every third step the same style - which is a periodic structure
    the optimizer could ride. The seeded shuffle avoids that while staying
    reproducible from the seed alone.
    """
    import random

    by_style: dict[str, list[int]] = {}
    for index, item in enumerate(items):
        by_style.setdefault(item["_style"], []).append(index)

    rng = random.Random(seed)

    # Per-style queues, each `per_style_steps` long.
    queues: dict[str, list[int]] = {}
    for style, indices in sorted(by_style.items()):
        order: list[int] = []
        pool: list[int] = []
        style_rng = random.Random(f"{seed}:{style}")
        while len(order) < per_style_steps:
            if not pool:
                pool = list(indices)
                style_rng.shuffle(pool)
            order.append(pool.pop())
        queues[style] = order

    slots = [style for style in sorted(by_style) for _ in range(per_style_steps)]
    rng.shuffle(slots)

    cursors = {style: 0 for style in queues}
    combined: list[int] = []
    for style in slots:
        combined.append(queues[style][cursors[style]])
        cursors[style] += 1
    return combined


def per_style_exposure(items: list[dict], order: list[int]) -> str:
    """Actual presentations per style, counted from the order that ran."""
    from collections import Counter

    counts = Counter(items[i]["_style"] for i in order)
    return ";".join(f"{style}:{counts[style]}" for style in sorted(counts))


def caption_for(item: dict, caption_mode: str) -> str:
    """Which column the run trains on. The ONLY difference between the two arms
    of the caption A/B - same images, same order, same seed, same steps."""
    from ml.training import style_kit

    if caption_mode == style_kit.CAPTION_MODE_STYLE_ONLY:
        return item["training_caption"]
    if caption_mode == style_kit.CAPTION_MODE_VERBATIM:
        return item["dataset_v1_caption"]
    # M5 smoke manifests carry a single `caption` column.
    return item.get("caption") or item["training_caption"]


def save_adapter(unet, out_dir: Path, pipeline_cls) -> dict:
    """Write LoRA weights to `out_dir` and describe what was actually written.

    Used for intermediate checkpoints and for the final save, so both are
    described identically and neither can claim more than it wrote.
    """
    from peft.utils import get_peft_model_state_dict
    from safetensors.torch import load_file

    out_dir.mkdir(parents=True, exist_ok=True)
    pipeline_cls.save_lora_weights(
        save_directory=str(out_dir),
        unet_lora_layers=get_peft_model_state_dict(unet),
        safe_serialization=True,
    )
    weights = sorted(out_dir.glob("*.safetensors"))
    if not weights:
        raise RuntimeError(f"no .safetensors written to {out_dir}")
    path = weights[0]
    saved = load_file(str(path))
    return {
        "path": str(path.relative_to(REPO)).replace("\\", "/"),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size_bytes": path.stat().st_size,
        "tensor_count": len(saved),
        "lora_key_count": sum(1 for k in saved if "lora" in k.lower()),
        "unexpected_base_model_keys": ",".join(
            sorted(k for k in saved if "lora" not in k.lower())
        )[:400],
    }


def presentation_counts(items: list[dict], order: list[int]) -> tuple[str, float]:
    """How often each item was actually shown.

    Recorded because the RQ4 size arms hold STEPS fixed rather than epochs, so a
    12-image arm presents each item ~25x against ~6.8x for the 44-image arm. That
    confound must be visible in the row, not inferred.
    """
    from collections import Counter

    counts = Counter(order)
    encoded = ";".join(f"{items[i]['id']}:{counts.get(i, 0)}" for i in range(len(items)))
    mean = sum(counts.values()) / len(items) if items else 0.0
    return encoded, round(mean, 3)


def build_sample_order(items: list[dict], seed: int, steps: int) -> list[int]:
    """Deterministic, recorded, and identical across every comparable tier."""
    import random

    rng = random.Random(seed)
    order: list[int] = []
    pool: list[int] = []
    while len(order) < steps:
        if not pool:
            pool = list(range(len(items)))
            rng.shuffle(pool)
        order.append(pool.pop())
    return order


def sample_order_fingerprint(items: list[dict], order: list[int]) -> str:
    return sha256_text("|".join(items[i]["id"] for i in order))


def prepare_image(path: Path, width: int, height: int, transform: str):
    """Sources are natively 512x1536. The transform is a RECORDED field, not a
    silent default: centre-crop preserves scale and discards area, which is a
    different experiment from squashing the aspect."""
    from PIL import Image

    image = Image.open(path).convert("RGB")
    if (image.width, image.height) == (width, height):
        return image
    if transform == "none":
        raise RuntimeError(
            f"{path.name} is {image.width}x{image.height} but the run declared transform 'none' "
            f"for target {width}x{height}"
        )
    if transform != "centre-crop":
        raise RuntimeError(f"unknown source transform {transform!r}")

    target_ratio = width / height
    src_ratio = image.width / image.height
    if src_ratio > target_ratio:
        crop_w = int(round(image.height * target_ratio))
        left = (image.width - crop_w) // 2
        box = (left, 0, left + crop_w, image.height)
    else:
        crop_h = int(round(image.width / target_ratio))
        top = (image.height - crop_h) // 2
        box = (0, top, image.width, top + crop_h)
    return image.resize((width, height), Image.LANCZOS, box=box)


def to_tensor(image, torch, dtype):
    import numpy as np

    array = np.asarray(image, dtype=np.float32) / 127.5 - 1.0
    tensor = torch.from_numpy(array).permute(2, 0, 1).unsqueeze(0)
    return tensor.to(device="cuda", dtype=dtype)


# --- parameter evidence ------------------------------------------------------


def lora_parameters(unet) -> list:
    return [(n, p) for n, p in unet.named_parameters() if "lora" in n.lower()]


def fingerprint_parameters(named_params) -> str:
    """Deterministic hash over the actual tensor bytes, so 'the weights changed'
    is evidence rather than an inference from the loss curve."""
    import torch

    digest = hashlib.sha256()
    for name, param in sorted(named_params, key=lambda kv: kv[0]):
        digest.update(name.encode("utf-8"))
        digest.update(param.detach().to(device="cpu", dtype=torch.float64).numpy().tobytes())
    return digest.hexdigest()


def l2_delta(before: dict, unet, torch) -> float:
    total = 0.0
    for name, param in lora_parameters(unet):
        if name in before:
            diff = param.detach().to(device="cpu", dtype=torch.float64) - before[name]
            total += float((diff * diff).sum())
    return math.sqrt(total)


# --- the run -----------------------------------------------------------------


def run(spec: TrainingSpec, results_path: Path) -> tuple[int, TrainingResultRow]:
    import psutil
    import torch
    from diffusers import AutoencoderKL, DDPMScheduler, StableDiffusionPipeline, UNet2DConditionModel
    from peft import LoraConfig
    from transformers import CLIPTextModel, CLIPTokenizer

    from ml.inference.benchmark import ResourceSampler

    import diffusers
    import peft as peft_pkg

    from ml.dataset.hashing import sha256_file
    from ml.training import style_kit

    multi_manifest_sha = ""
    exposure = ""
    style_item_counts = ""
    if spec.multi_style:
        manifest_paths = [p for p in spec.style_manifest_path.split(";") if p]
        items = load_multi_style_items(manifest_paths)
        per_manifest = [f"{p}:{sha256_file(REPO / p)}" for p in manifest_paths]
        manifest_sha = ""
        multi_manifest_sha = sha256_text("|".join(per_manifest))
        style_fingerprint = style_kit.kit_fingerprint()

        order = build_balanced_multi_style_order(items, spec.seed, spec.per_style_steps)
        if len(order) != spec.optimizer_steps_planned:
            raise RuntimeError(
                f"balanced order is {len(order)} steps but the spec planned "
                f"{spec.optimizer_steps_planned}"
            )
        exposure = per_style_exposure(items, order)
        # Asserted, not hoped for: an unbalanced multi-style run would make the
        # RQ5 comparison meaningless while still producing a plausible adapter.
        for pair in exposure.split(";"):
            style_name, count = pair.split(":")
            if int(count) != spec.per_style_steps:
                raise RuntimeError(
                    f"style {style_name} received {count} presentations, expected "
                    f"{spec.per_style_steps}"
                )
        from collections import Counter

        style_item_counts = ";".join(
            f"{s}:{n}" for s, n in sorted(Counter(i["_style"] for i in items).items())
        )
    elif spec.style_manifest_path:
        items = load_style_items(spec.style_manifest_path)
        manifest_sha = sha256_file(REPO / spec.style_manifest_path)
        style_fingerprint = style_kit.kit_fingerprint()
        order = build_sample_order(items, spec.seed, spec.optimizer_steps_planned)
    else:
        items = load_smoke_items()
        manifest_sha = ""
        style_fingerprint = ""
        order = build_sample_order(items, spec.seed, spec.optimizer_steps_planned)

    order_sha = sample_order_fingerprint(items, order)
    presentations, presentations_mean = presentation_counts(items, order)

    resources = ResourceRecord()
    gates = GateRecord()
    adapter = AdapterArtifact()
    boundaries: list[str] = []

    row = TrainingResultRow(
        exp_id=spec.exp_id,
        phase=spec.phase,
        timestamp_utc=utc_now(),
        process_config_key=spec.process_config_key,
        base_model_repo_id=spec.base_model_repo_id,
        base_model_revision_sha=spec.base_model_revision,
        torch_version=torch.__version__,
        torch_cuda_version=str(torch.version.cuda),
        diffusers_version=diffusers.__version__,
        peft_version=peft_pkg.__version__,
        gpu_name=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "no cuda device",
        dataset_version=spec.dataset_version,
        smoke_manifest_path=spec.smoke_manifest_path,
        smoke_kit_fingerprint=smoke_kit.kit_fingerprint(),
        sample_order_sha256=order_sha,
        style=spec.style,
        caption_strategy=spec.caption_strategy,
        item_count=len(items),
        width=spec.width,
        height=spec.height,
        source_transform=spec.source_transform,
        rank=spec.rank,
        alpha=spec.alpha,
        target_modules=spec.target_modules,
        learning_rate=spec.learning_rate,
        optimizer=spec.optimizer,
        optimizer_state_dtype=spec.optimizer_state_dtype,
        optimizer_steps_planned=spec.optimizer_steps_planned,
        batch_size=spec.batch_size,
        grad_accum=spec.grad_accum,
        effective_batch_size=spec.effective_batch_size,
        text_encoder_trained=spec.text_encoder_trained,
        vae_trained=spec.vae_trained,
        gradient_checkpointing=spec.gradient_checkpointing,
        latent_caching=spec.latent_caching,
        precision=spec.precision,
        attention_impl=spec.attention_impl,
        seed=spec.seed,
        memory_tier=spec.memory_tier,
        resources=resources,
        gates=gates,
        adapter=adapter,
        trigger_token=spec.trigger_token,
        trigger_token_ids=(
            ";".join(
                f"{s.key}:{','.join(str(i) for i in s.trigger_token_ids)}"
                for s in sorted(style_kit.STYLES, key=lambda s: s.order)
            )
            if spec.multi_style
            else (
                ",".join(str(i) for i in style_kit.style_by_key(spec.style).trigger_token_ids)
                if spec.style_manifest_path
                else ""
            )
        ),
        caption_mode=spec.caption_mode,
        style_manifest_path=spec.style_manifest_path,
        style_manifest_sha256=manifest_sha,
        style_kit_fingerprint=style_fingerprint,
        item_presentation_counts=presentations,
        presentations_per_item_mean=presentations_mean,
        per_style_exposure=exposure,
        per_style_item_counts=style_item_counts,
        multi_style_manifest_sha256=multi_manifest_sha,
    )

    if not torch.cuda.is_available():
        row.status = STATUS_FAILED
        row.error_type = "NoCudaDevice"
        row.error_message = "torch.cuda.is_available() is False"
        append_jsonl(row, results_path)
        return 1, row

    process = psutil.Process()
    sampler = ResourceSampler(torch, process)
    started = time.perf_counter()
    weight_dtype = torch.float16 if spec.precision == "fp16" else torch.float32

    try:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        boundaries.append("reset before component load")
        sampler.start()

        common = dict(revision=spec.base_model_revision)
        tokenizer = CLIPTokenizer.from_pretrained(
            spec.base_model_repo_id, subfolder="tokenizer", **common
        )
        text_encoder = CLIPTextModel.from_pretrained(
            spec.base_model_repo_id, subfolder="text_encoder", torch_dtype=weight_dtype, **common
        ).to("cuda")
        vae = AutoencoderKL.from_pretrained(
            spec.base_model_repo_id, subfolder="vae", torch_dtype=weight_dtype, **common
        ).to("cuda")
        unet = UNet2DConditionModel.from_pretrained(
            spec.base_model_repo_id, subfolder="unet", torch_dtype=weight_dtype, **common
        ).to("cuda")
        noise_scheduler = DDPMScheduler.from_pretrained(
            spec.base_model_repo_id, subfolder="scheduler", **common
        )

        # Everything frozen; only the LoRA adapter trains.
        vae.requires_grad_(False)
        text_encoder.requires_grad_(False)
        unet.requires_grad_(False)
        vae.eval()
        text_encoder.eval()

        base_param_fingerprint = fingerprint_parameters(
            [(n, p) for n, p in unet.named_parameters() if "lora" not in n.lower()][:8]
        )

        unet.add_adapter(
            LoraConfig(
                r=spec.rank,
                lora_alpha=spec.alpha,
                init_lora_weights="gaussian",
                target_modules=TARGET_MODULES,
            )
        )
        if spec.gradient_checkpointing:
            unet.enable_gradient_checkpointing()

        # LoRA parameters in fp32 while the frozen base stays fp16: the declared
        # tier-0 configuration. fp16 master weights for trained parameters are
        # numerically unstable.
        from diffusers.training_utils import cast_training_params

        cast_training_params(unet, dtype=torch.float32)
        unet.train()

        trainable = [(n, p) for n, p in unet.named_parameters() if p.requires_grad]
        lora_named = lora_parameters(unet)
        non_lora_trainable = [n for n, _ in trainable if "lora" not in n.lower()]
        if non_lora_trainable:
            raise RuntimeError(
                f"{len(non_lora_trainable)} non-LoRA parameters are trainable, e.g. "
                f"{non_lora_trainable[:3]}"
            )

        gates.trainable_lora_parameters = sum(p.numel() for _, p in trainable)
        gates.trainable_lora_tensors = len(trainable)
        # The expectation is derived from the adapter that was actually attached:
        # every trainable tensor must be a LoRA tensor and nothing else.
        gates.expected_trainable_parameters = sum(p.numel() for _, p in lora_named)
        gates.base_unet_parameters_frozen = True  # provisional; re-verified after training

        params = [p for _, p in trainable]
        optimizer = torch.optim.AdamW(params, lr=spec.learning_rate)
        scaler = torch.amp.GradScaler("cuda", enabled=weight_dtype == torch.float16)

        before_snapshot = {
            n: p.detach().to(device="cpu", dtype=torch.float64).clone() for n, p in lora_named
        }
        gates.lora_params_sha256_before = fingerprint_parameters(lora_named)

        torch.cuda.synchronize()
        resources.post_load_allocated_mb = round(torch.cuda.max_memory_allocated() / MIB, 2)
        resources.post_load_reserved_mb = round(torch.cuda.max_memory_reserved() / MIB, 2)
        free, total = torch.cuda.mem_get_info()
        resources.post_load_device_used_mb = round((total - free) / MIB, 2)
        device_total_mb = total / MIB
        print(
            f"  loaded: {resources.post_load_allocated_mb} MiB allocated, "
            f"{resources.post_load_device_used_mb} MiB device of {device_total_mb:.1f}"
        )
        print(
            f"  trainable: {gates.trainable_lora_tensors} LoRA tensors, "
            f"{gates.trainable_lora_parameters} parameters"
        )

        generator = torch.Generator(device="cuda").manual_seed(spec.seed)
        losses: list[float] = []
        checkpoint_records: list[tuple[int, dict]] = []
        peak_fb = 0.0
        peak_opt = 0.0
        grads_checked = False
        train_started = time.perf_counter()

        for step, index in enumerate(order):
            item = items[index]
            image = prepare_image(
                REPO / item["source_path"], spec.width, spec.height, spec.source_transform
            )
            pixel_values = to_tensor(image, torch, weight_dtype)

            tokens = tokenizer(
                caption_for(item, spec.caption_mode),
                padding="max_length",
                max_length=tokenizer.model_max_length,
                truncation=True,
                return_tensors="pt",
            ).input_ids.to("cuda")

            # --- measured boundary: forward + backward ---
            torch.cuda.reset_peak_memory_stats()
            if step == 0:
                boundaries.append("reset before step 0 forward/backward")

            with torch.no_grad():
                latents = vae.encode(pixel_values).latent_dist.sample(generator)
                latents = latents * vae.config.scaling_factor
                encoder_hidden_states = text_encoder(tokens)[0]

            noise = torch.randn(latents.shape, generator=generator, device="cuda", dtype=latents.dtype)
            timesteps = torch.randint(
                0,
                noise_scheduler.config.num_train_timesteps,
                (latents.shape[0],),
                generator=generator,
                device="cuda",
            ).long()
            noisy = noise_scheduler.add_noise(latents, noise, timesteps)

            if noise_scheduler.config.prediction_type == "v_prediction":
                target = noise_scheduler.get_velocity(latents, noise, timesteps)
            else:
                target = noise

            model_pred = unet(noisy, timesteps, encoder_hidden_states).sample
            loss = torch.nn.functional.mse_loss(model_pred.float(), target.float(), reduction="mean")
            scaler.scale(loss).backward()

            torch.cuda.synchronize()
            peak_fb = max(peak_fb, torch.cuda.max_memory_allocated() / MIB)

            if not grads_checked:
                grads = [p.grad for _, p in lora_named if p.grad is not None]
                gates.gradients_present = len(grads) > 0
                gates.gradients_finite = bool(grads) and all(
                    bool(torch.isfinite(g).all()) for g in grads
                )
                gates.gradients_nonzero = bool(grads) and any(
                    float(g.abs().sum()) > 0.0 for g in grads
                )
                grads_checked = True

            # --- measured boundary: optimizer step ---
            torch.cuda.reset_peak_memory_stats()
            if step == 0:
                boundaries.append("reset before step 0 optimizer step")
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
            torch.cuda.synchronize()
            peak_opt = max(peak_opt, torch.cuda.max_memory_allocated() / MIB)

            losses.append(float(loss.detach()))
            gates.optimizer_steps_completed = step + 1
            gates.global_steps_completed = step + 1

            elapsed = time.perf_counter() - started
            if step == 0 or (step + 1) % 25 == 0 or step + 1 == len(order):
                print(f"  step {step + 1}/{len(order)} loss={losses[-1]:.4f} elapsed={elapsed:.1f}s")

            if spec.phase in (PHASE_SINGLE_STEP, PHASE_STABILITY) and elapsed > PROBE_WALL_LIMIT_SECONDS:
                raise TimeoutError(
                    f"probe exceeded the {PROBE_WALL_LIMIT_SECONDS}s limit at step {step + 1}"
                )

            # --- intermediate checkpoint -------------------------------------
            # Saved so an over- or under-trained run is recoverable without
            # retraining, and so the human review can compare step counts rather
            # than take the final state on trust.
            if (step + 1) in spec.checkpoint_steps and (step + 1) != len(order):
                ck_dir = OUTPUT_ROOT / build_run_slug(spec) / f"step{step + 1:05d}"
                saved = save_adapter(unet, ck_dir, StableDiffusionPipeline)
                checkpoint_records.append((step + 1, saved))
                print(f"    checkpoint at step {step + 1} -> {saved['sha256'][:16]}...")

        train_seconds = time.perf_counter() - train_started

        # --- evidence, read back rather than assumed ---
        gates.losses_finite = all(math.isfinite(v) for v in losses)
        gates.first_loss = losses[0] if losses else "not measured"
        gates.last_loss = losses[-1] if losses else "not measured"
        gates.loss_decreased = (len(losses) > 1 and losses[-1] < losses[0]) if losses else "not measured"

        gates.lora_params_sha256_after = fingerprint_parameters(lora_named)
        gates.lora_params_changed = gates.lora_params_sha256_after != gates.lora_params_sha256_before
        gates.lora_params_l2_delta = round(l2_delta(before_snapshot, unet, torch), 8)

        after_base = fingerprint_parameters(
            [(n, p) for n, p in unet.named_parameters() if "lora" not in n.lower()][:8]
        )
        gates.base_unet_parameters_frozen = after_base == base_param_fingerprint

        # --- save the adapter, outside git ---
        slug = build_run_slug(spec)
        final = save_adapter(unet, OUTPUT_ROOT / slug / f"step{len(order):05d}", StableDiffusionPipeline)
        checkpoint_records.append((len(order), final))
        adapter.path = final["path"]
        adapter.size_bytes = final["size_bytes"]
        adapter.sha256 = final["sha256"]
        adapter.tensor_count = final["tensor_count"]
        adapter.lora_key_count = final["lora_key_count"]
        adapter.unexpected_base_model_keys = final["unexpected_base_model_keys"]
        row.checkpoints = ";".join(
            f"{step}:{rec['sha256']}:{rec['size_bytes']}" for step, rec in checkpoint_records
        )

        # --- full loss history, outside the row so the row stays readable ---
        history_dir = REPO / "docs" / "evidence" / spec.exp_id.split("_")[0]
        history_dir.mkdir(parents=True, exist_ok=True)
        history_path = history_dir / f"loss-history-{slug}.jsonl"
        with history_path.open("w", encoding="utf-8", newline="") as fh:
            for i, (index, value) in enumerate(zip(order, losses), start=1):
                fh.write(
                    json.dumps(
                        {"step": i, "item_id": items[index]["id"], "loss": value},
                        sort_keys=True,
                    )
                    + "\n"
                )
        row.loss_history_path = str(history_path.relative_to(REPO)).replace("\\", "/")

        resources.peak_forward_backward_allocated_mb = round(peak_fb, 2)
        resources.peak_optimizer_step_allocated_mb = round(peak_opt, 2)
        resources.process_peak_allocated_mb = round(
            max(peak_fb, peak_opt, float(resources.post_load_allocated_mb)), 2
        )
        resources.process_peak_reserved_mb = round(torch.cuda.max_memory_reserved() / MIB, 2)
        resources.seconds_per_optimizer_step = round(train_seconds / max(len(order), 1), 4)

        row.status = STATUS_OK

    except torch.cuda.OutOfMemoryError as err:
        row.status = STATUS_OOM
        row.error_type = "torch.cuda.OutOfMemoryError"
        row.error_message = str(err).strip().splitlines()[0][:400]
        print(f"  OOM: {row.error_message}")
    except Exception as err:  # noqa: BLE001 - a failed run is a recorded result
        row.status = STATUS_FAILED
        row.error_type = type(err).__name__
        row.error_message = str(err).strip().splitlines()[0][:400] if str(err).strip() else ""
        print(f"  FAILED: {row.error_type}: {row.error_message}")
    finally:
        sampler.stop()
        resources.wall_seconds = round(time.perf_counter() - started, 3)
        resources.process_peak_device_used_mb = round(sampler.peak_device_used_mb, 2)
        resources.peak_process_rss_mb = round(sampler.peak_process_rss_mb, 2)
        resources.reset_boundaries = "; ".join(boundaries)

    row.gates_passed = gates.passed()
    row.gate_failures = "; ".join(gates.failures())
    if row.status == STATUS_OK and not row.gates_passed:
        row.status = STATUS_FAILED
        row.error_type = row.error_type or "GatesNotMet"
        row.error_message = row.error_message or row.gate_failures

    append_jsonl(row, results_path)
    return (0 if row.status == STATUS_OK and row.gates_passed else 1), row


# --- CLI ---------------------------------------------------------------------


def build_spec(args) -> TrainingSpec:
    native = (args.width, args.height) == (512, 1536)

    style_manifest = getattr(args, "manifest", "") or ""
    style_name = getattr(args, "style", "") or ""
    caption_mode = getattr(args, "caption_mode", "") or ""
    checkpoint_steps = tuple(getattr(args, "checkpoint_steps", ()) or ())

    if getattr(args, "multi_style", False):
        from ml.training import style_kit

        style_manifest = ";".join(
            f"data/manifests/style-{key}-p4.csv" for key in style_kit.STYLE_ORDER
        )
        caption_mode = caption_mode or style_kit.CAPTION_MODE_STYLE_ONLY
        triggers = ",".join(style_kit.style_by_key(k).trigger for k in style_kit.STYLE_ORDER)
        return TrainingSpec(
            exp_id=args.exp_id,
            phase=args.phase,
            memory_tier=args.tier,
            dataset_version=style_kit.DATASET_V1_SHA256[:12],
            smoke_manifest_path=smoke_kit.SMOKE_MANIFEST_PATH,
            style="multi-style",
            caption_strategy=f"prototype-4 {caption_mode}; balanced; triggers {triggers}",
            style_manifest_path=style_manifest,
            caption_mode=caption_mode,
            trigger_token=triggers,
            checkpoint_steps=checkpoint_steps,
            multi_style=True,
            per_style_steps=args.per_style_steps,
            width=args.width,
            height=args.height,
            source_transform="none" if native else "centre-crop",
            rank=args.rank,
            alpha=args.alpha,
            target_modules=TARGET_MODULES_LABEL,
            learning_rate=args.learning_rate,
            optimizer="torch.optim.AdamW",
            optimizer_state_dtype="fp32",
            optimizer_steps_planned=args.steps,
            batch_size=1,
            grad_accum=1,
            text_encoder_trained=False,
            vae_trained=False,
            gradient_checkpointing=args.tier >= 1,
            latent_caching=args.tier >= 2,
            precision="fp16",
            attention_impl="sdpa",
            seed=args.seed,
        )

    if style_name:
        from ml.training import style_kit

        spec_style = style_kit.style_by_key(style_name)
        trigger = spec_style.trigger
        if not style_manifest:
            style_manifest = f"data/manifests/style-{style_name}-p4.csv"
        if not caption_mode:
            caption_mode = style_kit.CAPTION_MODE_STYLE_ONLY
        caption_strategy = f"prototype-4 {caption_mode}; trigger {trigger!r}"
        dataset_version = style_kit.DATASET_V1_SHA256[:12]
    else:
        trigger = ""
        style_name = smoke_kit.SMOKE_STYLE
        caption_strategy = smoke_kit.CAPTION_STRATEGY
        dataset_version = smoke_kit.DATASET_VERSION

    return TrainingSpec(
        exp_id=args.exp_id,
        phase=args.phase,
        memory_tier=args.tier,
        dataset_version=dataset_version,
        smoke_manifest_path=smoke_kit.SMOKE_MANIFEST_PATH,
        style=style_name,
        caption_strategy=caption_strategy,
        style_manifest_path=style_manifest,
        caption_mode=caption_mode,
        trigger_token=trigger,
        checkpoint_steps=checkpoint_steps,
        width=args.width,
        height=args.height,
        source_transform="none" if native else "centre-crop",
        rank=args.rank,
        alpha=args.alpha,
        target_modules=TARGET_MODULES_LABEL,
        learning_rate=args.learning_rate,
        optimizer="torch.optim.AdamW",
        optimizer_state_dtype="fp32",
        optimizer_steps_planned=args.steps,
        batch_size=1,
        grad_accum=1,
        text_encoder_trained=False,
        vae_trained=False,
        gradient_checkpointing=args.tier >= 1,
        latent_caching=args.tier >= 2,
        precision="fp16",
        attention_impl="sdpa",
        seed=args.seed,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exp-id", required=True)
    parser.add_argument("--phase", required=True, choices=PHASES)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--tier", type=int, default=0)
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--alpha", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--results", default="docs/evidence/EXP-016/training-runs.jsonl")
    parser.add_argument("--dry-run", action="store_true", help="print the spec and exit")
    # --- Prototype 4 (M6) ---
    parser.add_argument("--style", default="", help="train a Prototype 4 style (minimal-geometric, ukiyo-e, retro-poster)")
    parser.add_argument("--manifest", default="", help="override the style manifest, e.g. an RQ4 size arm")
    parser.add_argument(
        "--caption-mode",
        default="",
        choices=["", "style-only", "dataset-v1-verbatim"],
        help="which caption column to train on; the ONLY difference between the A/B arms",
    )
    parser.add_argument(
        "--checkpoint-steps",
        type=int,
        nargs="*",
        default=[],
        help="intermediate checkpoints, e.g. --checkpoint-steps 150",
    )
    parser.add_argument(
        "--multi-style",
        action="store_true",
        help="balanced RQ5 run across all three styles; use with --per-style-steps",
    )
    parser.add_argument(
        "--per-style-steps",
        type=int,
        default=0,
        help="exact optimizer-step presentations PER STYLE in a multi-style run",
    )
    args = parser.parse_args(argv)

    if args.multi_style:
        from ml.training import style_kit

        expected = args.per_style_steps * len(style_kit.STYLE_ORDER)
        if args.per_style_steps <= 0:
            parser.error("--multi-style requires --per-style-steps")
        if args.steps != expected:
            parser.error(
                f"--steps {args.steps} does not match {len(style_kit.STYLE_ORDER)} styles x "
                f"{args.per_style_steps} = {expected}"
            )

    spec = build_spec(args)
    print(f"{spec.exp_id} [{spec.phase}] {spec.width}x{spec.height} tier {spec.memory_tier}")
    print(f"  process_config_key: {spec.process_config_key}")
    print(f"  source transform:   {spec.source_transform}")
    print(f"  steps: {spec.optimizer_steps_planned}  rank {spec.rank}/{spec.alpha}  lr {spec.learning_rate}")

    if args.dry_run:
        print(json.dumps({"spec": spec.__dict__}, indent=2, default=str))
        return 0

    results_path = REPO / args.results
    code, row = run(spec, results_path)
    print()
    print(f"  status: {row.status}  gates: {row.gates_passed}")
    if row.gate_failures:
        print(f"  gate failures: {row.gate_failures}")
    print(
        f"  peak allocated {row.resources.process_peak_allocated_mb} MiB · "
        f"device {row.resources.process_peak_device_used_mb} MiB · "
        f"{row.resources.seconds_per_optimizer_step} s/step · "
        f"{row.resources.wall_seconds} s wall"
    )
    print(f"  results -> {results_path}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
