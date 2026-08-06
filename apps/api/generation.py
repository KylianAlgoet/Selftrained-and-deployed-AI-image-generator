"""The single-flight generation service: one GPU, one generation at a time.

THE LOCK IS PROCESS-LOCAL AND THAT IS THE WHOLE DESIGN. It is a `threading.Lock`
acquired non-blocking, so a concurrent request is refused immediately with 409
rather than queued. It means nothing across processes, which is why
`config.assert_single_worker` refuses to start a multi-worker configuration.

Release discipline, stated precisely because getting it wrong is the failure mode
that matters: the lock is released in `finally`, and `finally` is only reached
once `ResidentPipeline.generate` has returned or raised. There is no background
thread and no async cancellation, so there is no path where the HTTP response is
sent while GPU work continues. A client that disconnects or times out changes
nothing on the server - the work finishes, the lock is held until it does, and the
next request is refused with 409 in the meantime.
"""

import logging
import threading
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

from apps.api.config import (
    GENERATION_HEIGHT,
    GENERATION_WIDTH,
    REPO_ROOT,
    Settings,
)
from apps.api.pipeline import (
    DEVICE_TOTAL_MB,
    GenerationAborted,
    PipelineUnavailable,
    ResidentPipeline,
)
from apps.api.schemas import GenerationMetadata
from apps.api.styles import CheckpointUnavailable, production_style
from ml.evaluation import prompt_kit
from ml.inference.reference_schema import IP_ADAPTER_REPO, IP_ADAPTER_REVISION
from ml.training.lora_schema import BASE_MODEL_REPO_ID, BASE_MODEL_REVISION

logger = logging.getLogger("deckforge.api")

GENERATION_ID_PATTERN = r"^[A-Za-z0-9_-]{22}$"


class GenerationBusy(RuntimeError):
    """Another generation holds the GPU. Retry after it finishes."""


class GenerationService:
    def __init__(
        self,
        settings: Settings,
        pipeline: ResidentPipeline | None = None,
        repo_root: Path | None = None,
    ) -> None:
        self.settings = settings
        self.repo_root = repo_root or settings.checkpoint_root or REPO_ROOT
        self.pipeline = pipeline or ResidentPipeline(self.repo_root)
        self._lock = threading.Lock()
        self._registry: OrderedDict[str, Path] = OrderedDict()
        self._metadata: OrderedDict[str, GenerationMetadata] = OrderedDict()

    # --- state ---------------------------------------------------------------

    @property
    def busy(self) -> bool:
        return self._lock.locked()

    def resolve(self, generation_id: str) -> Path | None:
        """Registry lookup, never a path join.

        A generation id from the URL is used ONLY as a dictionary key. It is never
        concatenated with a directory, so a traversal string cannot express a
        filesystem location - it simply is not in the registry.
        """
        return self._registry.get(generation_id)

    def metadata_for(self, generation_id: str) -> GenerationMetadata | None:
        return self._metadata.get(generation_id)

    def _new_generation_id(self) -> str:
        import secrets

        return secrets.token_urlsafe(16)

    def _retain(self, generation_id: str, path: Path, metadata: GenerationMetadata) -> None:
        self._registry[generation_id] = path
        self._metadata[generation_id] = metadata
        while len(self._registry) > self.settings.max_retained_generations:
            old_id, old_path = self._registry.popitem(last=False)
            self._metadata.pop(old_id, None)
            try:
                old_path.unlink(missing_ok=True)
            except OSError:  # pragma: no cover - best effort cleanup
                logger.warning("could not remove expired generation %s", old_id)

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
    ) -> tuple[GenerationMetadata, list[str]]:
        """Run one generation under the busy lock, or raise `GenerationBusy`.

        Raises `CheckpointUnavailable` / `PipelineUnavailable` (-> 503) and
        `GenerationAborted` (-> 504). The deadline is enforced inside the
        denoising loop, so a 504 means the work actually stopped.
        """
        if not self._lock.acquire(blocking=False):
            raise GenerationBusy("a generation is already running")
        try:
            style = production_style(style_key)
            outcome = self.pipeline.generate(
                style_key=style_key,
                subject_prompt=subject_prompt,
                seed=seed,
                lora_weight=lora_weight,
                ip_adapter_scale=ip_adapter_scale,
                reference_image=reference_image,
                deadline_seconds=self.settings.generation_timeout_seconds,
            )

            generation_id = self._new_generation_id()
            self.settings.generated_dir.mkdir(parents=True, exist_ok=True)
            path = self.settings.generated_dir / f"{generation_id}.png"
            path.write_bytes(outcome.image_png)

            warnings: list[str] = []
            if style.is_partial_pass and style.limitation:
                warnings.append(style.limitation)
            spare = round(DEVICE_TOTAL_MB - outcome.device_used_mb, 2)

            metadata = GenerationMetadata(
                generation_id=generation_id,
                created_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                style=style.key,
                style_label=style.label,
                style_outcome=style.outcome,
                style_limitation=style.limitation,
                prompt=outcome.prompt,
                prompt_sha256=prompt_kit.text_sha256(outcome.prompt),
                negative_prompt_sha256=prompt_kit.text_sha256(prompt_kit.NEGATIVE_PROMPT),
                seed=outcome.seed,
                steps=prompt_kit.STEPS,
                steps_run=outcome.steps_run,
                guidance_scale=prompt_kit.GUIDANCE_SCALE,
                scheduler=prompt_kit.SCHEDULER,
                width=GENERATION_WIDTH,
                height=GENERATION_HEIGHT,
                base_model_repo_id=BASE_MODEL_REPO_ID,
                base_model_revision=BASE_MODEL_REVISION,
                lora_run_id=style.run_id,
                lora_checkpoint_step=style.checkpoint_step,
                lora_sha256=outcome.adapter_sha256 or style.sha256,
                lora_weight=float(lora_weight),
                active_adapters=list(outcome.active_adapters),
                live_lora_modules=outcome.live_lora_modules,
                ip_adapter_repo_id=IP_ADAPTER_REPO,
                ip_adapter_revision=IP_ADAPTER_REVISION,
                ip_adapter_scale=outcome.ip_adapter_scale_applied,
                reference_present=outcome.reference_present,
                generate_seconds=outcome.generate_seconds,
                peak_allocated_mb=outcome.peak_allocated_mb,
                peak_device_used_mb=outcome.device_used_mb,
                device_total_mb=DEVICE_TOTAL_MB,
                spare_device_mb=spare,
                image_sha256=outcome.image_sha256,
            )
            self._retain(generation_id, path, metadata)
            return metadata, warnings
        finally:
            # Reached only after the generation call has returned or raised. By
            # this point no GPU work from this request is still running.
            self._lock.release()


__all__ = [
    "CheckpointUnavailable",
    "GenerationAborted",
    "GenerationBusy",
    "GenerationService",
    "PipelineUnavailable",
    "GENERATION_ID_PATTERN",
]
