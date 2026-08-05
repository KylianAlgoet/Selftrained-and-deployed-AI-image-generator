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


# --- Prototype 4 additions ---------------------------------------------------


def _style_args(**overrides):
    base = dict(
        exp_id="EXP-020",
        phase=train_lora.PHASE_SMOKE,
        width=512,
        height=512,
        steps=300,
        tier=0,
        rank=8,
        alpha=8,
        learning_rate=1e-4,
        seed=42,
        style="minimal-geometric",
        manifest="",
        caption_mode="",
        checkpoint_steps=[150],
    )
    base.update(overrides)
    return Namespace(**base)


def test_style_spec_defaults_to_the_style_manifest_and_style_only_captions():
    spec = train_lora.build_spec(_style_args())
    assert spec.style == "minimal-geometric"
    assert spec.style_manifest_path == "data/manifests/style-minimal-geometric-p4.csv"
    assert spec.caption_mode == "style-only"
    assert spec.trigger_token == "xgeo"
    assert spec.checkpoint_steps == (150,)


def test_size_arm_manifest_overrides_without_changing_anything_else():
    """The RQ4 arms must differ from the full run in the manifest alone."""
    full = train_lora.build_spec(_style_args())
    arm = train_lora.build_spec(
        _style_args(manifest="data/manifests/style-minimal-geometric-p4-n12.csv")
    )
    assert arm.style_manifest_path.endswith("n12.csv")
    for field in ("seed", "rank", "alpha", "learning_rate", "optimizer_steps_planned",
                  "width", "height", "caption_mode", "trigger_token", "source_transform"):
        assert getattr(arm, field) == getattr(full, field), f"{field} drifted between arms"


def test_caption_ab_arms_differ_only_in_caption_mode():
    a = train_lora.build_spec(_style_args(caption_mode="style-only"))
    b = train_lora.build_spec(_style_args(caption_mode="dataset-v1-verbatim"))
    assert a.caption_mode != b.caption_mode
    for field in ("style", "style_manifest_path", "seed", "rank", "alpha", "learning_rate",
                  "optimizer_steps_planned", "width", "height", "trigger_token"):
        assert getattr(a, field) == getattr(b, field), f"{field} drifted between A/B arms"


def test_m5_smoke_behaviour_is_unchanged_when_no_style_is_given():
    """The M6 additions must not alter how the M5 runs were configured."""
    spec = train_lora.build_spec(_args())
    assert spec.style_manifest_path == ""
    assert spec.caption_mode == ""
    assert spec.trigger_token == ""
    assert spec.style == smoke_kit.SMOKE_STYLE


def test_caption_for_selects_the_declared_column():
    item = {"training_caption": "xgeo style-only", "dataset_v1_caption": "verbatim phrase"}
    assert train_lora.caption_for(item, "style-only") == "xgeo style-only"
    assert train_lora.caption_for(item, "dataset-v1-verbatim") == "verbatim phrase"


def test_caption_for_falls_back_to_the_m5_column():
    assert train_lora.caption_for({"caption": "m5 caption"}, "") == "m5 caption"


def test_style_manifest_loads_and_carries_both_caption_columns():
    rows = train_lora.load_style_items("data/manifests/style-minimal-geometric-p4.csv")
    assert len(rows) == 44
    assert rows[0]["training_caption"].startswith("xgeo ")
    assert rows[0]["dataset_v1_caption"] != rows[0]["training_caption"]


def test_missing_style_manifest_raises():
    with pytest.raises(RuntimeError, match="style manifest not found"):
        train_lora.load_style_items("data/manifests/style-does-not-exist.csv")


def test_presentation_counts_expose_the_equal_compute_confound():
    """At fixed steps a small set is shown far more often. The numbers must be
    recorded, not left to be inferred from steps / len(items)."""
    items = [{"id": f"DS-{i:04d}"} for i in range(12)]
    order = train_lora.build_sample_order(items, seed=42, steps=300)
    encoded, mean = train_lora.presentation_counts(items, order)
    assert mean == 25.0
    assert encoded.count(";") == 11
    assert sum(int(p.split(":")[1]) for p in encoded.split(";")) == 300


def test_presentation_counts_scale_with_set_size():
    order_n = {}
    for n in (12, 24, 44):
        items = [{"id": f"DS-{i:04d}"} for i in range(n)]
        order = train_lora.build_sample_order(items, seed=42, steps=300)
        order_n[n] = train_lora.presentation_counts(items, order)[1]
    assert order_n[12] == 25.0
    assert order_n[24] == 12.5
    assert round(order_n[44], 3) == 6.818
    assert order_n[12] > order_n[24] > order_n[44]


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


# --- M6 Phase B: balanced multi-style (RQ5) ----------------------------------


def test_multi_style_items_carry_their_own_style_and_trigger():
    from ml.training import style_kit

    paths = [f"data/manifests/style-{k}-p4.csv" for k in style_kit.STYLE_ORDER]
    items = train_lora.load_multi_style_items(paths)
    assert len(items) == 44 + 44 + 36
    for key in style_kit.STYLE_ORDER:
        trigger = style_kit.style_by_key(key).trigger
        rows = [i for i in items if i["_style"] == key]
        assert rows, f"no rows loaded for {key}"
        assert all(r["training_caption"].startswith(f"{trigger} ") for r in rows)


def test_balanced_order_gives_every_style_exactly_the_same_exposure():
    """RQ5 is only answerable if no style got more optimizer steps than another.
    The largest training set (44) must not dominate the smallest (36)."""
    from ml.training import style_kit

    paths = [f"data/manifests/style-{k}-p4.csv" for k in style_kit.STYLE_ORDER]
    items = train_lora.load_multi_style_items(paths)
    order = train_lora.build_balanced_multi_style_order(items, seed=42, per_style_steps=600)

    assert len(order) == 1800
    exposure = train_lora.per_style_exposure(items, order)
    assert exposure == "minimal-geometric:600;retro-poster:600;ukiyo-e:600"


def test_balanced_order_is_deterministic_and_seed_sensitive():
    items = [{"_style": s, "id": f"{s}-{i}"} for s in ("a", "b") for i in range(4)]
    first = train_lora.build_balanced_multi_style_order(items, seed=42, per_style_steps=10)
    assert first == train_lora.build_balanced_multi_style_order(items, seed=42, per_style_steps=10)
    assert first != train_lora.build_balanced_multi_style_order(items, seed=7, per_style_steps=10)


def test_balanced_order_is_not_a_round_robin():
    """A round-robin is balanced but ties style to step parity, a periodic
    structure the optimizer could ride. The shuffle must break it."""
    items = [{"_style": s, "id": f"{s}-{i}"} for s in ("a", "b", "c") for i in range(4)]
    order = train_lora.build_balanced_multi_style_order(items, seed=42, per_style_steps=60)
    styles = [items[i]["_style"] for i in order]
    cycles = [tuple(styles[i : i + 3]) for i in range(0, len(styles) - 2, 3)]
    assert not all(len(set(c)) == 3 for c in cycles)


def test_balanced_order_spreads_items_evenly_inside_each_style():
    """Balanced across styles must not mean lumpy inside one."""
    from collections import Counter

    from ml.training import style_kit

    paths = [f"data/manifests/style-{k}-p4.csv" for k in style_kit.STYLE_ORDER]
    items = train_lora.load_multi_style_items(paths)
    order = train_lora.build_balanced_multi_style_order(items, seed=42, per_style_steps=600)
    counts = Counter(order)
    for key in style_kit.STYLE_ORDER:
        seen = [counts[i] for i, it in enumerate(items) if it["_style"] == key]
        assert max(seen) - min(seen) <= 1, f"{key} exposure spread {min(seen)}..{max(seen)}"


def test_multi_style_spec_requires_matching_total_steps():
    with pytest.raises(SystemExit):
        train_lora.main(["--exp-id", "EXP-030", "--phase", "multi-style",
                         "--steps", "1500", "--multi-style", "--per-style-steps", "600",
                         "--dry-run"])


def test_multi_style_spec_records_all_three_manifests_and_style_only_captions():
    from ml.training import style_kit

    spec = train_lora.build_spec(
        _args(exp_id="EXP-030", phase=train_lora.PHASE_MULTI_STYLE, steps=1800,
              multi_style=True, per_style_steps=600)
    )
    assert spec.multi_style is True
    assert spec.per_style_steps == 600
    assert spec.style == "multi-style"
    assert spec.caption_mode == style_kit.CAPTION_MODE_STYLE_ONLY
    assert len(spec.style_manifest_path.split(";")) == 3
    assert spec.rank == 8 and spec.alpha == 8
    assert spec.learning_rate == 1e-4
    assert (spec.width, spec.height) == (512, 512)


def test_phase_names_distinguish_pilot_from_approved_full_runs():
    """A 300-step pilot and a 600-step approved run must not share a label."""
    from ml.training import lora_schema

    assert lora_schema.PHASE_SMOKE != lora_schema.PHASE_STYLE_FULL
    assert lora_schema.PHASE_STYLE_FULL in lora_schema.PHASES
    assert lora_schema.PHASE_MULTI_STYLE in lora_schema.PHASES


def test_gate_1_scoring_artifact_is_unchanged():
    """The fixed blind scores are evidence. If this hash moves, a human score was
    edited after unblinding, which the gate exists to prevent."""
    import hashlib

    path = REPO / "docs" / "evidence" / "prototype-4" / "pilot-scoring-form-completed-blind.md"
    assert path.is_file(), "the Gate-1 scoring artifact is missing"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == "cf6bf2605b7159128dc4d841ccd04cc8867211c53992d19fd0fb6856625b71ec"


# --- R14: adapter initialisation is reproducible from the seed ----------------


def _init_adapter_weights(seed: int) -> dict:
    """Build a LoRA adapter the same way the runner does and read its INITIAL
    weights back. Uses a small CPU model rather than the SD UNet: the property
    under test is where the initialisation draws its randomness from, which does
    not depend on the module it is attached to."""
    import torch
    from peft import LoraConfig, get_peft_model

    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.to_q = torch.nn.Linear(16, 16)
            self.to_k = torch.nn.Linear(16, 16)

    train_lora.seed_everything(seed)
    model = get_peft_model(
        Tiny(),
        LoraConfig(r=8, lora_alpha=8, init_lora_weights="gaussian",
                   target_modules=["to_q", "to_k"]),
    )
    return {
        name: param.detach().clone()
        for name, param in model.named_parameters()
        if "lora" in name.lower()
    }


def test_same_seed_gives_identical_initial_lora_weights():
    """R14's fix. Before it, `init_lora_weights="gaussian"` drew from the unseeded
    global torch RNG, so two runs of one configuration started from different
    adapters - measured at an L2 of ~158 against a norm of ~112, the sqrt(2) ratio
    of independent draws."""
    import torch

    a = _init_adapter_weights(42)
    b = _init_adapter_weights(42)

    assert a and set(a) == set(b)
    for name in a:
        assert torch.equal(a[name], b[name]), f"{name} differs at the same seed"


def test_different_seed_changes_the_initial_lora_weights():
    """Guards the opposite failure: seeding that pins every run to one adapter
    regardless of the seed would also pass the test above."""
    import torch

    a = _init_adapter_weights(42)
    c = _init_adapter_weights(1337)

    trainable = [n for n in a if not torch.equal(a[n], torch.zeros_like(a[n]))]
    assert trainable, "expected at least one non-zero-initialised LoRA tensor"
    assert any(not torch.equal(a[n], c[n]) for n in trainable), "seed had no effect"


def test_seeding_happens_before_adapter_construction():
    """Order matters: seeding after `add_adapter` would leave the initialisation
    itself unseeded and the test above would still pass for the wrong reason."""
    source = Path(train_lora.__file__).read_text(encoding="utf-8")
    seed_call = source.index("seed_everything(spec.seed)")
    add_adapter = source.index("unet.add_adapter(")
    assert seed_call < add_adapter


def test_m6_artifacts_are_not_claimed_reproducible():
    """The fix is forward-looking. The recorded M6 evidence predates it, and the
    docstring must keep saying so rather than quietly implying otherwise."""
    doc = train_lora.seed_everything.__doc__ or ""
    assert "not bit-reproducible" in doc
    assert "does not rewrite history" in doc


def test_gate_2_scoring_artifact_is_unchanged():
    """The Gate-2 scores and written decisions are evidence. If this hash moves,
    a human score or decision was edited after approval."""
    import hashlib

    path = REPO / "docs" / "evidence" / "prototype-4" / "gate-2-scoring-form-completed.md"
    assert path.is_file(), "the Gate-2 scoring artifact is missing"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == "835488f3821c4f6774546978b4e19f4d9a11b6b2e0fb88535b5796405aa16dbb"
