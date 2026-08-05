"""The resident generation pipeline: SD 1.5 + one per-style LoRA + IP-Adapter.

ONE instance, ONE process, loaded lazily on the first generation request and kept
for the process lifetime. See `config.assert_single_worker` for why a second
process is not merely wasteful but impossible: EXP-019b and EXP-032 measured this
stack at 7985.5 MiB of 8187.5 MiB physical, leaving 202.0 MiB. That is 2.5 % of
the device and it is NOT comfortable headroom.

This module does not re-implement the stack. It calls the same
`ml.inference.reference_conditioning` helpers the measured experiments used,
including the pinned-image-encoder workaround, and it applies the adapter weight
through `cross_attention_kwargs={"scale": ...}` exactly as
`ml/training/final_matrix.py` did - because that is the mechanism behind the
images Kylian actually scored.

torch and diffusers are imported inside methods, following the pattern the ML
runners already use, so importing this module (and therefore the whole app) costs
nothing and needs no GPU. The API test suite relies on that.
"""

import hashlib
import io
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from apps.api.config import GENERATION_HEIGHT, GENERATION_WIDTH, REPO_ROOT
from apps.api.styles import (
    DEFAULT_IP_ADAPTER_SCALE,
    CheckpointUnavailable,
    ProductionStyle,
    production_style,
    verify_checkpoint,
)
from ml.evaluation import prompt_kit
from ml.inference.reference_schema import (
    IP_ADAPTER_REPO,
    IP_ADAPTER_REVISION,
    IP_ADAPTER_SUBFOLDER,
)
from ml.training.lora_schema import BASE_MODEL_REPO_ID, BASE_MODEL_REVISION

MIB = 1024**2
DEVICE_TOTAL_MB = 8187.5
IP_ADAPTER_WEIGHT_NAME = "ip-adapter_sd15.safetensors"

# The neutral reference used for prompt-only requests. See `neutral_reference`.
NEUTRAL_REFERENCE_SIZE = 512
NEUTRAL_REFERENCE_LEVEL = 128


class GenerationAborted(RuntimeError):
    """The deadline fired and the denoising loop was stopped at a step boundary."""


class PipelineUnavailable(RuntimeError):
    """The pipeline could not be built or a required artifact is unusable."""


@dataclass
class GenerationOutcome:
    image_png: bytes
    image_sha256: str
    prompt: str
    seed: int
    steps_run: int
    generate_seconds: float
    load_seconds: float
    peak_allocated_mb: float
    peak_reserved_mb: float
    allocated_before_mb: float
    allocated_after_mb: float
    reserved_before_mb: float
    reserved_after_mb: float
    device_used_mb: float
    process_rss_mb: float
    active_adapters: tuple[str, ...]
    live_lora_modules: int
    ip_adapter_scale_applied: float
    reference_present: bool
    adapter_sha256: str = ""
    extra: dict = field(default_factory=dict)


def neutral_reference():
    """A fixed mid-grey image, used ONLY to satisfy a structural requirement.

    Why this exists at all. With IP-Adapter resident, diffusers 0.39.0 sets
    `added_cond_kwargs = None` when no reference is passed
    (`pipeline_stable_diffusion.py:1014-1018`), and the UNet then RAISES, because
    `encoder_hid_dim_type == "ip_image_proj"` requires `image_embeds`
    (`unet_2d_condition.py:964-967`). So a prompt-only request cannot simply omit
    the image while the adapter is loaded - it is not a stylistic choice.

    The two real options were to unload the adapter for prompt-only requests
    (`unload_ip_adapter()` discards the 2.35 GiB CLIP encoder, so every toggle
    would pay to rebuild it) or to keep it resident at scale 0.0. The second was
    chosen because M4 already MEASURED it: 12/12 IP-Adapter runs at scale 0.0 were
    byte-identical to the text-only baseline.

    That measurement used real reference images, not this placeholder, so the
    claim being relied on - that at scale 0.0 the image cannot affect the result -
    is verified separately by a test that generates from two DIFFERENT neutral
    images at scale 0.0 and requires byte-identical output. A previous user's
    reference is never reused for this; the placeholder is constructed from
    constants on every call.
    """
    from PIL import Image

    return Image.new(
        "RGB",
        (NEUTRAL_REFERENCE_SIZE, NEUTRAL_REFERENCE_SIZE),
        (NEUTRAL_REFERENCE_LEVEL,) * 3,
    )


class ResidentPipeline:
    """Holds the loaded stack and the identity of whichever style is active."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or REPO_ROOT
        self._pipe = None
        self._active_style: str | None = None
        self._active_adapter_sha: str = ""
        self._load_seconds: float = 0.0
        self._image_encoder_revision: str = ""

    # --- state ---------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._pipe is not None

    @property
    def active_style(self) -> str | None:
        return self._active_style

    def device_report(self) -> dict:
        """Best-effort device facts for /api/health. Never raises."""
        report = {
            "pid": os.getpid(),
            "pipeline_loaded": self.is_loaded,
            "active_style": self._active_style,
            "device_total_mb": DEVICE_TOTAL_MB,
        }
        try:
            import torch

            report["cuda_available"] = bool(torch.cuda.is_available())
            if torch.cuda.is_available():
                report["device_name"] = torch.cuda.get_device_name(0)
                free, total = torch.cuda.mem_get_info()
                report["device_used_mb"] = round((total - free) / MIB, 2)
                report["allocated_mb"] = round(torch.cuda.memory_allocated() / MIB, 2)
        except Exception:  # noqa: BLE001 - health must never fail on a probe
            report["cuda_available"] = False
        return report

    # --- loading -------------------------------------------------------------

    def ensure_loaded(self) -> None:
        if self._pipe is not None:
            return

        import torch
        from diffusers import DPMSolverMultistepScheduler, StableDiffusionPipeline

        from ml.inference.reference_conditioning import (
            adapter_attention_processors,
            attach_ip_adapter,
        )
        from ml.inference.reference_schema import MethodSpec

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
                note="M7 resident service",
            )
            self._image_encoder_revision = attach_ip_adapter(pipe, method, "float16")
            if not adapter_attention_processors(pipe):
                raise PipelineUnavailable(
                    "load_ip_adapter installed no IP-Adapter attention processor"
                )
            pipe.set_ip_adapter_scale(DEFAULT_IP_ADAPTER_SCALE)
        except PipelineUnavailable:
            raise
        except Exception as err:  # noqa: BLE001 - surfaced as 503, logged in full
            raise PipelineUnavailable(f"{type(err).__name__}: {err}") from err

        self._pipe = pipe
        self._load_seconds = round(time.perf_counter() - started, 3)

    # --- LoRA lifecycle ------------------------------------------------------

    def loaded_adapter_names(self) -> tuple[str, ...]:
        """Adapter names diffusers reports as loaded, across all components."""
        if self._pipe is None:
            return ()
        try:
            listed = self._pipe.get_list_adapters()
        except Exception:  # noqa: BLE001 - treated as "cannot verify"
            return ()
        names: list[str] = []
        for component_adapters in listed.values():
            for name in component_adapters:
                if name not in names:
                    names.append(name)
        return tuple(names)

    def live_lora_modules(self) -> int:
        if self._pipe is None:
            return 0
        return sum(1 for _, m in self._pipe.unet.named_modules() if hasattr(m, "lora_A"))

    def activate_style(self, style_key: str) -> ProductionStyle:
        """Make exactly one style's adapter live, and verify that it is.

        Every switch re-verifies the checkpoint hash and then CHECKS THE LIVE
        STATE rather than trusting that `load_lora_weights` returned without
        raising. Silently generating with the previous style's adapter would be
        indistinguishable from success in the response, and would quietly
        misattribute an image to a style that never produced it.
        """
        self.ensure_loaded()
        style = production_style(style_key)
        adapter_path = verify_checkpoint(style, self.repo_root)

        # Unload unconditionally, including when the same style is requested
        # again, so there is exactly one code path and no way to accumulate.
        self._pipe.unload_lora_weights()
        self._active_style = None
        self._active_adapter_sha = ""

        residual = self.loaded_adapter_names()
        if residual:
            raise PipelineUnavailable(
                f"adapters still loaded after unload: {list(residual)}"
            )

        self._pipe.load_lora_weights(
            str(adapter_path.parent),
            weight_name=adapter_path.name,
            adapter_name=style.key,
        )

        active = self.loaded_adapter_names()
        if active != (style.key,):
            raise PipelineUnavailable(
                f"expected exactly one active adapter {style.key!r}, found {list(active)}"
            )
        modules = self.live_lora_modules()
        if modules == 0:
            raise PipelineUnavailable(
                f"{style.key}: adapter loaded but no live LoRA modules are present"
            )

        self._active_style = style.key
        self._active_adapter_sha = style.sha256
        return style

    # --- generation ----------------------------------------------------------

    def generate(
        self,
        *,
        style_key: str,
        subject_prompt: str,
        seed: int,
        lora_weight: float,
        ip_adapter_scale: float,
        reference_image=None,
        deadline_seconds: float | None = None,
        width: int = GENERATION_WIDTH,
        height: int = GENERATION_HEIGHT,
    ) -> GenerationOutcome:
        """Run one generation. Raises `GenerationAborted` if the deadline fires.

        The caller holds the busy lock for the whole of this call and releases it
        only after this returns or raises - by then the GPU work has genuinely
        stopped.
        """
        import psutil
        import torch

        from apps.api.styles import build_prompt
        from ml.inference.reference_conditioning import preprocess_for_adapter

        style = self.activate_style(style_key)
        pipe = self._pipe
        assert pipe is not None  # activate_style guarantees this

        reference_present = reference_image is not None
        if reference_present:
            prepared, reference_note = preprocess_for_adapter(reference_image.convert("RGB"))
            scale_applied = float(ip_adapter_scale)
        else:
            # Structural requirement, not conditioning: see `neutral_reference`.
            prepared, reference_note = preprocess_for_adapter(neutral_reference())
            scale_applied = 0.0

        prompt = build_prompt(style.key, subject_prompt)

        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        allocated_before = round(torch.cuda.memory_allocated() / MIB, 2)
        reserved_before = round(torch.cuda.memory_reserved() / MIB, 2)

        pipe.set_ip_adapter_scale(scale_applied)
        pipe._interrupt = False

        steps_seen = {"count": 0}
        deadline = None if deadline_seconds is None else time.perf_counter() + deadline_seconds

        def on_step_end(inner_pipe, step_index, timestep, callback_kwargs):
            steps_seen["count"] = step_index + 1
            if deadline is not None and time.perf_counter() > deadline:
                # The SUPPORTED diffusers abort: the denoising loop checks
                # `self.interrupt` at the top of every step
                # (pipeline_stable_diffusion.py:1033). Setting it here stops the
                # loop at the next step boundary rather than tearing anything
                # down mid-step.
                inner_pipe._interrupt = True
            return callback_kwargs

        generator = torch.Generator(device="cuda").manual_seed(int(seed))
        started = time.perf_counter()
        try:
            result = pipe(
                prompt=prompt,
                negative_prompt=prompt_kit.NEGATIVE_PROMPT,
                ip_adapter_image=prepared,
                num_inference_steps=prompt_kit.STEPS,
                guidance_scale=prompt_kit.GUIDANCE_SCALE,
                width=width,
                height=height,
                generator=generator,
                cross_attention_kwargs={"scale": float(lora_weight)},
                callback_on_step_end=on_step_end,
            )
            generate_seconds = round(time.perf_counter() - started, 3)
            interrupted = bool(getattr(pipe, "_interrupt", False))
        finally:
            # Request-specific conditioning is reset here, not at the next
            # request's start, so no state can outlive the request that set it -
            # including when the request failed.
            try:
                pipe.set_ip_adapter_scale(DEFAULT_IP_ADAPTER_SCALE)
                pipe._interrupt = False
            except Exception:  # noqa: BLE001 - never mask the original failure
                pass

        if interrupted:
            raise GenerationAborted(
                f"generation exceeded its deadline and was stopped after "
                f"{steps_seen['count']} of {prompt_kit.STEPS} steps"
            )

        image = result.images[0]
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        png = buffer.getvalue()

        torch.cuda.synchronize()
        free, total = torch.cuda.mem_get_info()
        process = psutil.Process()

        return GenerationOutcome(
            image_png=png,
            image_sha256=hashlib.sha256(png).hexdigest(),
            prompt=prompt,
            seed=int(seed),
            steps_run=steps_seen["count"],
            generate_seconds=generate_seconds,
            load_seconds=self._load_seconds,
            peak_allocated_mb=round(torch.cuda.max_memory_allocated() / MIB, 2),
            peak_reserved_mb=round(torch.cuda.max_memory_reserved() / MIB, 2),
            allocated_before_mb=allocated_before,
            allocated_after_mb=round(torch.cuda.memory_allocated() / MIB, 2),
            reserved_before_mb=reserved_before,
            reserved_after_mb=round(torch.cuda.memory_reserved() / MIB, 2),
            device_used_mb=round((total - free) / MIB, 2),
            process_rss_mb=round(process.memory_info().rss / MIB, 2),
            active_adapters=self.loaded_adapter_names(),
            live_lora_modules=self.live_lora_modules(),
            ip_adapter_scale_applied=scale_applied,
            reference_present=reference_present,
            adapter_sha256=self._active_adapter_sha,
            extra={
                "reference_preprocessing": reference_note,
                "image_encoder_revision": self._image_encoder_revision,
            },
        )


__all__ = [
    "CheckpointUnavailable",
    "GenerationAborted",
    "GenerationOutcome",
    "PipelineUnavailable",
    "ResidentPipeline",
    "neutral_reference",
]
