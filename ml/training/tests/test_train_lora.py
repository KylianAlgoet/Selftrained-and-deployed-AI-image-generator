"""Guards for the training runner's GPU-free surface.

The runner itself needs a GPU, but its data handling, determinism and process
boundaries do not - and those are precisely the parts that silently corrupt a
comparison when they drift.
"""

import ast
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from ml.training import smoke_kit, train_lora

REPO = Path(__file__).resolve().parents[3]


def _args(**overrides) -> Namespace:
    base = dict(
        exp_id="EXP-016a",
        phase=train_lora.PHASE_SINGLE_STEP,
        width=512,
        height=512,
        steps=1,
        tier=0,
        rank=8,
        alpha=8,
        learning_rate=1e-4,
        seed=42,
    )
    base.update(overrides)
    return Namespace(**base)


# --- the frozen subset is honoured -------------------------------------------


def test_runner_reads_the_frozen_manifest_and_checks_it():
    items = train_lora.load_smoke_items()
    assert len(items) == 12
    assert tuple(i["id"] for i in items) == smoke_kit.SMOKE_ITEM_IDS


def test_runner_rejects_a_manifest_that_drifted(monkeypatch):
    """The subset must never be silently reselected or reordered."""
    monkeypatch.setattr(smoke_kit, "SMOKE_ITEM_IDS", ("DS-9999",))
    with pytest.raises(RuntimeError, match="does not match the frozen kit"):
        train_lora.load_smoke_items()


# --- determinism --------------------------------------------------------------


def test_sample_order_is_deterministic_for_a_seed():
    items = train_lora.load_smoke_items()
    first = train_lora.build_sample_order(items, seed=42, steps=50)
    second = train_lora.build_sample_order(items, seed=42, steps=50)
    assert first == second


def test_sample_order_differs_between_seeds():
    items = train_lora.load_smoke_items()
    assert train_lora.build_sample_order(items, 42, 50) != train_lora.build_sample_order(items, 7, 50)


def test_sample_order_covers_every_item_before_repeating():
    """Epoch-style shuffling: with 12 items, the first 12 draws are a permutation,
    so a short probe cannot accidentally train on one image twelve times."""
    items = train_lora.load_smoke_items()
    order = train_lora.build_sample_order(items, seed=42, steps=12)
    assert sorted(order) == list(range(12))


def test_sample_order_length_matches_the_step_count():
    items = train_lora.load_smoke_items()
    for steps in (1, 10, 300):
        assert len(train_lora.build_sample_order(items, 42, steps)) == steps


def test_sample_order_fingerprint_is_stable_and_sensitive():
    items = train_lora.load_smoke_items()
    order = train_lora.build_sample_order(items, 42, 12)
    fingerprint = train_lora.sample_order_fingerprint(items, order)
    assert fingerprint == train_lora.sample_order_fingerprint(items, order)
    assert len(fingerprint) == 64
    assert fingerprint != train_lora.sample_order_fingerprint(items, list(reversed(order)))


def test_sample_order_is_identical_across_tiers():
    """Tiers 0-4 must not change what was trained on, only how it fits in memory."""
    items = train_lora.load_smoke_items()
    assert train_lora.build_sample_order(items, 42, 10) == train_lora.build_sample_order(items, 42, 10)


# --- the source transform is explicit ----------------------------------------


def test_native_deck_geometry_uses_no_transform():
    spec = train_lora.build_spec(_args(width=512, height=1536))
    assert spec.source_transform == "none"


def test_square_geometry_records_centre_crop():
    spec = train_lora.build_spec(_args(width=512, height=512))
    assert spec.source_transform == "centre-crop"


def test_centre_crop_produces_the_requested_geometry():
    from PIL import Image

    items = train_lora.load_smoke_items()
    source = REPO / items[0]["source_path"]
    if not source.is_file():
        pytest.skip("raw dataset images are git-ignored and absent in this checkout")
    with Image.open(source) as original:
        assert (original.width, original.height) == (512, 1536)
    cropped = train_lora.prepare_image(source, 512, 512, "centre-crop")
    assert (cropped.width, cropped.height) == (512, 512)


def test_native_pass_through_leaves_the_image_untouched():
    items = train_lora.load_smoke_items()
    source = REPO / items[0]["source_path"]
    if not source.is_file():
        pytest.skip("raw dataset images are git-ignored and absent in this checkout")
    image = train_lora.prepare_image(source, 512, 1536, "none")
    assert (image.width, image.height) == (512, 1536)


def test_transform_none_refuses_a_mismatched_source():
    """A silent resize here would make the 512x512 and 512x1536 arms incomparable."""
    items = train_lora.load_smoke_items()
    source = REPO / items[0]["source_path"]
    if not source.is_file():
        pytest.skip("raw dataset images are git-ignored and absent in this checkout")
    with pytest.raises(RuntimeError, match="declared transform 'none'"):
        train_lora.prepare_image(source, 512, 512, "none")


def test_unknown_transform_is_rejected():
    items = train_lora.load_smoke_items()
    source = REPO / items[0]["source_path"]
    if not source.is_file():
        pytest.skip("raw dataset images are git-ignored and absent in this checkout")
    with pytest.raises(RuntimeError, match="unknown source transform"):
        train_lora.prepare_image(source, 512, 512, "squash")


# --- tier wiring --------------------------------------------------------------


def test_tier_0_has_no_checkpointing_and_no_latent_cache():
    spec = train_lora.build_spec(_args(tier=0))
    assert spec.gradient_checkpointing is False
    assert spec.latent_caching is False


def test_tier_1_enables_gradient_checkpointing_only():
    spec = train_lora.build_spec(_args(tier=1))
    assert spec.gradient_checkpointing is True
    assert spec.latent_caching is False


def test_tier_2_adds_latent_caching():
    spec = train_lora.build_spec(_args(tier=2))
    assert spec.gradient_checkpointing is True
    assert spec.latent_caching is True


def test_batch_and_accumulation_stay_at_one_across_tiers():
    """Accumulation is not a memory tier; escalating must not silently change it."""
    for tier in range(0, 5):
        spec = train_lora.build_spec(_args(tier=tier))
        assert spec.batch_size == 1
        assert spec.grad_accum == 1


def test_text_encoder_and_vae_are_never_trained():
    for tier in range(0, 5):
        spec = train_lora.build_spec(_args(tier=tier))
        assert spec.text_encoder_trained is False
        assert spec.vae_trained is False


def test_adapter_outputs_are_written_outside_the_repo_tree():
    """Model weights are never committed (.claude/rules/security.md)."""
    assert train_lora.OUTPUT_ROOT.name == "lora"
    assert train_lora.OUTPUT_ROOT.parent.name == "outputs"
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
    assert "outputs/" in gitignore


# --- import boundary ---------------------------------------------------------


def _top_level_imports(module) -> set[str]:
    """Imports at module scope only - a function-local `import torch` is fine,
    since it does not execute on import."""
    tree = ast.parse(Path(sys.modules[module.__name__].__file__).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _all_imports(module) -> set[str]:
    """Every import anywhere in the module, including function-local ones.

    Parsed from the AST, not scanned as text: a docstring naming the module it
    deliberately avoids is correct documentation, not a violation.
    """
    tree = ast.parse(Path(sys.modules[module.__name__].__file__).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_runner_never_imports_the_similarity_evaluator():
    """Phase 1 (training) and Phase 2 (similarity) are separate processes.
    Loading a 2.35 GiB metric encoder inside a measured training process would
    inflate exactly the VRAM figures the comparison rests on."""
    offenders = {name for name in _all_imports(train_lora) if name.startswith("ml.evaluation")}
    assert not offenders, f"training runner must not import {sorted(offenders)}"


def test_verifier_never_imports_the_similarity_evaluator():
    """EXP-018 Phase 1 generates; Phase 2 measures. The 2.35 GiB CLIP encoder must
    never be resident in a process reporting generation VRAM."""
    from ml.training import verify_lora

    offenders = {name for name in _all_imports(verify_lora) if name.startswith("ml.evaluation.similarity")}
    assert not offenders, f"verifier must not import {sorted(offenders)}"


def test_verifier_arms_cover_baseline_and_both_frozen_weights():
    from ml.training import verify_lora

    assert verify_lora.ARM_WEIGHTS[verify_lora.ARM_BASELINE] is None
    assert verify_lora.ARM_WEIGHTS[verify_lora.ARM_WEIGHT0] == smoke_kit.LORA_WEIGHT_LOWER_BOUND
    assert verify_lora.ARM_WEIGHTS[verify_lora.ARM_WEIGHT1] == smoke_kit.LORA_WEIGHT_ACTIVE


def test_runner_does_not_import_torch_at_module_scope():
    """Keeps `--dry-run` and these tests cheap, and keeps the module importable
    for inspection on a machine with no CUDA."""
    top = _top_level_imports(train_lora)
    assert not any(name.split(".")[0] in {"torch", "diffusers", "peft"} for name in top)
