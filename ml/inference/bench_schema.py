"""Pure data model for the Prototype 1 base-model benchmark.

Deliberately free of torch/diffusers imports so the schema, filename, tier, and
aggregation logic are unit-testable on any machine without a GPU.

Design intent worth preserving: `track`, `memory_tier`, `safety_checker_present`,
`safety_checker_enabled`, `vae_variant`, and `model_revision_sha` are all
first-class fields. A model that only ran at a deeper memory tier, or without an
auxiliary safety checker, must never be compared at face value against one that
did not - so the conditions travel with every single measurement.
"""

import csv
import json
import statistics
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

# --- Candidate registry ------------------------------------------------------


@dataclass(frozen=True)
class ModelSpec:
    key: str
    repo_id: str
    slug: str
    track_b_resolution: tuple[int, int]
    licence: str
    note: str
    # Supplementary out-of-distribution probes, reported separately and never
    # folded into a track's headline numbers.
    probe_resolutions: tuple[tuple[int, int], ...] = ()


MODELS: dict[str, ModelSpec] = {
    "sd15": ModelSpec(
        key="sd15",
        # The original `runwayml/stable-diffusion-v1-5` repo was withdrawn from
        # the Hub; this is the maintained mirror. Availability is verified at
        # run time and the resolved commit SHA is recorded per run.
        repo_id="stable-diffusion-v1-5/stable-diffusion-v1-5",
        slug="sd15",
        track_b_resolution=(512, 512),
        licence="CreativeML OpenRAIL-M",
        note="conservative anchor; native 512; richest LoRA/IP-Adapter ecosystem",
        probe_resolutions=((512, 768),),
    ),
    "sd21base": ModelSpec(
        key="sd21base",
        repo_id="stabilityai/stable-diffusion-2-1-base",
        slug="sd21-base",
        # SD 2.1 *base* is a 512 model, so Track B coincides with Track A here.
        # That is a legitimate finding about the candidate, not a gap.
        track_b_resolution=(512, 512),
        licence="CreativeML OpenRAIL++-M",
        note="mid-point; native 512; OpenCLIP-H text encoder",
        probe_resolutions=((768, 768),),
    ),
    "sdxl": ModelSpec(
        key="sdxl",
        repo_id="stabilityai/stable-diffusion-xl-base-1.0",
        slug="sdxl-base",
        track_b_resolution=(1024, 1024),
        licence="CreativeML OpenRAIL++-M",
        note="quality/VRAM stress test; native 1024; two text encoders",
    ),
}


# --- Memory tiers ------------------------------------------------------------

# A deeper tier is entered ONLY after a recorded failure. Tier 5 breaks
# comparability and is therefore reported as a separate finding.
MEMORY_TIERS: dict[int, str] = {
    0: "fp16 baseline, SDPA attention, no offload",
    1: "attention slicing",
    2: "attention slicing + VAE slicing/tiling",
    3: "model CPU offload",
    4: "sequential CPU offload",
    5: "reduced resolution or steps (BREAKS COMPARABILITY - separate finding)",
}

MAX_COMPARABLE_TIER = 4


def next_tier(current: int) -> int | None:
    """Escalation path. Returns None when no comparable tier remains."""
    if current >= MAX_COMPARABLE_TIER:
        return None
    return current + 1


# --- Result rows -------------------------------------------------------------

STATUS_OK = "ok"
STATUS_FAILED = "failed"
STATUS_TIMEOUT = "timeout"


@dataclass
class ResultRow:
    exp_id: str
    track: str
    timestamp_utc: str
    model_repo_id: str
    model_revision_sha: str
    torch_version: str
    torch_cuda_version: str
    diffusers_version: str
    gpu_name: str
    dtype: str
    scheduler: str
    prompt_id: str
    prompt_sha256: str
    negative_prompt_sha256: str
    seed: int
    width: int
    height: int
    steps: int
    guidance_scale: float
    memory_tier: int
    safety_checker_present: bool
    safety_checker_enabled: bool
    vae_variant: str
    load_seconds: float | str
    generate_seconds: float | str
    peak_vram_allocated_mb: float | str
    peak_vram_reserved_mb: float | str
    # Device-level peak (total - free via torch.cuda.mem_get_info), i.e. the same
    # quantity nvidia-smi reports as memory.used. Sampled in-process rather than
    # by spawning nvidia-smi repeatedly: identical figure, far lower overhead. A
    # full nvidia-smi snapshot is kept in the EXP-001 environment evidence.
    peak_device_used_mb: float | str
    peak_process_rss_mb: float | str
    output_sha256: str
    status: str
    error_type: str = ""
    error_message: str = ""
    output_path: str = ""


FIELDNAMES: list[str] = [f.name for f in fields(ResultRow)]


def build_output_filename(
    exp_id: str,
    model_slug: str,
    track: str,
    prompt_id: str,
    width: int,
    height: int,
    seed: int,
    steps: int,
    guidance_scale: float,
    memory_tier: int,
) -> str:
    """Every varying condition is visible in the filename, so a stray image can
    always be traced back to the exact run that produced it."""
    cfg = f"{guidance_scale:g}".replace(".", "p")
    return (
        f"{exp_id}__{model_slug}__{track}__{prompt_id}__{width}x{height}"
        f"__seed{seed}__st{steps}__cfg{cfg}__tier{memory_tier}.png"
    )


def write_jsonl(rows: list[ResultRow], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        for row in rows:
            fh.write(json.dumps(asdict(row), sort_keys=True) + "\n")
    return path


def append_jsonl(row: ResultRow, path: str | Path) -> Path:
    """Append as each run finishes, so a crash mid-benchmark loses nothing."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(asdict(row), sort_keys=True) + "\n")
    return path


def read_jsonl(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_csv(rows: list[dict] | list[ResultRow], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dicts = [asdict(r) if isinstance(r, ResultRow) else r for r in rows]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in dicts:
            writer.writerow({name: row.get(name, "") for name in FIELDNAMES})
    return path


# --- Aggregation -------------------------------------------------------------


@dataclass
class Summary:
    model_repo_id: str
    track: str
    width: int
    height: int
    memory_tier: int
    runs_ok: int
    runs_failed: int
    median_generate_seconds: float | None
    min_generate_seconds: float | None
    max_generate_seconds: float | None
    max_peak_vram_allocated_mb: float | None
    max_peak_vram_reserved_mb: float | None
    max_peak_device_used_mb: float | None
    max_peak_process_rss_mb: float | None
    load_seconds: float | None
    failures: list[str] = field(default_factory=list)


def _numeric(values: list) -> list[float]:
    out = []
    for value in values:
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            continue
    return out


def summarize(rows: list[dict]) -> list[Summary]:
    """Group by (model, track, resolution, tier). Median is reported rather than
    mean because a single stalled run should not distort the headline figure."""
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (
            row["model_repo_id"],
            row["track"],
            int(row["width"]),
            int(row["height"]),
            int(row["memory_tier"]),
        )
        groups.setdefault(key, []).append(row)

    summaries: list[Summary] = []
    for (repo_id, track, width, height, tier), group in sorted(groups.items()):
        ok = [r for r in group if r["status"] == STATUS_OK]
        failed = [r for r in group if r["status"] != STATUS_OK]
        durations = _numeric([r["generate_seconds"] for r in ok])
        summaries.append(
            Summary(
                model_repo_id=repo_id,
                track=track,
                width=width,
                height=height,
                memory_tier=tier,
                runs_ok=len(ok),
                runs_failed=len(failed),
                median_generate_seconds=round(statistics.median(durations), 3) if durations else None,
                min_generate_seconds=round(min(durations), 3) if durations else None,
                max_generate_seconds=round(max(durations), 3) if durations else None,
                max_peak_vram_allocated_mb=_max_or_none([r["peak_vram_allocated_mb"] for r in group]),
                max_peak_vram_reserved_mb=_max_or_none([r["peak_vram_reserved_mb"] for r in group]),
                max_peak_device_used_mb=_max_or_none([r["peak_device_used_mb"] for r in group]),
                max_peak_process_rss_mb=_max_or_none([r["peak_process_rss_mb"] for r in group]),
                load_seconds=_max_or_none([r["load_seconds"] for r in group]),
                failures=sorted({f"{r['status']}: {r['error_type']}" for r in failed}),
            )
        )
    return summaries


def _max_or_none(values: list) -> float | None:
    numeric = _numeric(values)
    return round(max(numeric), 2) if numeric else None


def render_summary_markdown(summaries: list[Summary], title: str) -> str:
    """Measurements only. Deliberately contains no quality verdict: qualitative
    scoring is the student's, supplied at the human-review gate."""
    lines = [
        f"# {title}",
        "",
        "Measured values only - no quality judgement. Peak VRAM is reported three ways:",
        "torch allocator (`allocated`/`reserved`) plus device-level usage, which",
        "additionally includes the CUDA context the allocator cannot see.",
        "",
        "| model | track | resolution | tier | ok | fail | median s | min s | max s | "
        "peak alloc MiB | peak reserved MiB | peak device MiB | peak RSS MiB | load s |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in summaries:
        lines.append(
            f"| {s.model_repo_id} | {s.track} | {s.width}x{s.height} | {s.memory_tier} | "
            f"{s.runs_ok} | {s.runs_failed} | {_fmt(s.median_generate_seconds)} | "
            f"{_fmt(s.min_generate_seconds)} | {_fmt(s.max_generate_seconds)} | "
            f"{_fmt(s.max_peak_vram_allocated_mb)} | {_fmt(s.max_peak_vram_reserved_mb)} | "
            f"{_fmt(s.max_peak_device_used_mb)} | {_fmt(s.max_peak_process_rss_mb)} | "
            f"{_fmt(s.load_seconds)} |"
        )
    failures = [(s, f) for s in summaries for f in s.failures]
    if failures:
        lines += ["", "## Failures", ""]
        for s, failure in failures:
            lines.append(f"- {s.model_repo_id} ({s.track}, {s.width}x{s.height}, tier {s.memory_tier}): {failure}")
    lines.append("")
    return "\n".join(lines)


def _fmt(value: float | None) -> str:
    return "not measured" if value is None else f"{value}"
