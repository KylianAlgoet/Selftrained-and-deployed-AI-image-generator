"""Pure data model for the Prototype 2 reference-conditioning comparison (RQ6, RQ7).

Deliberately free of torch/diffusers/PIL imports, exactly like `bench_schema`, so
the method registry, reference registry, condition table, level mapping, and all
arithmetic are unit-testable on any machine without a GPU.

Three design intents worth preserving:

1. **Generation measurement is separated from similarity evaluation.** The
   generation row (`ReferenceResultRow`) carries no similarity indicator at all.
   Phase 2 writes `SimilarityRow` into a separate file, joined on
   `output_sha256`. A metric model must never be loaded inside a process whose
   VRAM and latency figures describe a generation method.
2. **The influence-level mapping is an assumption under test, not a calibrated
   equivalence.** img2img `strength` is *inverted* (lower = stronger reference)
   while IP-Adapter `scale` is intuitive, so both the raw parameter and the
   normalised level travel with every row and a test guards the inversion.
3. **The process boundary is recorded, not asserted.** `process_config_key`
   states which OS process produced each row, so the isolation claim in
   `docs/evidence/prototype-2/process-isolation-check.md` is auditable from data.
"""

import csv
import json
import statistics
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

# --- Method registry ---------------------------------------------------------


@dataclass(frozen=True)
class MethodSpec:
    key: str
    label: str
    slug: str
    # Empty for the two SD 1.5-native arms: they download nothing at all.
    repo_id: str
    subfolder: str
    weight_name: str
    # The method's own native reference-strength parameter, recorded verbatim per
    # run so a chart can never be read against the wrong scale.
    strength_param_name: str
    strength_inverted: bool
    loads_image_encoder: bool
    note: str


# `.safetensors` only. The `.bin` twins in the same repository are pickles and
# .claude/rules/security.md treats untrusted binaries as untrusted.
IP_ADAPTER_REPO = "h94/IP-Adapter"
IP_ADAPTER_SUBFOLDER = "models"
IP_ADAPTER_IMAGE_ENCODER_SUBFOLDER = "models/image_encoder"

# Resolved and verified against the Hub on 2026-07-31; recorded here so a run is
# reproducible from the repository alone. Applied to BOTH the adapter weights and
# the image encoder - diffusers 0.39.0 does not forward `revision` to the encoder
# (loaders/ip_adapter.py:207), so the runner registers a pinned encoder itself.
IP_ADAPTER_REVISION = "018e402774aeeddd60609b4ecdb7e298259dc729"

METHODS: dict[str, MethodSpec] = {
    "text-only": MethodSpec(
        key="text-only",
        label="SD 1.5 text-only baseline",
        slug="text-only",
        repo_id="",
        subfolder="",
        weight_name="",
        strength_param_name="",
        strength_inverted=False,
        loads_image_encoder=False,
        note="control arm; without it no similarity number means anything",
    ),
    "img2img": MethodSpec(
        key="img2img",
        label="SD 1.5 img2img",
        slug="img2img",
        repo_id="",
        subfolder="",
        weight_name="",
        strength_param_name="strength",
        # Lower strength = fewer denoising steps = MORE of the reference survives.
        strength_inverted=True,
        loads_image_encoder=False,
        note="zero extra weights, zero extra VRAM; couples reference influence to denoising strength",
    ),
    "ip-adapter": MethodSpec(
        key="ip-adapter",
        label="IP-Adapter (base, SD 1.5)",
        slug="ip-adapter",
        repo_id=IP_ADAPTER_REPO,
        subfolder=IP_ADAPTER_SUBFOLDER,
        weight_name="ip-adapter_sd15.safetensors",
        strength_param_name="scale",
        strength_inverted=False,
        loads_image_encoder=True,
        note="attention-side scale, independent of output geometry",
    ),
    "ip-adapter-plus": MethodSpec(
        key="ip-adapter-plus",
        label="IP-Adapter-Plus (SD 1.5)",
        slug="ip-adapter-plus",
        repo_id=IP_ADAPTER_REPO,
        subfolder=IP_ADAPTER_SUBFOLDER,
        weight_name="ip-adapter-plus_sd15.safetensors",
        strength_param_name="scale",
        strength_inverted=False,
        loads_image_encoder=True,
        note="within-method variant probing content preservation vs style influence; medium level only",
    ),
}

# Methods that attach an adapter to the UNet. Used by the runner to decide
# whether an image encoder is loaded at all - see the Phase-1 process table.
ADAPTER_METHODS = tuple(key for key, spec in METHODS.items() if spec.loads_image_encoder)


# --- Influence levels --------------------------------------------------------

INFLUENCE_LEVELS: tuple[str, ...] = ("none", "weak", "medium", "strong")

# Shared levels mapped onto each method's native parameter. THIS MAPPING IS AN
# ASSUMPTION UNDER TEST, NOT A CALIBRATED EQUIVALENCE: nothing establishes that
# img2img strength 0.65 and IP-Adapter scale 0.55 exert comparable influence.
# It exists so the comparison has a shared axis, and it is stated as an
# assumption wherever it is used.
LEVEL_VALUES: dict[str, dict[str, float]] = {
    # "none" for img2img is text-to-image with no init image at all, which is the
    # text-only arm - so img2img has no "none" value of its own.
    "img2img": {"weak": 0.85, "medium": 0.65, "strong": 0.40},
    "ip-adapter": {"none": 0.0, "weak": 0.25, "medium": 0.55, "strong": 0.85},
    "ip-adapter-plus": {"none": 0.0, "weak": 0.25, "medium": 0.55, "strong": 0.85},
}

# Full sweeps for the strength-sweep grids required by issue #5.
SWEEP_VALUES: dict[str, tuple[float, ...]] = {
    "img2img": (0.90, 0.75, 0.60, 0.45, 0.30),
    "ip-adapter": (0.20, 0.40, 0.60, 0.80, 1.00),
    "ip-adapter-plus": (0.20, 0.40, 0.60, 0.80, 1.00),
}


def influence_value(method_key: str, level: str) -> float:
    """Native parameter value for a shared influence level."""
    try:
        return LEVEL_VALUES[method_key][level]
    except KeyError as err:
        raise KeyError(f"no {level!r} level defined for method {method_key!r}") from err


def level_for_value(method_key: str, value: float) -> str:
    """Nearest shared level for a raw parameter value.

    Written so the inverted axis is handled by the table rather than by
    arithmetic that could silently flip: for img2img the SMALLEST strength maps
    to `strong`, and a unit test asserts exactly that.
    """
    table = LEVEL_VALUES[method_key]
    return min(table, key=lambda level: abs(table[level] - value))


def effective_steps(method_key: str, steps: int, strength_value: float | None) -> int:
    """Denoising steps actually executed.

    Diffusers' img2img runs `int(steps * strength)` steps, so a STRONGER
    reference is also FASTER. Comparing raw wall-clock across strengths, or
    against IP-Adapter, would therefore be meaningless; latency is additionally
    reported per effective step.
    """
    if method_key == "img2img":
        if strength_value is None:
            raise ValueError("img2img requires a strength value to compute effective steps")
        return int(steps * strength_value)
    return steps


def retained_area_fraction(
    source_width: int, source_height: int, target_width: int, target_height: int
) -> float:
    """Fraction of a reference image surviving a centre-crop to the target aspect.

    img2img forces the reference into the output resolution, so this quantifies
    what that costs instead of merely describing it. IP-Adapter does not crop to
    the output geometry, so this is recorded as 1.0 for adapter arms.
    """
    if min(source_width, source_height, target_width, target_height) <= 0:
        raise ValueError("dimensions must be positive")
    source_aspect = source_width / source_height
    target_aspect = target_width / target_height
    return min(source_aspect, target_aspect) / max(source_aspect, target_aspect)


# --- Reference registry ------------------------------------------------------


@dataclass(frozen=True)
class ReferenceSpec:
    id: str
    category: str
    # "dataset-holdout" or "generated"
    origin: str
    dataset_item_id: str
    generator_seed: int | None
    width: int
    height: int
    licence: str
    permitted_use: str
    # Where the bytes originate. Empty for R4, which is generated from a seed
    # rather than copied from anywhere.
    source_path: str
    # Repo-relative location the runner actually reads. For the committed
    # references this is a byte-identical copy under `data/references/`, so the
    # SHA-256 is unchanged and the manifest link still holds.
    repo_path: str
    # Project-original references are committed (tiny, licence-clean, byte
    # reproducible from a seed). Externally sourced ones are not, consistent with
    # the existing "raw images stay out of Git" policy; their manifest ID +
    # SHA-256 makes them re-derivable.
    committed: bool
    note: str


# SHA-256 values are copied from `data/manifests/dataset-v1.csv` and re-verified
# against the file on disk by `scripts/build_reference_kit.py`. R4's hash is
# filled in by that script from the byte-exact seeded generation.
REFERENCES: dict[str, ReferenceSpec] = {
    "R1": ReferenceSpec(
        id="R1",
        category="retro-poster",
        origin="dataset-holdout",
        dataset_item_id="DS-0077",
        generator_seed=None,
        width=690,
        height=1024,
        licence="public domain",
        permitted_use="public domain (Library of Congress, no known restrictions)",
        source_path="data/raw/retro-poster/loc-98518996.jpg",
        repo_path="data/raw/retro-poster/loc-98518996.jpg",
        committed=False,
        note="verified by inspection: a portrait WPA theatre poster ('Federal Mayan Theatre'), "
        "photographed inside a dark frame and dominated by lettering. Style-matched to P1-poster, "
        "but it carries the same frame and typography properties as R5 - so R5 is the harder case "
        "by orientation, not by being the only framed or text-bearing reference",
    ),
    "R2": ReferenceSpec(
        id="R2",
        category="minimal-geometric",
        origin="dataset-holdout",
        dataset_item_id="DS-0048",
        generator_seed=None,
        width=512,
        height=1536,
        licence="project-original",
        permitted_use="project-original, generated by ml/dataset/generate_geometric.py",
        source_path="data/raw/minimal-geometric/geo-1047.png",
        repo_path="data/references/R2-DS-0048-geo-1047.png",
        committed=True,
        note="already 1:3; the only reference needing no crop at the deck format",
    ),
    "R3": ReferenceSpec(
        id="R3",
        category="ukiyo-e",
        origin="dataset-holdout",
        dataset_item_id="DS-0103",
        generator_seed=None,
        width=4000,
        height=2980,
        licence="CC0",
        permitted_use="CC0 (The Metropolitan Museum of Art open access)",
        source_path="data/raw/ukiyo-e/met-37129.jpg",
        repo_path="data/raw/ukiyo-e/met-37129.jpg",
        committed=False,
        note="verified by inspection: a landscape ukiyo-e print of a seated figure at a low desk in "
        "an interior, on a wide off-white paper margin. NOT a cresting wave - that phrase belongs to "
        "prompt P3-ukiyo, not to this image. It is style-matched to P3-ukiyo and subject-mismatched, "
        "and it is the conflict reference in C5",
    ),
    "R4": ReferenceSpec(
        id="R4",
        category="simple shape/layout transfer",
        origin="generated",
        dataset_item_id="",
        # Outside the dataset's 1000-based range, so this can never collide with
        # a training item while remaining byte-exact reproducible.
        generator_seed=9001,
        width=512,
        height=1536,
        licence="project-original",
        permitted_use="project-original, generated for Prototype 2 at seed 9001",
        source_path="",
        repo_path="data/references/R4-generated-seed9001.png",
        committed=True,
        note="unambiguous single subject and layout; the clean case for asking whether "
        "layout transfers independently of style",
    ),
    "R5": ReferenceSpec(
        id="R5",
        category="deliberately difficult",
        origin="dataset-holdout",
        dataset_item_id="DS-0088",
        generator_seed=None,
        width=1024,
        height=699,
        licence="public domain",
        permitted_use="public domain (Library of Congress, no known restrictions)",
        source_path="data/raw/retro-poster/loc-98519423.jpg",
        repo_path="data/raw/retro-poster/loc-98519423.jpg",
        committed=False,
        note="verified by inspection: a landscape WPA poster for \"Alison's House\", photographed in "
        "a dark frame, with large display lettering occupying most of the image. Landscape is the one "
        "orientation the deck format cannot accommodate, and framing plus typography are the two open "
        "M2 findings - all three stresses in one image",
    ),
}


# --- Condition table ---------------------------------------------------------


@dataclass(frozen=True)
class ConditionSpec:
    id: str
    reference_id: str
    prompt_id: str
    purpose: str


# Purposes describe what the reference images ACTUALLY depict, verified by
# opening all five before this table was written. The approved plan described
# C5's reference as "cresting wave"; that is the wording of prompt P3-ukiyo, not
# the content of R3, which is a figurative interior scene. Corrected here rather
# than carried forward - see docs/evidence/prototype-2/reference-kit.md.
CONDITIONS: dict[str, ConditionSpec] = {
    "C1": ConditionSpec(
        "C1", "R1", "P1-poster", "style-matched - reference and prompt are both retro-poster"
    ),
    "C2": ConditionSpec("C2", "R2", "P2-geo", "style-matched; already at the deck aspect"),
    "C3": ConditionSpec(
        "C3", "R3", "P3-ukiyo", "style-matched on style; subject differs (interior scene vs cresting wave)"
    ),
    "C4": ConditionSpec("C4", "R4", "P4-deck", "layout transfer onto a different subject"),
    "C5": ConditionSpec(
        "C5",
        "R3",
        "P2-geo",
        "CONFLICT - reference is a figurative ukiyo-e interior scene, prompt asks for "
        "minimal-geometric flat shapes",
    ),
    "C6": ConditionSpec("C6", "R5", "P1-poster", "difficult - frames, typography, wrong orientation"),
}

# The four style-matched / layout conditions carried through both sweeps.
SWEEP_CONDITIONS: tuple[str, ...] = ("C1", "C2", "C3", "C4")
# The two stress conditions.
STRESS_CONDITIONS: tuple[str, ...] = ("C5", "C6")
# Conditions exercised at the 512x1536 deck format.
DECK_CONDITIONS: tuple[str, ...] = ("C1", "C2", "C4")


# --- Process isolation -------------------------------------------------------


def process_config_key(method_key: str, width: int, height: int, memory_tier: int) -> str:
    """The exact process boundary: one fresh OS process per
    method x adapter variant x output resolution x memory tier.

    The adapter variant is already distinct in `method_key`
    (`ip-adapter` vs `ip-adapter-plus`), so it needs no separate component.

    Strength/scale levels SHARE a process within one such combination, because
    tensor geometry is unchanged across levels. That sharing carries three
    obligations, enforced in reporting rather than here:
      * `peak_vram_allocated_mb` is per-run and is the level-to-level figure;
      * `peak_vram_reserved_mb` / `peak_device_used_mb` are process-level
        high-water marks and are NEVER compared between levels sharing a process;
      * a clean-process spot check must pass before the shared-process
        comparison is accepted (see SPOT_CHECK_TOLERANCE_FRACTION).
    """
    return f"{method_key}@{width}x{height}@tier{memory_tier}"


# Pre-declared before any measurement, so it cannot be tuned to the result.
SPOT_CHECK_TOLERANCE_FRACTION = 0.02

# Physical VRAM of the audited RTX 4060 Laptop GPU. Windows WDDM spills silently
# into host RAM instead of raising a CUDA OOM (the DR-007 finding), so exceeding
# this is detected by comparison rather than caught as an exception.
PHYSICAL_VRAM_MIB = 8187.5

# The project's existing near-duplicate threshold, reused unchanged.
COPY_RISK_MAX_DHASH_DISTANCE = 6


def spot_check_within_tolerance(
    shared_process_mb: float,
    clean_process_mb: float,
    tolerance: float = SPOT_CHECK_TOLERANCE_FRACTION,
) -> bool:
    """True when a clean-process peak allocated figure agrees with its
    shared-process counterpart. On False the shared-process comparison is
    REJECTED and that method is re-run one level per process."""
    if clean_process_mb <= 0:
        raise ValueError("clean-process measurement must be positive")
    return abs(shared_process_mb - clean_process_mb) / clean_process_mb <= tolerance


def vram_overflow_suspected(
    peak_allocated_mb: float | str,
    peak_reserved_mb: float | str,
    limit_mib: float = PHYSICAL_VRAM_MIB,
) -> bool:
    """Flag a run whose allocator figures exceed physical VRAM. Such a run is
    never described as 'works on 8 GB'."""
    for value in (peak_allocated_mb, peak_reserved_mb):
        try:
            if float(value) > limit_mib:
                return True
        except (TypeError, ValueError):
            continue
    return False


# --- Result rows -------------------------------------------------------------

STATUS_OK = "ok"
STATUS_FAILED = "failed"
STATUS_TIMEOUT = "timeout"


@dataclass
class ReferenceResultRow:
    """One Phase-1 generation. Carries NO similarity indicator by construction."""

    exp_id: str
    condition_id: str
    method: str
    timestamp_utc: str
    model_repo_id: str
    model_revision_sha: str
    method_repo_id: str
    method_revision_sha: str
    # Empty for every method that loads no image encoder. An empty value in a
    # text-only or img2img row is positive evidence that no metric or adapter
    # encoder was resident in that measured process.
    image_encoder_revision_sha: str
    torch_version: str
    torch_cuda_version: str
    diffusers_version: str
    gpu_name: str
    dtype: str
    scheduler: str
    prompt_id: str
    prompt_sha256: str
    negative_prompt_sha256: str
    reference_id: str
    reference_sha256: str
    reference_preprocess: str
    reference_retained_area_fraction: float | str
    influence_level: str
    strength_param_name: str
    strength_value: float | str
    effective_steps: int | str
    seed: int
    width: int
    height: int
    steps: int
    guidance_scale: float
    memory_tier: int
    process_config_key: str
    safety_checker_present: bool
    safety_checker_enabled: bool
    vae_variant: str
    load_seconds: float | str
    generate_seconds: float | str
    peak_vram_allocated_mb: float | str
    # Process-level high-water marks. NEVER compared between levels that share a
    # process; see process_config_key.
    peak_vram_reserved_mb: float | str
    peak_device_used_mb: float | str
    peak_process_rss_mb: float | str
    output_sha256: str
    status: str
    error_type: str = ""
    error_message: str = ""
    output_path: str = ""


FIELDNAMES: list[str] = [f.name for f in fields(ReferenceResultRow)]


@dataclass
class SimilarityRow:
    """One Phase-2 offline indicator set, joined to a generation row on
    `output_sha256`. Written to a SEPARATE file: no similarity value ever enters
    a generation row, because the model computing it must never be resident in a
    process whose VRAM and latency describe a generation method."""

    output_sha256: str
    exp_id: str
    condition_id: str
    method: str
    influence_level: str
    strength_value: float | str
    seed: int
    width: int
    height: int
    reference_id: str
    # Perceptual-hash Hamming distance. Model-free. A COARSE NEAR-COPY FLAG ONLY -
    # not a measure of style, quality, or influence strength.
    dhash_distance_to_reference: int | str
    # Cosine similarity of CLIP image embeddings. Entangles subject, composition,
    # semantics, colour and style, so it is an OVERALL REFERENCE-IMAGE SIMILARITY
    # indicator, never a "style similarity" score. Style is judged by the human
    # `style_consistency` rubric dimension.
    overall_reference_similarity: float | str
    similarity_to_baseline: float | str
    baseline_output_sha256: str
    copy_risk_flag: bool
    evaluation_device: str
    evaluation_encoder_repo_id: str
    evaluation_encoder_revision_sha: str
    status: str = STATUS_OK
    error_type: str = ""
    error_message: str = ""


SIMILARITY_FIELDNAMES: list[str] = [f.name for f in fields(SimilarityRow)]


def build_output_filename(
    exp_id: str,
    method_slug: str,
    condition_id: str,
    reference_id: str,
    influence_level: str,
    strength_value: float | None,
    width: int,
    height: int,
    seed: int,
    memory_tier: int,
) -> str:
    """Every varying condition is visible in the filename, so a stray image can
    always be traced back to the exact run that produced it."""
    strength = "na" if strength_value is None else f"{strength_value:g}".replace(".", "p")
    return (
        f"{exp_id}__{method_slug}__{condition_id}__{reference_id}__{influence_level}"
        f"__s{strength}__{width}x{height}__seed{seed}__tier{memory_tier}.png"
    )


# --- IO ----------------------------------------------------------------------


def _write_rows(rows: list, path: Path, fieldnames: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    dicts = [asdict(r) if hasattr(r, "__dataclass_fields__") else r for r in rows]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in dicts:
            writer.writerow({name: row.get(name, "") for name in fieldnames})
    return path


def append_jsonl(row, path: str | Path) -> Path:
    """Append as each run finishes, so a crash mid-sweep loses nothing."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(asdict(row), sort_keys=True) + "\n")
    return path


def read_jsonl(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_csv(rows: list, path: str | Path) -> Path:
    return _write_rows(rows, Path(path), FIELDNAMES)


def write_similarity_csv(rows: list, path: str | Path) -> Path:
    return _write_rows(rows, Path(path), SIMILARITY_FIELDNAMES)


def join_similarity(
    generation_rows: list[dict], similarity_rows: list[dict]
) -> list[dict]:
    """Left-join Phase 2 onto Phase 1 on `output_sha256`, for reporting only.

    The joined view is built at read time and never written back into the
    generation file: the separation of the two files is the guarantee that no
    metric ever contaminated a measured generation process.
    """
    by_hash = {r["output_sha256"]: r for r in similarity_rows if r.get("output_sha256")}
    joined: list[dict] = []
    for row in generation_rows:
        merged = dict(row)
        match = by_hash.get(row.get("output_sha256", ""))
        for name in SIMILARITY_FIELDNAMES:
            if name in FIELDNAMES:
                continue
            merged[name] = match.get(name, "") if match else ""
        joined.append(merged)
    return joined


# --- Aggregation -------------------------------------------------------------


@dataclass
class ReferenceSummary:
    method: str
    width: int
    height: int
    influence_level: str
    strength_value: float | str
    memory_tier: int
    runs_ok: int
    runs_failed: int
    median_generate_seconds: float | None
    min_generate_seconds: float | None
    max_generate_seconds: float | None
    median_seconds_per_effective_step: float | None
    max_peak_vram_allocated_mb: float | None
    # Process-level high-water marks: comparable across methods (each method has
    # its own fresh process), NOT between levels inside one process.
    max_peak_vram_reserved_mb: float | None
    max_peak_device_used_mb: float | None
    max_peak_process_rss_mb: float | None
    load_seconds: float | None
    process_config_key: str
    vram_overflow_suspected: bool
    failures: list[str] = field(default_factory=list)


def _numeric(values: list) -> list[float]:
    out: list[float] = []
    for value in values:
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            continue
    return out


def _max_or_none(values: list) -> float | None:
    numeric = _numeric(values)
    return round(max(numeric), 2) if numeric else None


def summarize(rows: list[dict]) -> list[ReferenceSummary]:
    """Group by (method, resolution, influence level, tier). Median rather than
    mean, so a single stalled run cannot distort the headline figure."""
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (
            row["method"],
            int(row["width"]),
            int(row["height"]),
            row["influence_level"],
            str(row.get("strength_value", "")),
            int(row["memory_tier"]),
        )
        groups.setdefault(key, []).append(row)

    summaries: list[ReferenceSummary] = []
    for (method, width, height, level, strength, tier), group in sorted(groups.items()):
        ok = [r for r in group if r["status"] == STATUS_OK]
        failed = [r for r in group if r["status"] != STATUS_OK]
        durations = _numeric([r["generate_seconds"] for r in ok])

        per_step: list[float] = []
        for row in ok:
            seconds = _numeric([row["generate_seconds"]])
            steps = _numeric([row.get("effective_steps", "")])
            if seconds and steps and steps[0] > 0:
                per_step.append(seconds[0] / steps[0])

        summaries.append(
            ReferenceSummary(
                method=method,
                width=width,
                height=height,
                influence_level=level,
                strength_value=strength,
                memory_tier=tier,
                runs_ok=len(ok),
                runs_failed=len(failed),
                median_generate_seconds=round(statistics.median(durations), 3) if durations else None,
                min_generate_seconds=round(min(durations), 3) if durations else None,
                max_generate_seconds=round(max(durations), 3) if durations else None,
                median_seconds_per_effective_step=(
                    round(statistics.median(per_step), 4) if per_step else None
                ),
                max_peak_vram_allocated_mb=_max_or_none([r["peak_vram_allocated_mb"] for r in group]),
                max_peak_vram_reserved_mb=_max_or_none([r["peak_vram_reserved_mb"] for r in group]),
                max_peak_device_used_mb=_max_or_none([r["peak_device_used_mb"] for r in group]),
                max_peak_process_rss_mb=_max_or_none([r["peak_process_rss_mb"] for r in group]),
                load_seconds=_max_or_none([r["load_seconds"] for r in group]),
                process_config_key=group[0].get("process_config_key", ""),
                vram_overflow_suspected=any(
                    vram_overflow_suspected(r["peak_vram_allocated_mb"], r["peak_vram_reserved_mb"])
                    for r in group
                ),
                failures=sorted({f"{r['status']}: {r['error_type']}" for r in failed}),
            )
        )
    return summaries


def _fmt(value: float | None) -> str:
    return "not measured" if value is None else f"{value}"


def render_summary_markdown(summaries: list[ReferenceSummary], title: str) -> str:
    """Measurements only. Deliberately contains no quality verdict: qualitative
    scoring is the student's, supplied at the human-review gate. A pytest asserts
    the rendered text contains no verdict vocabulary."""
    lines = [
        f"# {title}",
        "",
        "Measured values only - no quality judgement, no method selection.",
        "",
        "Reading rules that travel with these numbers:",
        "",
        "- `peak alloc MiB` is **per run** and is the figure used to compare influence levels.",
        "- `peak reserved MiB` and `peak device MiB` are **process-level high-water marks**.",
        "  Influence levels share one OS process per (method, resolution, tier), so these two",
        "  columns must not be compared between levels. Comparison **between methods** remains",
        "  valid, because each method runs in its own fresh process.",
        "- img2img executes `int(steps x strength)` denoising steps, so a stronger reference is",
        "  also faster. `s/eff step` is therefore reported alongside wall-clock seconds.",
        "- img2img `strength` is **inverted**: a lower value means a stronger reference.",
        "",
        "| method | resolution | level | param | tier | ok | fail | median s | min s | max s | "
        "s/eff step | peak alloc MiB | peak reserved MiB | peak device MiB | peak RSS MiB | load s | process |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in summaries:
        lines.append(
            f"| {s.method} | {s.width}x{s.height} | {s.influence_level} | {s.strength_value} | "
            f"{s.memory_tier} | {s.runs_ok} | {s.runs_failed} | {_fmt(s.median_generate_seconds)} | "
            f"{_fmt(s.min_generate_seconds)} | {_fmt(s.max_generate_seconds)} | "
            f"{_fmt(s.median_seconds_per_effective_step)} | {_fmt(s.max_peak_vram_allocated_mb)} | "
            f"{_fmt(s.max_peak_vram_reserved_mb)} | {_fmt(s.max_peak_device_used_mb)} | "
            f"{_fmt(s.max_peak_process_rss_mb)} | {_fmt(s.load_seconds)} | `{s.process_config_key}` |"
        )

    overflow = [s for s in summaries if s.vram_overflow_suspected]
    if overflow:
        lines += [
            "",
            "## VRAM overflow suspected",
            "",
            f"Windows WDDM spills into host RAM without raising a CUDA OOM, so these rows exceeded the "
            f"{PHYSICAL_VRAM_MIB} MiB of physical VRAM without failing. They are not described as running on 8 GB.",
            "",
        ]
        for s in overflow:
            lines.append(
                f"- {s.method} {s.width}x{s.height} {s.influence_level}: "
                f"alloc {_fmt(s.max_peak_vram_allocated_mb)} MiB / reserved {_fmt(s.max_peak_vram_reserved_mb)} MiB"
            )

    failures = [(s, f) for s in summaries for f in s.failures]
    if failures:
        lines += ["", "## Failures", ""]
        for s, failure in failures:
            lines.append(
                f"- {s.method} ({s.width}x{s.height}, {s.influence_level}, tier {s.memory_tier}): {failure}"
            )
    lines.append("")
    return "\n".join(lines)


# --- Monotonicity ------------------------------------------------------------

# Ordered weakest to strongest reference influence, independent of each method's
# native parameter direction.
MONOTONICITY_LEVEL_ORDER: tuple[str, ...] = ("none", "weak", "medium", "strong")


def is_monotone_increasing(values: list[float]) -> bool:
    """Non-strict: equal consecutive values do not break monotonicity."""
    return all(b >= a for a, b in zip(values, values[1:]))


def monotonicity_by_condition(
    similarity_rows: list[dict],
    method_key: str,
    level_order: tuple[str, ...] = MONOTONICITY_LEVEL_ORDER,
) -> dict[str, bool | None]:
    """Per condition: does the MEDIAN overall reference-image similarity increase
    as the shared influence level rises?

    Returns None for a condition that does not have at least two ordered levels
    with usable values - an absent answer, never a fabricated one.
    """
    by_condition: dict[str, dict[str, list[float]]] = {}
    for row in similarity_rows:
        if row.get("method") != method_key:
            continue
        value = _numeric([row.get("overall_reference_similarity", "")])
        if not value:
            continue
        by_condition.setdefault(row["condition_id"], {}).setdefault(row["influence_level"], []).append(
            value[0]
        )

    result: dict[str, bool | None] = {}
    for condition, levels in sorted(by_condition.items()):
        ordered = [
            statistics.median(levels[level]) for level in level_order if levels.get(level)
        ]
        result[condition] = is_monotone_increasing(ordered) if len(ordered) >= 2 else None
    return result
