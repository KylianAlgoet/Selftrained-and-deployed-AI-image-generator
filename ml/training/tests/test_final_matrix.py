"""Guards for the EXP-031 final validation matrix's GPU-free surface.

The cap, the candidate set and the prompt roles decide what GPU work happens.
They are exactly the things that must not drift silently.
"""

import ast
import sys
from pathlib import Path

from ml.training import final_matrix as fm
from ml.training import style_kit

REPO = Path(__file__).resolve().parents[3]


def _all_imports(module) -> set[str]:
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_matrix_stays_within_the_pre_declared_cap():
    """The cap is asserted before any GPU work, not tallied afterwards."""
    assert fm.planned_generations() <= style_kit.FINAL_MATRIX_MAX_GENERATIONS


def test_every_arm_has_a_plan_and_no_arm_is_empty():
    arms = fm.planned_arms()
    assert arms
    for arm in arms:
        assert fm.plan_for_arm(arm["kind"], arm["geometry"]), arm


def test_candidates_are_only_gate_1_approved_full_runs():
    """A rejected pilot checkpoint must never reach the final matrix."""
    approved_runs = {"EXP-027", "EXP-028", "EXP-029"}
    assert {c[0] for c in fm.CANDIDATES} == approved_runs
    assert {c[2] for c in fm.CANDIDATES} <= {300, 600}
    pilots = {"EXP-020", "EXP-021", "EXP-022", "EXP-023", "EXP-024n12", "EXP-024n24"}
    assert not ({c[0] for c in fm.CANDIDATES} & pilots)


def test_all_four_prompt_roles_are_present():
    roles = {p.role for p in fm.FINAL_PROMPTS}
    assert roles == {"style-matching", "shared-cross-style", "out-of-style", "style-free"}


def test_style_free_prompt_carries_neither_trigger_nor_phrase():
    """It exists to detect leakage into prompts that never asked for the style."""
    p = fm.prompt_by_id("FP4-style-free")
    assert "{trigger}" not in p.template
    assert "{phrase}" not in p.template


def test_built_prompts_carry_the_frozen_trigger_sequences():
    for key in style_kit.STYLE_ORDER:
        trigger = style_kit.style_by_key(key).trigger
        text = fm.build_prompt(key, fm.prompt_by_id("FP1-style").template)
        assert text.startswith(f"{trigger} ")


def test_weight_sweep_includes_the_zero_lower_bound():
    """Weight 0.0 is the diagnostic that the adapter is actually being applied."""
    assert 0.0 in fm.WEIGHTS_SWEEP
    assert 1.0 in fm.WEIGHTS_SWEEP


def test_both_geometries_are_covered_including_the_deck_format():
    geometries = {a["geometry"] for a in fm.planned_arms()}
    assert geometries == {"512x512", "512x1536"}


def test_base_control_arm_exists_for_every_style():
    base_styles = {a["style"] for a in fm.planned_arms() if a["kind"] == "base"}
    assert base_styles == set(style_kit.STYLE_ORDER)


def test_matrix_never_imports_the_similarity_evaluator():
    """Phase 1 generates; Phase 2 measures. The 2.35 GiB CLIP encoder must never be
    resident in a process reporting generation VRAM."""
    offenders = {n for n in _all_imports(fm) if n.startswith("ml.evaluation.similarity")}
    assert not offenders, f"final matrix must not import {sorted(offenders)}"


def test_matrix_fingerprint_is_stable_across_calls():
    assert fm.matrix_fingerprint() == fm.matrix_fingerprint()


def test_style_kit_fingerprint_is_untouched_by_phase_b():
    """Phase B added no entry to the hash-locked kit, so every Phase-A row's
    recorded fingerprint still refers to the same object."""
    assert style_kit.kit_fingerprint() == (
        "fc11d8289a88760745a6228d94c498d1ed95648a6c38f80c1a88601de202a58b"
    )


def test_gate_1_approval_record_exists_and_names_the_scoring_artifact():
    path = REPO / "docs" / "evidence" / "prototype-4" / "GATE-1-approval.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "cf6bf2605b7159128dc4d841ccd04cc8867211c53992d19fd0fb6856625b71ec" in text
    assert "Kylian Algoet" in text


def test_no_arm_generates_the_same_configuration_twice():
    """Blocks A and B overlap at the nominal weight. The first executed matrix
    repeated 24 cells because of it, wasting capped GPU budget and putting a
    self-pair into every diversity cell it touched."""
    for arm in fm.planned_arms():
        plan = fm.plan_for_arm(arm["kind"], arm["geometry"])
        assert len(plan) == len(set(plan)), f"{arm} repeats a configuration"


def test_dedup_removed_exactly_the_overlapping_cells():
    """The unique set is unchanged; only repeats were dropped. 252 executed
    generations covered 228 distinct configurations."""
    assert fm.planned_generations() == 228
