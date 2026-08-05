"""Pure data model for the Prototype 3 (M5) LoRA smoke test (RQ1).

Deliberately free of torch/diffusers/PIL imports, exactly like `bench_schema` and
`reference_schema`, so the tier ladder, result rows, filename encoding and all
arithmetic are unit-testable on any machine without a GPU.

Four design intents worth preserving:

1. **The training tier ladder is NOT the inference tier ladder.** The inference
   ladder in `ml.inference.bench_schema` escalates attention slicing, VAE
   slicing and CPU offload - none of which describe what makes a *training* step
   expensive. Conflating the two would let a row claim "tier 2" and mean two
   different things depending on which milestone read it, so this module defines
   its own and a test asserts the two ladders are distinct.

2. **Gradient accumulation is not a memory tier.** At micro-batch 1 it changes
   effective batch size and training semantics but does NOT reduce the peak
   memory of one forward/backward micro-step. It is recorded as a training
   *parameter*, never as an escalation.

3. **Resource use is recorded in phases, not as one number.** A single "peak
   VRAM" figure hides whether the ceiling was hit by the backward pass or by the
   optimizer state - which is exactly the distinction that decides which tier to
   escalate to. `ResourceRecord` keeps them apart and names the boundary at
   which peak statistics were reset.

4. **A run states what it PROVED, not merely that it returned.** `GateRecord`
   carries the technical-success evidence (trainable parameter count, base-model
   frozen, finite non-zero gradients, parameter delta) so a row cannot claim
   success on the strength of "no exception was raised".
"""

import csv
import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

# --- Pinned base model -------------------------------------------------------

# DR-007 selected SD 1.5 for Prototypes 2-5. Pinned to a commit SHA so a Hub-side
# change cannot silently alter what was trained against.
BASE_MODEL_REPO_ID = "stable-diffusion-v1-5/stable-diffusion-v1-5"
BASE_MODEL_REVISION = "451f4fe16113bff5a5d2269ed5ad43b0592e9a14"

# --- Training memory tiers ---------------------------------------------------

# A deeper tier is entered ONLY after a recorded failure. Tier 5 breaks
# comparability and is therefore reported as a separate finding, never as the
# same experiment.
#
# This ladder is deliberately different from the inference ladder in
# `bench_schema.MEMORY_TIERS`. Attention slicing and CPU offload are inference
# remedies; what dominates a training step is activation storage (tier 1),
# the VAE encode pass (tier 2) and optimizer state (tier 3).
TRAINING_MEMORY_TIERS: dict[int, str] = {
    0: "fp16 mixed precision, SDPA attention, no gradient checkpointing, no latent cache",
    1: "gradient checkpointing",
    2: "gradient checkpointing + VAE latents precomputed outside the measured process",
    3: "tier 2 + lower-memory optimizer state (requires an installed, validated optimizer)",
    4: "tier 3 + an officially supported attention/model-memory feature preserving run semantics",
    5: "reduced rank or resolution (BREAKS COMPARABILITY - separate finding)",
}

MAX_COMPARABLE_TRAINING_TIER = 4

# Tiers 0-4 must leave these identical, or the rows are not comparable. Tier 5 is
# the only tier permitted to change them, and only as a labelled deviation.
TIER_INVARIANTS: tuple[str, ...] = (
    "sample_order_sha256",
    "seed",
    "optimizer_steps_planned",
    "caption_strategy",
    "rank",
    "width",
    "height",
)


def next_training_tier(current: int) -> int | None:
    """Escalation path. Returns None when no comparable tier remains."""
    if current >= MAX_COMPARABLE_TRAINING_TIER:
        return None
    return current + 1


def tier_breaks_comparability(tier: int) -> bool:
    return tier > MAX_COMPARABLE_TRAINING_TIER


# --- Run phases --------------------------------------------------------------

# M5 is micro-gated: nothing long starts before something short has proved the
# loop works. Each phase is its own row in its own OS process.
PHASE_SINGLE_STEP = "probe-1step"
PHASE_STABILITY = "probe-10step"
PHASE_SMOKE = "smoke"

# M6 Phase B. Named rather than reusing "smoke", because a 600-step approved
# production run and a 300-step pilot are different claims and must not share a
# label in the evidence.
PHASE_STYLE_FULL = "style-full"
PHASE_MULTI_STYLE = "multi-style"

PHASES: tuple[str, ...] = (
    PHASE_SINGLE_STEP,
    PHASE_STABILITY,
    PHASE_SMOKE,
    PHASE_STYLE_FULL,
    PHASE_MULTI_STYLE,
)

# Plan step 11: no single preliminary probe may run longer than 20 minutes, and
# the smoke run needs explicit approval above 60 minutes.
PROBE_WALL_LIMIT_SECONDS = 20 * 60
SMOKE_WALL_ASK_THRESHOLD_SECONDS = 60 * 60

STATUS_OK = "ok"
STATUS_FAILED = "failed"
STATUS_OOM = "oom"
STATUS_TIMEOUT = "timeout"


# --- Training specification --------------------------------------------------


@dataclass(frozen=True)
class TrainingSpec:
    """One configuration. One OS process. Never two in the same process when VRAM
    or timing is being measured (see docs/evidence/EXP-005/)."""

    exp_id: str
    phase: str
    memory_tier: int

    # data
    dataset_version: str
    smoke_manifest_path: str
    style: str
    caption_strategy: str

    # geometry, and how the 512x1536 sources reach it
    width: int
    height: int
    source_transform: str

    # LoRA
    rank: int
    alpha: int
    target_modules: str

    # optimisation
    learning_rate: float
    optimizer: str
    optimizer_state_dtype: str
    optimizer_steps_planned: int
    batch_size: int
    # Recorded as a parameter. NOT a memory tier: at micro-batch 1 it changes
    # effective batch size, not the peak memory of one micro-step.
    grad_accum: int

    # what is and is not trained
    text_encoder_trained: bool
    vae_trained: bool
    gradient_checkpointing: bool
    latent_caching: bool

    # environment
    precision: str
    attention_impl: str
    seed: int
    base_model_repo_id: str = BASE_MODEL_REPO_ID
    base_model_revision: str = BASE_MODEL_REVISION

    # --- Prototype 4 (M6) additions ------------------------------------------
    # Empty selects the M5 smoke manifest, so existing M5 behaviour is unchanged.
    style_manifest_path: str = ""
    caption_mode: str = ""
    trigger_token: str = ""
    checkpoint_steps: tuple[int, ...] = ()

    # --- M6 Phase B, balanced multi-style (RQ5) -------------------------------
    # When set, the run draws from every style's manifest with exactly
    # `per_style_steps` presentations each, so no style can dominate by having
    # the largest training set.
    multi_style: bool = False
    per_style_steps: int = 0

    @property
    def effective_batch_size(self) -> int:
        return self.batch_size * self.grad_accum

    @property
    def process_config_key(self) -> str:
        """States which OS process produced a row, so the isolation claim is
        auditable from the data rather than promised in prose."""
        return (
            f"{self.exp_id}__{self.phase}__{self.width}x{self.height}"
            f"__tier{self.memory_tier}__r{self.rank}__seed{self.seed}"
        )


# --- Resource measurement ----------------------------------------------------


@dataclass
class ResourceRecord:
    """Phase-separated, because one collapsed peak cannot tell you whether the
    ceiling was hit by activations or by optimizer state - which is exactly what
    decides the next tier.

    `reset_boundaries` names each point at which torch peak statistics were
    reset, so the figures can be audited rather than trusted.
    """

    post_load_allocated_mb: float | str = "not measured"
    post_load_reserved_mb: float | str = "not measured"
    post_load_device_used_mb: float | str = "not measured"

    peak_forward_backward_allocated_mb: float | str = "not measured"
    peak_optimizer_step_allocated_mb: float | str = "not measured"

    process_peak_allocated_mb: float | str = "not measured"
    process_peak_reserved_mb: float | str = "not measured"
    process_peak_device_used_mb: float | str = "not measured"
    peak_process_rss_mb: float | str = "not measured"

    wall_seconds: float | str = "not measured"
    seconds_per_optimizer_step: float | str = "not measured"

    reset_boundaries: str = ""


# --- Technical-success gates -------------------------------------------------


@dataclass
class GateRecord:
    """What the run PROVED. A row may not claim success because nothing raised.

    Every field here is read back from the live objects after the fact, not
    inferred from a call returning without error - the standard EXP-007 set for
    the IP-Adapter environment gate.
    """

    trainable_lora_parameters: int = 0
    trainable_lora_tensors: int = 0
    expected_trainable_parameters: int | str = "not measured"
    base_unet_parameters_frozen: bool | str = "not measured"
    optimizer_steps_completed: int = 0
    global_steps_completed: int = 0
    gradients_present: bool | str = "not measured"
    gradients_finite: bool | str = "not measured"
    gradients_nonzero: bool | str = "not measured"
    losses_finite: bool | str = "not measured"
    first_loss: float | str = "not measured"
    last_loss: float | str = "not measured"
    # Deliberately NOT a pass condition: a few-hundred-step run on 12 images is
    # far too short and noisy for a loss trend to mean anything. Recorded because
    # it is useful evidence, never gated on.
    loss_decreased: bool | str = "not measured"
    lora_params_sha256_before: str = ""
    lora_params_sha256_after: str = ""
    lora_params_l2_delta: float | str = "not measured"
    lora_params_changed: bool | str = "not measured"

    def passed(self) -> bool:
        """The technical-success definition, all of which must hold.

        `loss_decreased` is intentionally absent.
        """
        return bool(
            self.trainable_lora_parameters > 0
            and self.expected_trainable_parameters == self.trainable_lora_parameters
            and self.base_unet_parameters_frozen is True
            and self.optimizer_steps_completed >= 1
            and self.gradients_present is True
            and self.gradients_finite is True
            and self.gradients_nonzero is True
            and self.losses_finite is True
            and self.lora_params_changed is True
        )

    def failures(self) -> list[str]:
        """Which gates did not hold, for an honest failure row."""
        checks = {
            "trainable_lora_parameters > 0": self.trainable_lora_parameters > 0,
            "trainable parameter count matches expectation": (
                self.expected_trainable_parameters == self.trainable_lora_parameters
            ),
            "base UNet parameters frozen": self.base_unet_parameters_frozen is True,
            "at least one optimizer step": self.optimizer_steps_completed >= 1,
            "gradients present": self.gradients_present is True,
            "gradients finite": self.gradients_finite is True,
            "gradients non-zero": self.gradients_nonzero is True,
            "losses finite": self.losses_finite is True,
            "LoRA parameters changed from init": self.lora_params_changed is True,
        }
        return [name for name, ok in checks.items() if not ok]


# --- Saved adapter -----------------------------------------------------------


@dataclass
class AdapterArtifact:
    """The checkpoint, described well enough to prove it is a LoRA and not a
    smuggled copy of the base model."""

    path: str = ""
    sha256: str = ""
    size_bytes: int = 0
    tensor_count: int = 0
    lora_key_count: int = 0
    # Any key that looks like a full base-model weight rather than a LoRA delta.
    # Must be empty: committing or shipping base weights is both a licence and a
    # repository-size problem.
    unexpected_base_model_keys: str = ""
    reload_ok: bool | str = "not measured"
    reloaded_adapter_modules: int | str = "not measured"

    def is_lora_only(self) -> bool:
        return self.lora_key_count > 0 and not self.unexpected_base_model_keys


# --- Result row --------------------------------------------------------------


@dataclass
class TrainingResultRow:
    exp_id: str
    phase: str
    timestamp_utc: str
    process_config_key: str

    base_model_repo_id: str
    base_model_revision_sha: str
    torch_version: str
    torch_cuda_version: str
    diffusers_version: str
    peft_version: str
    gpu_name: str

    dataset_version: str
    smoke_manifest_path: str
    smoke_kit_fingerprint: str
    sample_order_sha256: str
    style: str
    caption_strategy: str
    item_count: int

    width: int
    height: int
    source_transform: str
    rank: int
    alpha: int
    target_modules: str
    learning_rate: float
    optimizer: str
    optimizer_state_dtype: str
    optimizer_steps_planned: int
    batch_size: int
    grad_accum: int
    effective_batch_size: int
    text_encoder_trained: bool
    vae_trained: bool
    gradient_checkpointing: bool
    latent_caching: bool
    precision: str
    attention_impl: str
    seed: int
    memory_tier: int

    resources: ResourceRecord = field(default_factory=ResourceRecord)
    gates: GateRecord = field(default_factory=GateRecord)
    adapter: AdapterArtifact = field(default_factory=AdapterArtifact)

    status: str = STATUS_OK
    gates_passed: bool | str = "not measured"
    gate_failures: str = ""
    error_type: str = ""
    error_message: str = ""

    # --- Prototype 4 (M6) additions ------------------------------------------
    # Empty on the M5 smoke rows, which predate per-style training. Appended
    # rather than inserted so the existing EXP-016/017 JSONL stays readable.
    trigger_token: str = ""
    trigger_token_ids: str = ""
    caption_mode: str = ""
    style_manifest_path: str = ""
    style_manifest_sha256: str = ""
    style_kit_fingerprint: str = ""
    # How many times each item was actually presented, as "DS-0001:7;DS-0002:7".
    # This is what makes the RQ4 equal-compute confound auditable: at a fixed
    # step count a 12-image arm presents each item far more often than a
    # 44-image arm, and those numbers must be visible in the record rather than
    # left to be inferred from steps / len(items).
    item_presentation_counts: str = ""
    presentations_per_item_mean: float | str = "not measured"
    loss_history_path: str = ""
    # "step:sha256:bytes" per saved checkpoint, semicolon separated.
    checkpoints: str = ""

    # --- M6 Phase B, balanced multi-style (RQ5) -------------------------------
    # Per-style optimizer-step presentations, as "minimal-geometric:600;ukiyo-e:600".
    # RQ5's comparison is only fair if each style got the SAME exposure it got in
    # its own per-style run, so the exposure is recorded per style rather than
    # divided out of a single total afterwards.
    per_style_exposure: str = ""
    per_style_item_counts: str = ""
    multi_style_manifest_sha256: str = ""


FIELDNAMES: list[str] = [f.name for f in fields(TrainingResultRow)]


def flatten(row: TrainingResultRow | dict) -> dict:
    """Flatten the nested records into one CSV-friendly mapping.

    Nested dataclasses keep the JSONL readable and the code honest; a flat CSV
    keeps the evidence greppable. Both are written from the same source.
    """
    data = asdict(row) if isinstance(row, TrainingResultRow) else dict(row)
    flat: dict = {}
    for key, value in data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flat[f"{key}_{sub_key}"] = sub_value
        else:
            flat[key] = value
    return flat


def build_run_slug(spec: TrainingSpec) -> str:
    """Every varying condition visible in the name, so a stray artefact can always
    be traced back to the run that produced it."""
    lr = f"{spec.learning_rate:g}".replace(".", "p").replace("-", "m")
    return (
        f"{spec.exp_id}__{spec.phase}__{spec.width}x{spec.height}"
        f"__r{spec.rank}a{spec.alpha}__lr{lr}__bs{spec.batch_size}x{spec.grad_accum}"
        f"__st{spec.optimizer_steps_planned}__seed{spec.seed}__tier{spec.memory_tier}"
    )


# --- Writers -----------------------------------------------------------------


def write_jsonl(rows: list[TrainingResultRow], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        for row in rows:
            fh.write(json.dumps(asdict(row), sort_keys=True) + "\n")
    return path


def append_jsonl(row: TrainingResultRow, path: str | Path) -> Path:
    """Append as each run finishes, so a crash mid-milestone loses nothing."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(asdict(row), sort_keys=True) + "\n")
    return path


def read_jsonl(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_csv(rows: list[TrainingResultRow] | list[dict], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flat_rows = [flatten(r) for r in rows]
    if not flat_rows:
        raise ValueError("refusing to write an empty result CSV")
    names: list[str] = []
    for flat in flat_rows:
        for key in flat:
            if key not in names:
                names.append(key)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=names)
        writer.writeheader()
        for flat in flat_rows:
            writer.writerow({name: flat.get(name, "") for name in names})
    return path


# --- Reporting ---------------------------------------------------------------


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    if value is None or value == "":
        return "not measured"
    return str(value)


def render_summary_markdown(rows: list[dict], title: str, device_total_mb: float) -> str:
    """One table, with the device ceiling stated on every row.

    The ceiling is printed deliberately: a peak is meaningless without it, and
    R12 exists precisely because a figure close to the ceiling was at risk of
    being described as comfortable.
    """
    lines = [
        f"# {title}",
        "",
        f"Physical VRAM: **{device_total_mb:.1f} MiB**. Every peak below is stated against it.",
        "",
        "| exp | phase | geometry | tier | status | gates | peak alloc MiB | peak device MiB | "
        "spare MiB | s/step | wall s |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        flat = flatten(row)
        device_peak = flat.get("resources_process_peak_device_used_mb")
        spare = (
            f"{device_total_mb - device_peak:.1f}"
            if isinstance(device_peak, (int, float))
            else "not measured"
        )
        gates = flat.get("gates_passed")
        gates_text = "PASS" if gates is True else ("FAIL" if gates is False else "not measured")
        lines.append(
            f"| {flat.get('exp_id')} | {flat.get('phase')} | "
            f"{flat.get('width')}x{flat.get('height')} | {flat.get('memory_tier')} | "
            f"{flat.get('status')} | {gates_text} | "
            f"{_fmt(flat.get('resources_process_peak_allocated_mb'))} | "
            f"{_fmt(device_peak)} | {spare} | "
            f"{_fmt(flat.get('resources_seconds_per_optimizer_step'))} | "
            f"{_fmt(flat.get('resources_wall_seconds'))} |"
        )

    failures = [
        (flatten(r).get("exp_id"), flatten(r).get("gate_failures"))
        for r in rows
        if flatten(r).get("gate_failures")
    ]
    if failures:
        lines += ["", "## Gate failures", ""]
        lines += [f"- **{exp_id}**: {detail}" for exp_id, detail in failures]
    return "\n".join(lines) + "\n"
