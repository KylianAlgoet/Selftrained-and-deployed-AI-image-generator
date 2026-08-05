"""The production style table and the checkpoint integrity gate.

These assertions are what stop the service from quietly drifting away from what
gate 2 approved: the styles, their checkpoints, the prompt form and the default
weight all have to keep matching the recorded decision.
"""

import hashlib

import pytest

from apps.api.styles import (
    DEFAULT_IP_ADAPTER_SCALE,
    DEFAULT_LORA_WEIGHT,
    PRODUCTION_STYLES,
    STYLE_KEYS,
    CheckpointUnavailable,
    build_prompt,
    production_style,
    verify_checkpoint,
)
from ml.dataset.captions import STYLE_PHRASES
from ml.training.style_kit import style_by_key


def test_the_three_gate_2_selections_are_recorded_exactly():
    selected = {
        (s.key, s.run_id, s.checkpoint_step, s.outcome) for s in PRODUCTION_STYLES
    }
    assert selected == {
        ("minimal-geometric", "EXP-027", 300, "PASS"),
        ("ukiyo-e", "EXP-028", 600, "PASS"),
        ("retro-poster", "EXP-029", 300, "PARTIAL PASS"),
    }


def test_two_of_the_three_are_step_300_not_600():
    """The finding is load-bearing, so a silent change to 600 must fail a test."""
    steps = {s.key: s.checkpoint_step for s in PRODUCTION_STYLES}
    assert steps["minimal-geometric"] == 300
    assert steps["retro-poster"] == 300
    assert steps["ukiyo-e"] == 600


def test_retro_poster_ships_as_a_partial_pass_with_its_limitation_stated():
    style = production_style("retro-poster")
    assert style.is_partial_pass
    assert "pseudo-text" in style.limitation
    assert "border" in style.limitation.lower()


def test_the_renamed_style_never_reappears():
    assert "retro-comic" not in STYLE_KEYS


def test_defaults_match_the_decision_records():
    assert DEFAULT_LORA_WEIGHT == 0.7        # DR-010
    assert DEFAULT_IP_ADAPTER_SCALE == 0.55  # DR-008


def test_every_style_declares_the_same_adapter_size():
    assert {s.size_bytes for s in PRODUCTION_STYLES} == {6414480}


def test_recorded_hashes_are_wellformed_and_distinct():
    hashes = [s.sha256 for s in PRODUCTION_STYLES]
    assert len(set(hashes)) == 3
    for value in hashes:
        assert len(value) == 64
        assert set(value) <= set("0123456789abcdef")


def test_triggers_and_phrases_come_from_the_frozen_kits():
    for style in PRODUCTION_STYLES:
        assert style.trigger == style_by_key(style.key).trigger
        assert style.phrase == STYLE_PHRASES[style.key]


def test_prompt_form_matches_the_scored_matrix():
    """`<trigger> <phrase> skateboard decal artwork, <subject>` - as EXP-031 built it."""
    assert build_prompt("minimal-geometric", "a coiled serpent") == (
        "xgeo minimal geometric abstract style skateboard decal artwork, a coiled serpent"
    )
    assert build_prompt("ukiyo-e", "a mountain and a rising sun") == (
        "xkyo ukiyo-e woodblock print style skateboard decal artwork, "
        "a mountain and a rising sun"
    )
    assert build_prompt("retro-poster", "a coiled serpent") == (
        "xpst retro silkscreen poster style skateboard decal artwork, a coiled serpent"
    )


def test_prompt_normalises_whitespace_and_a_trailing_period():
    assert build_prompt("ukiyo-e", "  a   fox.  ").endswith("artwork, a fox")


def test_an_empty_subject_is_refused():
    with pytest.raises(ValueError):
        build_prompt("ukiyo-e", "   ")


# --- the integrity gate ------------------------------------------------------


def _plant(tmp_path, style, payload: bytes):
    directory = style.adapter_dir(tmp_path)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "pytorch_lora_weights.safetensors").write_bytes(payload)


def test_a_missing_adapter_is_refused(tmp_path):
    with pytest.raises(CheckpointUnavailable) as err:
        verify_checkpoint(production_style("ukiyo-e"), tmp_path)
    assert "missing" in str(err.value)


def test_a_wrong_size_adapter_is_refused(tmp_path):
    style = production_style("ukiyo-e")
    _plant(tmp_path, style, b"too short")
    with pytest.raises(CheckpointUnavailable) as err:
        verify_checkpoint(style, tmp_path)
    assert "bytes" in str(err.value)


def test_a_correct_size_but_wrong_content_adapter_is_refused(tmp_path):
    """The size check alone must not be able to pass a substituted file."""
    style = production_style("ukiyo-e")
    _plant(tmp_path, style, b"\x00" * style.size_bytes)
    with pytest.raises(CheckpointUnavailable) as err:
        verify_checkpoint(style, tmp_path)
    assert "sha256" in str(err.value)


def test_a_matching_adapter_is_accepted(tmp_path):
    """Uses a synthetic file whose hash is asserted, not a real checkpoint copy."""
    style = production_style("ukiyo-e")
    payload = b"\x01" * style.size_bytes
    digest = hashlib.sha256(payload).hexdigest()
    substitute = type(style)(
        key=style.key,
        label=style.label,
        run_id=style.run_id,
        checkpoint_step=style.checkpoint_step,
        run_dir=style.run_dir,
        sha256=digest,
        size_bytes=style.size_bytes,
        outcome=style.outcome,
        limitation=style.limitation,
    )
    _plant(tmp_path, substitute, payload)
    assert verify_checkpoint(substitute, tmp_path).is_file()
