"""Request, response and metadata models.

The metadata block is the point of this file. Every generated image carries the
same identifying facts the experiment rows carry - pinned model revisions,
adapter hash, conditioning scale, seed, sampler settings and measured cost - so an
image produced through the UI can be traced back to the evidence rather than
being an unattributable picture.

What it deliberately does NOT carry: any filesystem path. The browser learns the
adapter's HASH and its public style identity, never where anything lives on disk.
"""

from pydantic import BaseModel, Field

from apps.api.styles import (
    DEFAULT_IP_ADAPTER_SCALE,
    DEFAULT_LORA_WEIGHT,
    IP_ADAPTER_SCALE_MAX,
    IP_ADAPTER_SCALE_MIN,
    LORA_WEIGHT_MAX,
    LORA_WEIGHT_MIN,
)

MAX_PROMPT_CHARS = 400


class GenerationMetadata(BaseModel):
    generation_id: str
    created_utc: str

    style: str
    style_label: str
    style_outcome: str
    style_limitation: str = ""

    prompt: str
    prompt_sha256: str
    negative_prompt_sha256: str

    seed: int
    steps: int
    steps_run: int
    guidance_scale: float
    scheduler: str
    width: int
    height: int

    base_model_repo_id: str
    base_model_revision: str

    lora_run_id: str
    lora_checkpoint_step: int
    lora_sha256: str
    lora_weight: float
    active_adapters: list[str]
    live_lora_modules: int

    ip_adapter_repo_id: str
    ip_adapter_revision: str
    ip_adapter_scale: float
    reference_present: bool

    generate_seconds: float
    peak_allocated_mb: float
    peak_device_used_mb: float
    device_total_mb: float
    spare_device_mb: float

    image_sha256: str


class GenerateResponse(BaseModel):
    generation_id: str
    status: str = "completed"
    image_url: str
    metadata: GenerationMetadata
    warnings: list[str] = Field(default_factory=list)


class StyleInfo(BaseModel):
    key: str
    label: str
    outcome: str
    limitation: str = ""
    trigger: str
    run_id: str
    checkpoint_step: int
    default_lora_weight: float = DEFAULT_LORA_WEIGHT
    lora_weight_min: float = LORA_WEIGHT_MIN
    lora_weight_max: float = LORA_WEIGHT_MAX


class StylesResponse(BaseModel):
    styles: list[StyleInfo]
    default_lora_weight: float = DEFAULT_LORA_WEIGHT
    default_ip_adapter_scale: float = DEFAULT_IP_ADAPTER_SCALE
    ip_adapter_scale_min: float = IP_ADAPTER_SCALE_MIN
    ip_adapter_scale_max: float = IP_ADAPTER_SCALE_MAX
    width: int
    height: int


class GenerationProgressResponse(BaseModel):
    """Read-only telemetry for the generation currently holding the GPU.

    Every field is a number, a short enumerated string, or null. There is no
    path, filename, prompt, image or model object here, and nothing in this
    shape can be used to steer a generation.

    `estimated_remaining_seconds` is null far more often than it is set, and
    that is the point: it is published only while real denoising steps are being
    timed. Model loading and VAE decoding expose no progress signal, so no
    estimate is offered for them rather than a guess dressed up as a measurement.
    """

    operation_id: str | None = None
    status: str
    stage: str
    current_step: int
    total_steps: int
    denoising_fraction: float
    elapsed_seconds: float
    estimated_remaining_seconds: float | None = None
    pipeline_loaded: bool


class HealthResponse(BaseModel):
    status: str
    pid: int
    pipeline_loaded: bool
    active_style: str | None = None
    generation_in_progress: bool
    cuda_available: bool
    device_name: str | None = None
    device_total_mb: float
    device_used_mb: float | None = None
    allocated_mb: float | None = None
    single_worker_guard: str


class ErrorResponse(BaseModel):
    error: str
    detail: str
    field: str | None = None
