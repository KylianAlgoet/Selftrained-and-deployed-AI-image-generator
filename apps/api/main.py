"""FastAPI application for DeckForge AI (M7 / Prototype 5).

Start it - one process, no reload - with:

    .venv/Scripts/python.exe -m uvicorn apps.api.main:app \
        --host 127.0.0.1 --port 8000 --workers 1

`--workers 1` is a correctness requirement, not a default. See
`config.assert_single_worker`. `--reload` must be off for any real generation,
EXP-034 run, measurement or evidence capture, because the reloader runs a second
process that would hold the same GPU.

Error policy: the client gets a stable machine-readable `error` code and a short
human message. Local paths, checkpoint paths, library messages and stack traces
go to the server log only.
"""

import logging
import re

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from apps.api.config import (
    GENERATION_HEIGHT,
    GENERATION_WIDTH,
    ConfigurationError,
    load_settings,
)
from apps.api.generation import (
    GENERATION_ID_PATTERN,
    CheckpointUnavailable,
    GenerationAborted,
    GenerationBusy,
    GenerationService,
    PipelineUnavailable,
)
from apps.api.pipeline import DEVICE_TOTAL_MB
from apps.api.schemas import (
    MAX_PROMPT_CHARS,
    ErrorResponse,
    GenerateResponse,
    GenerationProgressResponse,
    HealthResponse,
    StyleInfo,
    StylesResponse,
)
from apps.api.styles import (
    DEFAULT_IP_ADAPTER_SCALE,
    DEFAULT_LORA_WEIGHT,
    IP_ADAPTER_SCALE_MAX,
    IP_ADAPTER_SCALE_MIN,
    LORA_WEIGHT_MAX,
    LORA_WEIGHT_MIN,
    PRODUCTION_STYLES,
    STYLE_KEYS,
    production_style,
)
from apps.api.uploads import UploadRejected, validate_reference_upload

logger = logging.getLogger("deckforge.api")

_ID_RE = re.compile(GENERATION_ID_PATTERN)


def _error(status: int, code: str, detail: str, field: str | None = None) -> JSONResponse:
    payload = ErrorResponse(error=code, detail=detail, field=field)
    return JSONResponse(status_code=status, content=payload.model_dump(exclude_none=True))


def create_app(service: GenerationService | None = None) -> FastAPI:
    settings = load_settings()
    app = FastAPI(
        title="DeckForge AI",
        version="0.5.0",
        description=(
            "Skateboard-decal generation: SD 1.5 with one per-style LoRA and "
            "IP-Adapter reference conditioning, at the 512x1536 deck format."
        ),
    )
    app.state.settings = settings
    app.state.service = service or GenerationService(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        svc: GenerationService = app.state.service
        report = svc.pipeline.device_report()
        return HealthResponse(
            status="ok",
            pid=report["pid"],
            pipeline_loaded=report["pipeline_loaded"],
            active_style=report.get("active_style"),
            generation_in_progress=svc.busy,
            cuda_available=report.get("cuda_available", False),
            device_name=report.get("device_name"),
            device_total_mb=report.get("device_total_mb", DEVICE_TOTAL_MB),
            device_used_mb=report.get("device_used_mb"),
            allocated_mb=report.get("allocated_mb"),
            single_worker_guard="enforced",
        )

    @app.get("/api/generation-progress", response_model=GenerationProgressResponse)
    def generation_progress() -> GenerationProgressResponse:
        """Observe the in-flight generation. Never touches it.

        This endpoint is read-only in the strongest sense available here: it
        acquires no generation lock, starts nothing, cancels nothing, and cannot
        change the pipeline. Polling it during a generation is safe by
        construction, and a client that stops polling changes nothing on the
        server - `POST /api/generate` remains the authoritative request.
        """
        svc: GenerationService = app.state.service
        snapshot = svc.progress_snapshot()
        return GenerationProgressResponse(
            operation_id=snapshot.operation_id,
            status=snapshot.status,
            stage=snapshot.stage,
            current_step=snapshot.current_step,
            total_steps=snapshot.total_steps,
            denoising_fraction=snapshot.denoising_fraction,
            elapsed_seconds=snapshot.elapsed_seconds,
            estimated_remaining_seconds=snapshot.estimated_remaining_seconds,
            pipeline_loaded=snapshot.pipeline_loaded,
        )

    @app.get("/api/styles", response_model=StylesResponse)
    def styles() -> StylesResponse:
        return StylesResponse(
            styles=[
                StyleInfo(
                    key=s.key,
                    label=s.label,
                    outcome=s.outcome,
                    limitation=s.limitation,
                    trigger=s.trigger,
                    run_id=s.run_id,
                    checkpoint_step=s.checkpoint_step,
                )
                for s in PRODUCTION_STYLES
            ],
            width=GENERATION_WIDTH,
            height=GENERATION_HEIGHT,
        )

    @app.post("/api/generate", response_model=GenerateResponse)
    def generate(
        prompt: str = Form(...),
        style: str = Form(...),
        seed: int = Form(None),
        lora_weight: float = Form(DEFAULT_LORA_WEIGHT),
        ip_adapter_scale: float = Form(DEFAULT_IP_ADAPTER_SCALE),
        reference_image: UploadFile | None = File(None),
    ):
        svc: GenerationService = app.state.service
        settings = app.state.settings

        cleaned_prompt = " ".join((prompt or "").split()).strip()
        if not cleaned_prompt:
            return _error(422, "validation_failed", "Describe what to generate.", "prompt")
        if len(cleaned_prompt) > MAX_PROMPT_CHARS:
            return _error(
                422,
                "validation_failed",
                f"Keep the description under {MAX_PROMPT_CHARS} characters.",
                "prompt",
            )
        if style not in STYLE_KEYS:
            return _error(
                422,
                "validation_failed",
                f"Choose one of: {', '.join(STYLE_KEYS)}.",
                "style",
            )
        if not (LORA_WEIGHT_MIN <= lora_weight <= LORA_WEIGHT_MAX):
            return _error(
                422,
                "validation_failed",
                f"Style strength must be between {LORA_WEIGHT_MIN} and {LORA_WEIGHT_MAX}.",
                "lora_weight",
            )
        if not (IP_ADAPTER_SCALE_MIN <= ip_adapter_scale <= IP_ADAPTER_SCALE_MAX):
            return _error(
                422,
                "validation_failed",
                f"Reference influence must be between {IP_ADAPTER_SCALE_MIN} "
                f"and {IP_ADAPTER_SCALE_MAX}.",
                "ip_adapter_scale",
            )

        reference = None
        if reference_image is not None and (reference_image.filename or ""):
            try:
                raw = reference_image.file.read(settings.max_upload_bytes + 1)
                reference = validate_reference_upload(
                    reference_image.filename, reference_image.content_type, raw
                )
            except UploadRejected as rejected:
                return _error(422, "validation_failed", rejected.reason, rejected.field)
            finally:
                # The upload's temporary storage is released here, on every path,
                # before generation begins. Nothing user-supplied is written to
                # disk by this service.
                try:
                    reference_image.file.close()
                except Exception:  # noqa: BLE001
                    pass

        effective_seed = settings.default_seed if seed is None else int(seed)

        try:
            metadata, warnings = svc.generate(
                style_key=style,
                subject_prompt=cleaned_prompt,
                seed=effective_seed,
                lora_weight=float(lora_weight),
                ip_adapter_scale=float(ip_adapter_scale),
                reference_image=reference,
            )
        except GenerationBusy:
            return _error(
                409,
                "generation_in_progress",
                "The GPU is busy with another generation. Try again in a moment.",
            )
        except CheckpointUnavailable as err:
            logger.error("checkpoint unavailable: %s", err)
            return _error(
                503,
                "model_unavailable",
                "A trained style is unavailable on this machine. Check the server log.",
            )
        except PipelineUnavailable as err:
            logger.error("pipeline unavailable: %s", err)
            return _error(
                503, "model_unavailable", "The generation model could not be prepared."
            )
        except GenerationAborted as err:
            logger.warning("generation aborted by deadline: %s", err)
            # The step counts are safe to publish and make the early stop
            # verifiable from the response itself rather than from timing.
            return _error(
                504,
                "generation_timeout",
                f"Generation took too long and was stopped after "
                f"{err.steps_run} of {err.steps_total} steps.",
            )
        except ValueError as err:
            return _error(422, "validation_failed", str(err), "prompt")
        except Exception:  # noqa: BLE001 - never leak internals to the browser
            logger.exception("unexpected generation failure")
            return _error(
                500, "generation_failed", "Generation failed unexpectedly."
            )

        return GenerateResponse(
            generation_id=metadata.generation_id,
            status="completed",
            image_url=f"/api/generated/{metadata.generation_id}",
            metadata=metadata,
            warnings=warnings,
        )

    @app.get("/api/generated/{generation_id}")
    def generated(generation_id: str):
        svc: GenerationService = app.state.service
        if not _ID_RE.match(generation_id):
            return _error(422, "validation_failed", "Malformed image id.", "generation_id")
        path = svc.resolve(generation_id)
        if path is None or not path.is_file():
            return _error(404, "not_found", "That image is no longer available.")
        return FileResponse(path, media_type="image/png")

    @app.exception_handler(ConfigurationError)
    def _configuration_error(_request: Request, err: ConfigurationError):  # pragma: no cover
        logger.error("configuration error: %s", err)
        return _error(503, "configuration_error", "The service is misconfigured.")

    return app


app = create_app()


def _style_keys_for_docs() -> list[str]:  # pragma: no cover - documentation helper
    return [s.key for s in PRODUCTION_STYLES]


__all__ = ["app", "create_app", "production_style", "_style_keys_for_docs"]
