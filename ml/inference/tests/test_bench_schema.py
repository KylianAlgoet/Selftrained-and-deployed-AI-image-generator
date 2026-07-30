"""Tests for the benchmark data model. CPU-only - no GPU or model download.

`ml.inference.bench_schema` deliberately imports neither torch nor diffusers so
these run anywhere, including on a machine that cannot execute the benchmark.
"""

import pytest

from ml.inference.bench_schema import (
    FIELDNAMES,
    MAX_COMPARABLE_TIER,
    MEMORY_TIERS,
    MODELS,
    STATUS_FAILED,
    STATUS_OK,
    STATUS_TIMEOUT,
    ResultRow,
    append_jsonl,
    build_output_filename,
    next_tier,
    read_jsonl,
    render_summary_markdown,
    summarize,
    write_csv,
    write_jsonl,
)


def make_row(**overrides) -> ResultRow:
    defaults = dict(
        exp_id="EXP-002",
        track="A",
        timestamp_utc="2026-07-30T00:00:00+00:00",
        model_repo_id="org/model",
        model_revision_sha="a" * 40,
        torch_version="2.13.0+cu126",
        torch_cuda_version="12.6",
        diffusers_version="0.39.0",
        gpu_name="NVIDIA GeForce RTX 4060 Laptop GPU",
        dtype="float16",
        scheduler="DPMSolverMultistepScheduler",
        prompt_id="P1-poster",
        prompt_sha256="b" * 64,
        negative_prompt_sha256="c" * 64,
        seed=42,
        width=512,
        height=512,
        steps=30,
        guidance_scale=7.5,
        memory_tier=0,
        safety_checker_present=True,
        safety_checker_enabled=False,
        vae_variant="pipeline default",
        load_seconds=12.5,
        generate_seconds=4.0,
        peak_vram_allocated_mb=2500.0,
        peak_vram_reserved_mb=2800.0,
        peak_device_used_mb=3400.0,
        peak_process_rss_mb=5000.0,
        output_sha256="d" * 64,
        status=STATUS_OK,
    )
    defaults.update(overrides)
    return ResultRow(**defaults)


# --- candidate registry ------------------------------------------------------


def test_three_candidates_registered_with_licences():
    assert set(MODELS) == {"sd15", "sd21base", "sdxl"}
    for spec in MODELS.values():
        assert spec.licence
        assert spec.repo_id.count("/") == 1


def test_sdxl_track_b_is_native_1024_and_512_natives_coincide_with_track_a():
    """The whole point of Track B: SDXL is not judged at a size it was not built for."""
    assert MODELS["sdxl"].track_b_resolution == (1024, 1024)
    assert MODELS["sd15"].track_b_resolution == (512, 512)
    assert MODELS["sd21base"].track_b_resolution == (512, 512)


def test_sd15_repo_is_the_maintained_mirror_not_the_withdrawn_runwayml_repo():
    assert MODELS["sd15"].repo_id == "stable-diffusion-v1-5/stable-diffusion-v1-5"


# --- memory tiers ------------------------------------------------------------


def test_tier_escalation_stops_at_the_last_comparable_tier():
    assert next_tier(0) == 1
    assert next_tier(3) == 4
    assert next_tier(MAX_COMPARABLE_TIER) is None


def test_tier_5_exists_but_is_flagged_as_breaking_comparability():
    assert 5 in MEMORY_TIERS
    assert "BREAKS COMPARABILITY" in MEMORY_TIERS[5]
    assert MAX_COMPARABLE_TIER < 5


# --- output naming -----------------------------------------------------------


def test_output_filename_encodes_every_varying_condition():
    name = build_output_filename("EXP-002", "sd15", "A", "P1-poster", 512, 768, 1337, 30, 7.5, 2)
    assert name == "EXP-002__sd15__A__P1-poster__512x768__seed1337__st30__cfg7p5__tier2.png"


def test_output_filenames_differ_by_tier_and_track():
    common = ("EXP-002", "sd15", "A", "P1-poster", 512, 512, 42, 30, 7.5)
    assert build_output_filename(*common, 0) != build_output_filename(*common, 3)
    a = build_output_filename("EXP-002", "sd15", "A", "P1-poster", 512, 512, 42, 30, 7.5, 0)
    b = build_output_filename("EXP-002", "sd15", "B", "P1-poster", 512, 512, 42, 30, 7.5, 0)
    assert a != b


# --- serialisation -----------------------------------------------------------


def test_jsonl_round_trip(tmp_path):
    rows = [make_row(), make_row(seed=1337)]
    path = write_jsonl(rows, tmp_path / "results.jsonl")
    loaded = read_jsonl(path)
    assert len(loaded) == 2
    assert loaded[0]["seed"] == 42
    assert loaded[1]["seed"] == 1337


def test_append_jsonl_survives_incremental_writes(tmp_path):
    """Rows are appended as runs finish so a mid-benchmark crash loses nothing."""
    path = tmp_path / "results.jsonl"
    append_jsonl(make_row(prompt_id="P1-poster"), path)
    append_jsonl(make_row(prompt_id="P2-geo"), path)
    assert [r["prompt_id"] for r in read_jsonl(path)] == ["P1-poster", "P2-geo"]


def test_csv_has_every_schema_column(tmp_path):
    path = write_csv([make_row()], tmp_path / "results.csv")
    header = path.read_text(encoding="utf-8").splitlines()[0]
    assert header.split(",") == FIELDNAMES
    for required in ("track", "memory_tier", "model_revision_sha", "output_sha256",
                     "safety_checker_present", "safety_checker_enabled", "peak_device_used_mb"):
        assert required in FIELDNAMES


def test_csv_accepts_plain_dicts_too(tmp_path):
    path = write_csv(read_jsonl(write_jsonl([make_row()], tmp_path / "r.jsonl")), tmp_path / "r.csv")
    assert "EXP-002" in path.read_text(encoding="utf-8")


# --- aggregation -------------------------------------------------------------


def test_summarize_uses_median_and_reports_range():
    rows = [
        vars(make_row(seed=1, generate_seconds=4.0)),
        vars(make_row(seed=2, generate_seconds=5.0)),
        vars(make_row(seed=3, generate_seconds=99.0)),
    ]
    summary = summarize(rows)[0]
    assert summary.runs_ok == 3
    assert summary.median_generate_seconds == 5.0  # not dragged by the outlier
    assert summary.min_generate_seconds == 4.0
    assert summary.max_generate_seconds == 99.0


def test_summarize_groups_by_track_resolution_and_tier():
    rows = [
        vars(make_row(track="A", width=512, height=512, memory_tier=0)),
        vars(make_row(track="B", width=1024, height=1024, memory_tier=1)),
    ]
    summaries = summarize(rows)
    assert len(summaries) == 2
    assert {(s.track, s.memory_tier) for s in summaries} == {("A", 0), ("B", 1)}


def test_failures_are_counted_and_never_dropped():
    rows = [
        vars(make_row(seed=1)),
        vars(make_row(seed=2, status=STATUS_FAILED, error_type="OutOfMemoryError",
                      generate_seconds="not measured")),
        vars(make_row(seed=3, status=STATUS_TIMEOUT, error_type="GenerationTimeout",
                      generate_seconds="not measured")),
    ]
    summary = summarize(rows)[0]
    assert summary.runs_ok == 1
    assert summary.runs_failed == 2
    assert any("OutOfMemoryError" in f for f in summary.failures)
    assert any("GenerationTimeout" in f for f in summary.failures)


def test_unmeasured_values_are_reported_honestly_not_as_zero():
    rows = [vars(make_row(status=STATUS_FAILED, generate_seconds="not measured",
                          peak_vram_allocated_mb="not measured"))]
    summary = summarize(rows)[0]
    assert summary.median_generate_seconds is None
    markdown = render_summary_markdown(summarize(rows), "t")
    assert "not measured" in markdown
    assert "| 0 |" not in markdown.split("## Failures")[0].split("\n")[-2]


def test_summary_markdown_contains_no_quality_verdict():
    """Qualitative scoring belongs to the student at the human-review gate."""
    markdown = render_summary_markdown(summarize([vars(make_row())]), "EXP-002 measurements")
    lowered = markdown.lower()
    for forbidden in ("winner", "best", "recommend", "better", "worse", "quality score"):
        assert forbidden not in lowered
    assert "no quality judgement" in lowered


def test_summarize_empty_input():
    assert summarize([]) == []
