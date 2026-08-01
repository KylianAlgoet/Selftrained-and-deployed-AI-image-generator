"""Unit tests for the Phase-2 similarity evaluator's pure logic.

CPU-only and model-free: `ml.evaluation.similarity` imports torch, transformers
and PIL only inside the functions that need them, so the baseline matching, the
copy-risk threshold and the row filtering are testable without downloading a
2.35 GiB encoder.

These cover the parts that decide WHAT each indicator is compared against. A
wrong baseline match would not raise - it would silently produce a plausible
`similarity_to_baseline` column describing the wrong comparison.
"""

import ast
from pathlib import Path

from ml.dataset.hashing import NEAR_DUPLICATE_MAX_DISTANCE
from ml.evaluation import similarity as sim
from ml.inference import reference_schema as rs

REPO = Path(__file__).resolve().parents[3]


def _gen(**overrides) -> dict:
    row = dict(
        exp_id="EXP-009",
        condition_id="C1",
        prompt_id="P1-poster",
        method="ip-adapter",
        influence_level="medium",
        strength_value=0.55,
        seed=42,
        width=512,
        height=512,
        reference_id="R1",
        output_sha256="d" * 64,
        output_path="outputs/EXP-009/image.png",
        status=rs.STATUS_OK,
    )
    row.update(overrides)
    return row


# --- baseline matching -------------------------------------------------------


def test_baseline_is_keyed_on_the_prompt_not_the_condition():
    """A text-only output uses no reference at all, so it is fully determined by
    prompt, seed and geometry. Keying on the condition would leave every stress
    row without a baseline for no real reason."""
    baseline = _gen(method="text-only", condition_id="C2", prompt_id="P2-geo",
                    reference_id="", output_sha256="b" * 64)
    # C5 is the conflict condition and shares P2-geo with C2.
    conflict = _gen(condition_id="C5", prompt_id="P2-geo", reference_id="R3")

    index = sim.baseline_index([baseline, conflict])
    assert sim.baseline_for(conflict, index) == "b" * 64


def test_the_condition_table_really_does_share_prompts_across_the_stress_arm():
    """Guards the assumption the previous test rests on, against the actual
    frozen condition table rather than a fixture."""
    prompts = {c_id: c.prompt_id for c_id, c in rs.CONDITIONS.items()}
    assert prompts["C5"] == prompts["C2"] == "P2-geo"
    assert prompts["C6"] == prompts["C1"] == "P1-poster"


def test_a_baseline_is_never_substituted_across_seed_or_geometry():
    baseline = _gen(method="text-only", reference_id="", output_sha256="b" * 64)
    index = sim.baseline_index([baseline])

    assert sim.baseline_for(_gen(seed=1337), index) == ""
    assert sim.baseline_for(_gen(width=512, height=1536), index) == ""
    assert sim.baseline_for(_gen(prompt_id="P3-ukiyo"), index) == ""
    # The matching cell still resolves.
    assert sim.baseline_for(_gen(), index) == "b" * 64


def test_a_failed_text_only_run_is_not_used_as_a_baseline():
    """A failed run has no image, so treating it as a baseline would silently
    produce an empty comparison presented as a real one."""
    broken = _gen(method="text-only", reference_id="", output_sha256="",
                  status=rs.STATUS_FAILED)
    assert sim.baseline_index([broken]) == {}


# --- what gets evaluated -----------------------------------------------------


def test_only_successful_rows_with_an_image_are_evaluated():
    rows = [
        _gen(),
        _gen(output_sha256="e" * 64, status=rs.STATUS_FAILED),
        _gen(output_sha256="f" * 64, status=rs.STATUS_TIMEOUT),
        _gen(output_sha256="a" * 64, output_path=""),
    ]
    evaluable = sim.evaluable_rows(rows)
    assert len(evaluable) == 1
    assert evaluable[0]["output_sha256"] == "d" * 64
    # The excluded rows are filtered here only; they remain in the generation
    # results, where a failure is a first-class result.
    assert len(rows) == 4


# --- copy risk ---------------------------------------------------------------


def test_copy_risk_uses_the_existing_project_threshold():
    assert sim.is_copy_risk(0) is True
    assert sim.is_copy_risk(NEAR_DUPLICATE_MAX_DISTANCE) is True
    assert sim.is_copy_risk(NEAR_DUPLICATE_MAX_DISTANCE + 1) is False
    # The text-only arm has no reference, so it has no distance and no flag.
    assert sim.is_copy_risk("") is False
    assert sim.is_copy_risk(None) is False


# --- the Phase 1 / Phase 2 boundary ------------------------------------------


def test_the_evaluator_is_pinned_to_a_recorded_encoder_revision():
    """The evaluation encoder is pinned exactly like a generation component, so
    an indicator can always be traced back to the weights that produced it."""
    assert sim.EVALUATION_ENCODER_REVISION == rs.IP_ADAPTER_REVISION
    assert len(sim.EVALUATION_ENCODER_REVISION) == 40


def test_the_evaluator_never_imports_the_phase_one_runner():
    """The guard runs in both directions. Phase 2 needs the schema, never the
    runner: importing it would pull diffusers into the evaluation process and
    blur the boundary the two-phase design exists to keep sharp."""
    source = (REPO / "ml" / "evaluation" / "similarity.py").read_text(encoding="utf-8")
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    assert "ml.inference.reference_conditioning" not in imported
    assert "diffusers" not in imported
    assert "ml.inference.reference_schema" in imported
