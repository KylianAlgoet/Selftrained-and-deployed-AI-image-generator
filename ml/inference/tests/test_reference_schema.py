"""Unit tests for the Prototype 2 reference-conditioning data model.

CPU-only and import-light: `reference_schema` deliberately imports neither torch
nor diffusers, so every rule below is testable on any machine.
"""

import ast
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from ml.dataset.hashing import NEAR_DUPLICATE_MAX_DISTANCE, sha256_file
from ml.dataset.manifest import load_manifest
from ml.evaluation import prompt_kit
from ml.inference import reference_schema as rs

REPO = Path(__file__).resolve().parents[3]


def _row(**overrides) -> rs.ReferenceResultRow:
    defaults = dict(
        exp_id="EXP-009",
        condition_id="C1",
        method="ip-adapter",
        timestamp_utc="2026-07-31T10:00:00+00:00",
        model_repo_id="stable-diffusion-v1-5/stable-diffusion-v1-5",
        model_revision_sha="451f4fe16113bff5a5d2269ed5ad43b0592e9a14",
        method_repo_id=rs.IP_ADAPTER_REPO,
        method_revision_sha=rs.IP_ADAPTER_REVISION,
        image_encoder_revision_sha=rs.IP_ADAPTER_REVISION,
        torch_version="2.13.0+cu126",
        torch_cuda_version="12.6",
        diffusers_version="0.39.0",
        gpu_name="NVIDIA GeForce RTX 4060 Laptop GPU",
        dtype="float16",
        scheduler="DPMSolverMultistepScheduler",
        prompt_id="P1-poster",
        prompt_sha256="a" * 64,
        negative_prompt_sha256="b" * 64,
        reference_id="R1",
        reference_sha256="c" * 64,
        reference_preprocess="CLIP processor resize + centre-crop 224",
        reference_retained_area_fraction=1.0,
        influence_level="medium",
        strength_param_name="scale",
        strength_value=0.55,
        effective_steps=30,
        seed=42,
        width=512,
        height=512,
        steps=30,
        guidance_scale=7.5,
        memory_tier=0,
        process_config_key="ip-adapter@512x512@tier0",
        safety_checker_present=True,
        safety_checker_enabled=False,
        vae_variant="pipeline default",
        load_seconds=9.1,
        generate_seconds=5.0,
        peak_vram_allocated_mb=3900.0,
        peak_vram_reserved_mb=4200.0,
        peak_device_used_mb=5600.0,
        peak_process_rss_mb=2400.0,
        output_sha256="d" * 64,
        status=rs.STATUS_OK,
    )
    defaults.update(overrides)
    return rs.ReferenceResultRow(**defaults)


# --- schema round-trip -------------------------------------------------------


def test_generation_row_round_trips_through_jsonl_and_csv(tmp_path):
    rows = [_row(), _row(seed=1337, output_sha256="e" * 64)]
    jsonl = tmp_path / "results.jsonl"
    for row in rows:
        rs.append_jsonl(row, jsonl)

    read_back = rs.read_jsonl(jsonl)
    assert read_back == [asdict(row) for row in rows]

    csv_path = rs.write_csv(read_back, tmp_path / "results.csv")
    header = csv_path.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert header == rs.FIELDNAMES


def test_generation_row_carries_no_similarity_field():
    """Phase 1 must not be able to record a Phase-2 indicator, even by accident:
    that is what keeps a metric model out of a measured generation process."""
    phase2_only = set(rs.SIMILARITY_FIELDNAMES) - set(rs.FIELDNAMES)
    assert "overall_reference_similarity" in phase2_only
    assert "dhash_distance_to_reference" in phase2_only
    for name in ("overall_reference_similarity", "dhash_distance_to_reference", "similarity_to_baseline"):
        assert name not in rs.FIELDNAMES


# --- influence-level mapping -------------------------------------------------


def test_named_levels_resolve_to_the_documented_values():
    assert rs.influence_value("img2img", "medium") == 0.65
    assert rs.influence_value("ip-adapter", "medium") == 0.55
    assert rs.influence_value("ip-adapter", "none") == 0.0


def test_img2img_has_no_none_level_because_that_is_the_text_only_arm():
    with pytest.raises(KeyError):
        rs.influence_value("img2img", "none")


def test_img2img_strength_inversion_is_not_silently_flipped():
    """Regression guard for the trap in the plan: for img2img the SMALLEST
    strength is the STRONGEST reference influence. A chart read against the wrong
    direction would invert the entire RQ6 conclusion."""
    assert rs.METHODS["img2img"].strength_inverted is True
    assert rs.METHODS["ip-adapter"].strength_inverted is False

    weak = rs.influence_value("img2img", "weak")
    strong = rs.influence_value("img2img", "strong")
    assert strong < weak, "img2img: strong influence must map to the LOWER strength"

    assert rs.level_for_value("img2img", 0.30) == "strong"
    assert rs.level_for_value("img2img", 0.90) == "weak"

    # IP-Adapter runs the other way and must stay that way.
    assert rs.influence_value("ip-adapter", "strong") > rs.influence_value("ip-adapter", "weak")
    assert rs.level_for_value("ip-adapter", 1.00) == "strong"
    assert rs.level_for_value("ip-adapter", 0.20) == "weak"


def test_sweep_values_span_each_method_native_range():
    assert rs.SWEEP_VALUES["img2img"] == (0.90, 0.75, 0.60, 0.45, 0.30)
    assert rs.SWEEP_VALUES["ip-adapter"] == (0.20, 0.40, 0.60, 0.80, 1.00)
    for method_key, values in rs.SWEEP_VALUES.items():
        assert len(set(values)) == 5, f"{method_key} sweep must have five distinct levels"


# --- arithmetic --------------------------------------------------------------


def test_effective_steps_follows_diffusers_img2img_arithmetic():
    """Diffusers runs int(steps * strength) denoising steps, so a stronger
    reference is also faster - the latency trap the summary must expose."""
    assert rs.effective_steps("img2img", 30, 0.90) == 27
    assert rs.effective_steps("img2img", 30, 0.30) == 9
    assert rs.effective_steps("img2img", 30, 0.65) == 19
    # Every other method runs the full schedule.
    assert rs.effective_steps("ip-adapter", 30, 0.55) == 30
    assert rs.effective_steps("text-only", 30, None) == 30


def test_effective_steps_refuses_to_guess_a_missing_img2img_strength():
    with pytest.raises(ValueError):
        rs.effective_steps("img2img", 30, None)


def test_retained_area_matches_the_planned_deck_format_arithmetic():
    """Values quoted in the M4 plan, recomputed from the manifest dimensions."""
    assert rs.retained_area_fraction(512, 1536, 512, 1536) == pytest.approx(1.0)
    assert rs.retained_area_fraction(690, 1024, 512, 1536) == pytest.approx(0.4947, abs=5e-4)
    assert rs.retained_area_fraction(4000, 2980, 512, 1536) == pytest.approx(0.2484, abs=5e-4)
    assert rs.retained_area_fraction(1024, 699, 512, 1536) == pytest.approx(0.2275, abs=5e-4)
    # Symmetric: cropping a square target from a square source keeps everything.
    assert rs.retained_area_fraction(512, 512, 512, 512) == pytest.approx(1.0)


def test_retained_area_rejects_impossible_dimensions():
    with pytest.raises(ValueError):
        rs.retained_area_fraction(0, 100, 512, 512)


# --- process isolation -------------------------------------------------------


def test_process_config_key_encodes_exactly_the_declared_boundary():
    """method x adapter variant x resolution x tier. Influence level and seed are
    deliberately absent: those share a process."""
    assert rs.process_config_key("img2img", 512, 512, 0) == "img2img@512x512@tier0"
    assert rs.process_config_key("ip-adapter", 512, 1536, 0) == "ip-adapter@512x1536@tier0"

    base = rs.process_config_key("ip-adapter", 512, 512, 0)
    assert rs.process_config_key("ip-adapter-plus", 512, 512, 0) != base  # variant
    assert rs.process_config_key("ip-adapter", 512, 1536, 0) != base  # resolution
    assert rs.process_config_key("ip-adapter", 512, 512, 1) != base  # tier


def test_spot_check_tolerance_is_two_percent_and_pre_declared():
    assert rs.SPOT_CHECK_TOLERANCE_FRACTION == 0.02
    assert rs.spot_check_within_tolerance(1000.0, 1000.0)
    assert rs.spot_check_within_tolerance(1019.0, 1000.0)
    assert not rs.spot_check_within_tolerance(1021.0, 1000.0)
    assert not rs.spot_check_within_tolerance(978.0, 1000.0)


def test_vram_overflow_is_detected_by_comparison_not_by_exception():
    """Windows WDDM spills into host RAM without raising a CUDA OOM (DR-007), so
    tier escalation cannot fire. Detection has to be explicit."""
    assert rs.vram_overflow_suspected(10738.08, 14510.0)
    assert not rs.vram_overflow_suspected(3892.01, 4200.0)
    assert not rs.vram_overflow_suspected("not measured", "not measured")


# --- registry integrity ------------------------------------------------------


def test_every_reference_resolves_to_a_holdout_manifest_item_or_a_generator_seed():
    manifest = {row["id"]: row for row in load_manifest(REPO / "data" / "manifests" / "dataset-v1.csv")}
    for spec in rs.REFERENCES.values():
        if spec.origin == "generated":
            assert spec.generator_seed is not None
            assert spec.dataset_item_id == ""
            continue
        item = manifest.get(spec.dataset_item_id)
        assert item is not None, f"{spec.id}: {spec.dataset_item_id} is not in the manifest"
        assert item["split"] == "holdout", f"{spec.id}: must come from the holdout split"
        assert (int(item["width"]), int(item["height"])) == (spec.width, spec.height)
        assert item["licence"] == spec.licence


def test_reference_files_on_disk_match_their_manifest_hashes():
    manifest = {row["id"]: row for row in load_manifest(REPO / "data" / "manifests" / "dataset-v1.csv")}
    for spec in rs.REFERENCES.values():
        path = REPO / spec.repo_path
        if not path.exists():
            pytest.skip(f"{spec.id} not materialised; run scripts/build_reference_kit.py")
        if spec.origin == "generated":
            continue
        assert sha256_file(path) == manifest[spec.dataset_item_id]["sha256"], (
            f"{spec.id}: file on disk does not match the manifest SHA-256"
        )


def test_generated_reference_is_byte_exact_from_its_seed(tmp_path):
    """R4's provenance is 'generator + seed', so that claim is verified rather
    than asserted."""
    from ml.dataset.generate_geometric import generate_geometric

    spec = rs.REFERENCES["R4"]
    committed = REPO / spec.repo_path
    if not committed.exists():
        pytest.skip("R4 not materialised; run scripts/build_reference_kit.py")
    regenerated = tmp_path / "R4.png"
    generate_geometric(spec.generator_seed, regenerated)
    assert sha256_file(regenerated) == sha256_file(committed)


def test_only_project_original_references_are_marked_committed():
    for spec in rs.REFERENCES.values():
        if spec.committed:
            assert spec.licence == "project-original", (
                f"{spec.id}: only project-original references may be committed"
            )
            assert spec.repo_path.startswith("data/references/")
        else:
            assert spec.repo_path.startswith("data/raw/")


def test_conditions_reference_real_references_and_frozen_prompts():
    prompt_ids = {p.id for p in prompt_kit.PROMPTS}
    for condition in rs.CONDITIONS.values():
        assert condition.reference_id in rs.REFERENCES
        assert condition.prompt_id in prompt_ids


def test_condition_c5_is_a_genuine_conflict():
    """C5 must pair a reference with a prompt of a DIFFERENT style, otherwise the
    prompt-vs-reference trade-off is never forced open."""
    c5 = rs.CONDITIONS["C5"]
    reference_style = rs.REFERENCES[c5.reference_id].category
    assert reference_style == "ukiyo-e"
    assert c5.prompt_id == "P2-geo"
    assert "CONFLICT" in c5.purpose


def test_condition_purposes_do_not_repeat_the_corrected_cresting_wave_label():
    """Regression guard for a plan label that did not survive inspection of the
    actual image: R3 is a figurative interior scene, not a cresting wave. That
    phrase belongs to prompt P3-ukiyo only."""
    for condition in rs.CONDITIONS.values():
        assert "reference says cresting wave" not in condition.purpose
    assert "NOT a cresting wave" in rs.REFERENCES["R3"].note


# --- similarity join ---------------------------------------------------------


def test_similarity_joins_onto_generation_rows_by_output_hash():
    generation = [asdict(_row()), asdict(_row(seed=1337, output_sha256="e" * 64))]
    similarity = [
        {
            "output_sha256": "d" * 64,
            "overall_reference_similarity": 0.71,
            "dhash_distance_to_reference": 18,
            "similarity_to_baseline": 0.62,
        }
    ]
    joined = rs.join_similarity(generation, similarity)
    assert joined[0]["overall_reference_similarity"] == 0.71
    assert joined[0]["dhash_distance_to_reference"] == 18
    # An unmatched generation row gets empty indicators, never an invented value.
    assert joined[1]["overall_reference_similarity"] == ""


def test_copy_risk_threshold_reuses_the_existing_project_constant():
    assert rs.COPY_RISK_MAX_DHASH_DISTANCE == NEAR_DUPLICATE_MAX_DISTANCE == 6


# --- monotonicity ------------------------------------------------------------


def test_is_monotone_increasing_accepts_plateaus_and_rejects_dips():
    assert rs.is_monotone_increasing([0.1, 0.2, 0.3])
    assert rs.is_monotone_increasing([0.1, 0.2, 0.2])
    assert not rs.is_monotone_increasing([0.1, 0.3, 0.2])


def test_monotonicity_uses_medians_and_reports_none_when_it_cannot_answer():
    rows = [
        {"method": "ip-adapter", "condition_id": "C1", "influence_level": "weak",
         "overall_reference_similarity": 0.40},
        {"method": "ip-adapter", "condition_id": "C1", "influence_level": "medium",
         "overall_reference_similarity": 0.55},
        {"method": "ip-adapter", "condition_id": "C1", "influence_level": "strong",
         "overall_reference_similarity": 0.70},
        {"method": "ip-adapter", "condition_id": "C2", "influence_level": "weak",
         "overall_reference_similarity": 0.60},
        {"method": "ip-adapter", "condition_id": "C2", "influence_level": "strong",
         "overall_reference_similarity": 0.30},
        # Only one usable level: unanswerable, so None rather than a guess.
        {"method": "ip-adapter", "condition_id": "C3", "influence_level": "medium",
         "overall_reference_similarity": 0.50},
        # Different method: must not leak into these counts.
        {"method": "img2img", "condition_id": "C1", "influence_level": "strong",
         "overall_reference_similarity": 0.99},
    ]
    result = rs.monotonicity_by_condition(rows, "ip-adapter")
    assert result == {"C1": True, "C2": False, "C3": None}


# --- unscored summary --------------------------------------------------------

# Vocabulary that would turn a measurement table into a quality verdict. The
# human-review gate exists precisely so these words are the student's to write.
VERDICT_WORDS = (
    "better", "worse", "best", "worst", "winner", "wins", "loses", "superior",
    "inferior", "recommend", "recommended", "preferred", "selected", "we choose",
    "outperforms", "beats", "excellent", "poor quality", "high quality",
    "good result", "bad result", "should be used",
)


def test_rendered_summary_contains_measurements_but_no_verdict():
    rows = [
        asdict(_row()),
        asdict(_row(method="img2img", influence_level="strong", strength_value=0.40,
                    effective_steps=12, process_config_key="img2img@512x512@tier0")),
    ]
    text = rs.render_summary_markdown(rs.summarize(rows), "EXP-009 measurements")
    lowered = text.lower()
    for word in VERDICT_WORDS:
        assert word not in lowered, f"summary must not contain verdict language: {word!r}"
    # It must still carry the numbers and the two reading rules.
    assert "peak alloc MiB" in text
    assert "s/eff step" in text
    assert "inverted" in lowered
    assert "process-level high-water marks" in text


def test_summary_flags_overflow_rows_instead_of_calling_them_a_success():
    rows = [asdict(_row(peak_vram_allocated_mb=10738.08, peak_vram_reserved_mb=14510.0))]
    summaries = rs.summarize(rows)
    assert summaries[0].vram_overflow_suspected is True
    assert "VRAM overflow suspected" in rs.render_summary_markdown(summaries, "t")


def test_summary_reports_seconds_per_effective_step_for_the_img2img_trap():
    rows = [
        asdict(_row(method="img2img", influence_level="strong", strength_value=0.40,
                    generate_seconds=1.8, effective_steps=12)),
    ]
    summary = rs.summarize(rows)[0]
    assert summary.median_seconds_per_effective_step == pytest.approx(0.15, abs=1e-4)


def test_summary_groups_by_method_resolution_level_and_tier():
    rows = [
        asdict(_row(seed=42)),
        asdict(_row(seed=1337)),
        asdict(_row(seed=42, influence_level="strong", strength_value=0.85)),
    ]
    summaries = rs.summarize(rows)
    assert len(summaries) == 2
    assert {s.influence_level for s in summaries} == {"medium", "strong"}
    assert [s.runs_ok for s in summaries] == [2, 1]


def test_failed_rows_survive_into_the_summary():
    rows = [
        asdict(_row()),
        asdict(_row(seed=1337, status=rs.STATUS_FAILED, error_type="OutOfMemoryError")),
    ]
    summary = rs.summarize(rows)[0]
    assert summary.runs_ok == 1
    assert summary.runs_failed == 1
    assert summary.failures == ["failed: OutOfMemoryError"]


# --- filenames ---------------------------------------------------------------


def test_output_filename_exposes_every_varying_condition():
    name = rs.build_output_filename(
        "EXP-009", "ip-adapter", "C1", "R1", "medium", 0.55, 512, 1536, 42, 0
    )
    for fragment in ("EXP-009", "ip-adapter", "C1", "R1", "medium", "s0p55", "512x1536", "seed42", "tier0"):
        assert fragment in name
    assert name.endswith(".png")


def test_text_only_filename_records_an_absent_strength_as_na():
    name = rs.build_output_filename(
        "EXP-010", "text-only", "C1", "R1", "none", None, 512, 512, 42, 0
    )
    assert "__sna__" in name


# --- the Phase 1 / Phase 2 boundary, enforced in code ------------------------


def test_phase_one_runner_never_imports_the_similarity_module():
    """The structural correction of the M4 plan, enforced statically.

    Loading the 2.35 GiB CLIP metric encoder inside a text-only or img2img
    process would inflate exactly the VRAM figures the method comparison rests
    on - the same class of error as the EXP-005 allocator contamination. Parsed
    with `ast` rather than imported, so this test needs neither torch nor a GPU.
    """
    source = (REPO / "ml" / "inference" / "reference_conditioning.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    # Fully-qualified names, so `from ml.evaluation import similarity` is caught
    # as `ml.evaluation.similarity` rather than hiding behind its package.
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
            imported.update(f"{node.module}.{alias.name}" for alias in node.names)

    forbidden = {"ml.evaluation.similarity"}
    assert not (imported & forbidden), (
        f"Phase-1 runner must not import the similarity module; found {imported & forbidden}"
    )
    for name in imported:
        assert "similarity" not in name, f"Phase-1 runner imports {name!r}"

    # The frozen prompt kit is the one thing the runner legitimately takes from
    # `ml.evaluation`: it holds no metric model, only the hash-locked prompts,
    # seeds and sampler settings shared with Prototype 1.
    assert "ml.evaluation.prompt_kit" in imported


def test_only_the_adapter_methods_declare_an_image_encoder():
    """Positive evidence that a text-only or img2img VRAM figure cannot contain
    an image encoder: the method registry says those arms load none."""
    assert rs.METHODS["text-only"].loads_image_encoder is False
    assert rs.METHODS["img2img"].loads_image_encoder is False
    assert rs.METHODS["ip-adapter"].loads_image_encoder is True
    assert rs.METHODS["ip-adapter-plus"].loads_image_encoder is True
    assert set(rs.ADAPTER_METHODS) == {"ip-adapter", "ip-adapter-plus"}


def test_only_safetensors_weights_are_ever_named():
    """.bin twins in the same repository are pickles; security.md treats
    untrusted binaries as untrusted."""
    for spec in rs.METHODS.values():
        if spec.weight_name:
            assert spec.weight_name.endswith(".safetensors")


def test_adapter_revision_is_a_full_commit_sha_not_a_branch():
    assert len(rs.IP_ADAPTER_REVISION) == 40
    assert all(c in "0123456789abcdef" for c in rs.IP_ADAPTER_REVISION)
    assert rs.IP_ADAPTER_REVISION == "018e402774aeeddd60609b4ecdb7e298259dc729"


def test_similarity_rows_serialise_with_their_stated_provenance(tmp_path):
    row = rs.SimilarityRow(
        output_sha256="d" * 64,
        exp_id="EXP-014",
        condition_id="C1",
        method="ip-adapter",
        influence_level="medium",
        strength_value=0.55,
        seed=42,
        width=512,
        height=512,
        reference_id="R1",
        dhash_distance_to_reference=18,
        overall_reference_similarity=0.71,
        similarity_to_baseline=0.62,
        baseline_output_sha256="f" * 64,
        copy_risk_flag=False,
        evaluation_device="cpu",
        evaluation_encoder_repo_id=rs.IP_ADAPTER_REPO,
        evaluation_encoder_revision_sha=rs.IP_ADAPTER_REVISION,
    )
    path = rs.write_similarity_csv([row], tmp_path / "similarity.csv")
    header = path.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert header == rs.SIMILARITY_FIELDNAMES
    # The device and encoder revision travel with every indicator, so a GPU
    # evaluation pass can never be mistaken for part of a generation figure.
    assert "evaluation_device" in header
    assert "evaluation_encoder_revision_sha" in header


def test_similarity_schema_names_the_indicator_by_what_it_measures():
    """Correction 3 of the plan: the CLIP indicator entangles subject,
    composition, semantics, colour and style, so it is never called a style
    score anywhere in the schema."""
    serialised = json.dumps(rs.SIMILARITY_FIELDNAMES)
    assert "overall_reference_similarity" in serialised
    assert "style_similarity" not in serialised
    assert "style" not in serialised
