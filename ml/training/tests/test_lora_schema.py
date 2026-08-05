"""Guards for the Prototype 3 training schema.

The tier-ladder and gate tests carry the weight here. The ladder must not drift
back into the inference ladder's shape, and `GateRecord.passed()` must not
quietly start accepting a run that merely failed to raise.
"""

import ast
import json
import sys
from pathlib import Path

import pytest

from ml.inference import bench_schema
from ml.training import lora_schema as ls


def _spec(**overrides) -> ls.TrainingSpec:
    base = dict(
        exp_id="EXP-016",
        phase=ls.PHASE_SINGLE_STEP,
        memory_tier=0,
        dataset_version="dataset-v1",
        smoke_manifest_path="data/manifests/smoke-test-p3.csv",
        style="minimal-geometric",
        caption_strategy="dataset-v1 captions verbatim; no trigger token",
        width=512,
        height=512,
        source_transform="centre-crop",
        rank=8,
        alpha=8,
        target_modules="unet attention to_q,to_k,to_v,to_out.0",
        learning_rate=1e-4,
        optimizer="torch.optim.AdamW",
        optimizer_state_dtype="fp32",
        optimizer_steps_planned=1,
        batch_size=1,
        grad_accum=1,
        text_encoder_trained=False,
        vae_trained=False,
        gradient_checkpointing=False,
        latent_caching=False,
        precision="fp16",
        attention_impl="sdpa",
        seed=42,
    )
    base.update(overrides)
    return ls.TrainingSpec(**base)


def _passing_gates(**overrides) -> ls.GateRecord:
    base = dict(
        trainable_lora_parameters=797184,
        trainable_lora_tensors=128,
        expected_trainable_parameters=797184,
        base_unet_parameters_frozen=True,
        optimizer_steps_completed=1,
        global_steps_completed=1,
        gradients_present=True,
        gradients_finite=True,
        gradients_nonzero=True,
        losses_finite=True,
        lora_params_changed=True,
    )
    base.update(overrides)
    return ls.GateRecord(**base)


# --- pinned model ------------------------------------------------------------


def test_base_model_is_the_dr007_selection_pinned_to_a_sha():
    assert ls.BASE_MODEL_REPO_ID == "stable-diffusion-v1-5/stable-diffusion-v1-5"
    assert ls.BASE_MODEL_REVISION == "451f4fe16113bff5a5d2269ed5ad43b0592e9a14"
    assert len(ls.BASE_MODEL_REVISION) == 40


# --- the training tier ladder ------------------------------------------------


def test_tier_ladder_is_contiguous_and_documented():
    assert sorted(ls.TRAINING_MEMORY_TIERS) == [0, 1, 2, 3, 4, 5]
    for tier, text in ls.TRAINING_MEMORY_TIERS.items():
        assert text.strip(), f"tier {tier} has no description"


def test_escalation_stops_at_the_last_comparable_tier():
    assert ls.next_training_tier(0) == 1
    assert ls.next_training_tier(3) == 4
    assert ls.next_training_tier(ls.MAX_COMPARABLE_TRAINING_TIER) is None
    assert ls.next_training_tier(5) is None


def test_only_tier_5_breaks_comparability():
    for tier in range(0, 5):
        assert not ls.tier_breaks_comparability(tier)
    assert ls.tier_breaks_comparability(5)


def test_tier_0_matches_the_declared_baseline_configuration():
    text = ls.TRAINING_MEMORY_TIERS[0]
    assert "fp16" in text
    assert "no gradient checkpointing" in text
    assert "no latent cache" in text


def test_tier_1_is_gradient_checkpointing_and_tier_2_is_cached_latents():
    assert "gradient checkpointing" in ls.TRAINING_MEMORY_TIERS[1]
    assert "precomputed outside the measured process" in ls.TRAINING_MEMORY_TIERS[2]


def test_gradient_accumulation_is_not_a_memory_tier():
    """At micro-batch 1 it changes effective batch size, not micro-step peak memory.

    This is the correction that removed it from the ladder; the guard keeps it out.
    """
    for text in ls.TRAINING_MEMORY_TIERS.values():
        lowered = text.lower()
        assert "accumulation" not in lowered
        assert "grad accum" not in lowered


def test_training_ladder_is_distinct_from_the_inference_ladder():
    """Conflating them would let 'tier 2' mean two different things by milestone."""
    assert ls.TRAINING_MEMORY_TIERS != bench_schema.MEMORY_TIERS
    for tier in (1, 2, 3, 4):
        assert ls.TRAINING_MEMORY_TIERS[tier] != bench_schema.MEMORY_TIERS[tier]


def test_inference_only_remedies_do_not_appear_in_the_training_ladder():
    for tier in range(0, 5):
        lowered = ls.TRAINING_MEMORY_TIERS[tier].lower()
        assert "attention slicing" not in lowered
        assert "cpu offload" not in lowered


def test_tier_invariants_name_the_things_that_must_not_move():
    for name in ("sample_order_sha256", "seed", "optimizer_steps_planned", "rank"):
        assert name in ls.TIER_INVARIANTS


# --- phases and limits -------------------------------------------------------


def test_phases_are_ordered_shortest_first():
    """M5's micro-gating order, then M6 Phase B's longer approved runs appended.
    The M5 prefix stays fixed so existing rows keep their meaning."""
    assert ls.PHASES[:3] == (ls.PHASE_SINGLE_STEP, ls.PHASE_STABILITY, ls.PHASE_SMOKE)
    assert ls.PHASES == (
        ls.PHASE_SINGLE_STEP,
        ls.PHASE_STABILITY,
        ls.PHASE_SMOKE,
        ls.PHASE_STYLE_FULL,
        ls.PHASE_MULTI_STYLE,
    )


def test_run_limits_match_the_approved_plan():
    assert ls.PROBE_WALL_LIMIT_SECONDS == 20 * 60
    assert ls.SMOKE_WALL_ASK_THRESHOLD_SECONDS == 60 * 60


# --- spec --------------------------------------------------------------------


def test_effective_batch_size_multiplies_accumulation():
    assert _spec(batch_size=1, grad_accum=1).effective_batch_size == 1
    assert _spec(batch_size=1, grad_accum=4).effective_batch_size == 4


def test_process_config_key_separates_geometry_tier_and_phase():
    a = _spec(width=512, height=512).process_config_key
    b = _spec(width=512, height=1536).process_config_key
    c = _spec(width=512, height=512, memory_tier=1).process_config_key
    d = _spec(width=512, height=512, phase=ls.PHASE_SMOKE).process_config_key
    assert len({a, b, c, d}) == 4


def test_spec_is_frozen():
    spec = _spec()
    with pytest.raises(Exception):
        spec.rank = 16  # type: ignore[misc]


def test_run_slug_encodes_every_varying_condition():
    slug = ls.build_run_slug(_spec(phase=ls.PHASE_SMOKE, optimizer_steps_planned=300))
    for fragment in ("EXP-016", "smoke", "512x512", "r8a8", "bs1x1", "st300", "seed42", "tier0"):
        assert fragment in slug
    assert "." not in slug, "a dot in the slug would break the file extension"


def test_run_slug_differs_when_geometry_differs():
    assert ls.build_run_slug(_spec(height=512)) != ls.build_run_slug(_spec(height=1536))


# --- gates -------------------------------------------------------------------


def test_a_fully_evidenced_run_passes():
    assert _passing_gates().passed() is True
    assert _passing_gates().failures() == []


def test_default_gate_record_does_not_pass():
    """An unmeasured run must never read as a success."""
    assert ls.GateRecord().passed() is False
    assert ls.GateRecord().failures()


@pytest.mark.parametrize(
    "override",
    [
        {"trainable_lora_parameters": 0, "expected_trainable_parameters": 0},
        {"base_unet_parameters_frozen": False},
        {"optimizer_steps_completed": 0},
        {"gradients_present": False},
        {"gradients_finite": False},
        {"gradients_nonzero": False},
        {"losses_finite": False},
        {"lora_params_changed": False},
    ],
)
def test_each_required_gate_can_fail_the_run(override):
    gates = _passing_gates(**override)
    assert gates.passed() is False
    assert gates.failures()


def test_a_mismatched_trainable_parameter_count_fails():
    """Non-zero is not enough - it must be the EXPECTED count."""
    gates = _passing_gates(trainable_lora_parameters=12, expected_trainable_parameters=797184)
    assert gates.passed() is False


def test_unmeasured_gates_are_not_treated_as_true():
    """'not measured' is not a pass; the default sentinel must never satisfy a gate."""
    gates = _passing_gates(base_unet_parameters_frozen="not measured")
    assert gates.passed() is False


def test_decreasing_loss_is_recorded_but_never_gated_on():
    """A few-hundred-step run on 12 images is too short and noisy to gate on."""
    assert _passing_gates(loss_decreased=False).passed() is True
    assert _passing_gates(loss_decreased="not measured").passed() is True
    assert "loss_decreased" not in " ".join(_passing_gates(loss_decreased=False).failures())


def test_failures_names_every_broken_gate():
    gates = _passing_gates(gradients_nonzero=False, losses_finite=False)
    failures = gates.failures()
    assert any("non-zero" in f for f in failures)
    assert any("finite" in f for f in failures)


# --- adapter artefact --------------------------------------------------------


def test_adapter_with_lora_keys_and_no_base_weights_is_lora_only():
    artifact = ls.AdapterArtifact(lora_key_count=128, unexpected_base_model_keys="")
    assert artifact.is_lora_only() is True


def test_adapter_carrying_base_model_keys_is_rejected():
    artifact = ls.AdapterArtifact(
        lora_key_count=128, unexpected_base_model_keys="conv_in.weight"
    )
    assert artifact.is_lora_only() is False


def test_adapter_with_no_lora_keys_is_rejected():
    assert ls.AdapterArtifact(lora_key_count=0).is_lora_only() is False


# --- writers -----------------------------------------------------------------


def _row(**overrides) -> ls.TrainingResultRow:
    spec = _spec()
    base = dict(
        exp_id=spec.exp_id,
        phase=spec.phase,
        timestamp_utc="2026-08-04T00:00:00Z",
        process_config_key=spec.process_config_key,
        base_model_repo_id=ls.BASE_MODEL_REPO_ID,
        base_model_revision_sha=ls.BASE_MODEL_REVISION,
        torch_version="2.13.0+cu126",
        torch_cuda_version="12.6",
        diffusers_version="0.39.0",
        peft_version="0.20.0",
        gpu_name="NVIDIA GeForce RTX 4060 Laptop GPU",
        dataset_version=spec.dataset_version,
        smoke_manifest_path=spec.smoke_manifest_path,
        smoke_kit_fingerprint="a8052f44",
        sample_order_sha256="deadbeef",
        style=spec.style,
        caption_strategy=spec.caption_strategy,
        item_count=12,
        width=spec.width,
        height=spec.height,
        source_transform=spec.source_transform,
        rank=spec.rank,
        alpha=spec.alpha,
        target_modules=spec.target_modules,
        learning_rate=spec.learning_rate,
        optimizer=spec.optimizer,
        optimizer_state_dtype=spec.optimizer_state_dtype,
        optimizer_steps_planned=spec.optimizer_steps_planned,
        batch_size=spec.batch_size,
        grad_accum=spec.grad_accum,
        effective_batch_size=spec.effective_batch_size,
        text_encoder_trained=spec.text_encoder_trained,
        vae_trained=spec.vae_trained,
        gradient_checkpointing=spec.gradient_checkpointing,
        latent_caching=spec.latent_caching,
        precision=spec.precision,
        attention_impl=spec.attention_impl,
        seed=spec.seed,
        memory_tier=spec.memory_tier,
        gates=_passing_gates(),
        gates_passed=True,
    )
    base.update(overrides)
    return ls.TrainingResultRow(**base)


def test_jsonl_round_trip(tmp_path):
    rows = [_row(), _row(exp_id="EXP-017", width=512, height=1536)]
    path = ls.write_jsonl(rows, tmp_path / "results.jsonl")
    read = ls.read_jsonl(path)
    assert len(read) == 2
    assert read[0]["exp_id"] == "EXP-016"
    assert read[1]["height"] == 1536
    assert read[0]["gates"]["trainable_lora_parameters"] == 797184


def test_append_jsonl_survives_partial_runs(tmp_path):
    path = tmp_path / "results.jsonl"
    ls.append_jsonl(_row(), path)
    ls.append_jsonl(_row(exp_id="EXP-017"), path)
    assert len(ls.read_jsonl(path)) == 2


def test_csv_flattens_nested_records(tmp_path):
    path = ls.write_csv([_row()], tmp_path / "results.csv")
    header = path.read_text(encoding="utf-8").splitlines()[0]
    assert "gates_trainable_lora_parameters" in header
    assert "resources_process_peak_device_used_mb" in header
    assert "adapter_lora_key_count" in header


def test_csv_refuses_to_write_nothing(tmp_path):
    with pytest.raises(ValueError, match="empty result CSV"):
        ls.write_csv([], tmp_path / "empty.csv")


def test_unmeasured_resources_serialise_as_not_measured():
    row = _row()
    assert row.resources.process_peak_device_used_mb == "not measured"
    payload = json.loads(json.dumps(ls.flatten(row)))
    assert payload["resources_process_peak_device_used_mb"] == "not measured"


# --- reporting ---------------------------------------------------------------


def test_summary_states_the_device_ceiling_and_spare_headroom():
    row = _row()
    row.resources.process_peak_device_used_mb = 7965.5
    row.resources.process_peak_allocated_mb = 5140.69
    md = ls.render_summary_markdown([row], "Prototype 3", device_total_mb=8187.5)
    assert "8187.5" in md
    assert "222.0" in md, "spare headroom must be computed and shown, not left implicit"
    assert "PASS" in md


def test_summary_reports_unmeasured_rather_than_zero():
    md = ls.render_summary_markdown([_row()], "Prototype 3", device_total_mb=8187.5)
    assert "not measured" in md


def test_summary_lists_gate_failures():
    row = _row(gates_passed=False, gate_failures="gradients non-zero")
    md = ls.render_summary_markdown([row], "Prototype 3", device_total_mb=8187.5)
    assert "Gate failures" in md
    assert "gradients non-zero" in md


# --- import boundary ---------------------------------------------------------


def test_lora_schema_imports_no_torch_or_evaluation_model():
    """Keeps the schema testable without a GPU, and keeps a metric encoder out of
    any process whose VRAM figures are being measured."""
    tree = ast.parse(Path(sys.modules[ls.__name__].__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    banned = {"torch", "diffusers", "transformers", "peft", "PIL", "accelerate"}
    assert not (imported & banned), f"lora_schema must not import {sorted(imported & banned)}"
