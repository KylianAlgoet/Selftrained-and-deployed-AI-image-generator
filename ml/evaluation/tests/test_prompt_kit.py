"""Guards for the frozen evaluation kit.

The fingerprint test is the important one: it is what makes "frozen" real. If a
prompt, seed, sampler setting, or the underlying caption template changes, this
test fails and forces a deliberate decision instead of silently invalidating
every cross-prototype comparison built on the kit.
"""

import pytest

from ml.evaluation import prompt_kit

# Recorded 2026-07-30 from the kit as first frozen in Prototype 1.
# Only update this together with a documented decision + process-log entry.
FROZEN_FINGERPRINT = "c40749bc100deea5cc5854e40ba34928dcf3fdda31ff3c41840dafdfba1f5228"


def test_kit_fingerprint_is_frozen():
    assert prompt_kit.kit_fingerprint() == FROZEN_FINGERPRINT, (
        "The frozen evaluation kit changed. This invalidates comparability with every "
        "earlier experiment. If the change is intended, record a decision and process-log "
        "entry, then update FROZEN_FINGERPRINT deliberately."
    )


def test_fingerprint_is_sensitive_to_change(monkeypatch):
    """A fingerprint that never changes would be a useless lock."""
    monkeypatch.setattr(prompt_kit, "STEPS", prompt_kit.STEPS + 1)
    assert prompt_kit.kit_fingerprint() != FROZEN_FINGERPRINT


def test_frozen_settings_have_expected_values():
    assert prompt_kit.SEEDS == (42, 1337, 2026)
    assert prompt_kit.STEPS == 30
    assert prompt_kit.GUIDANCE_SCALE == 7.5
    assert prompt_kit.TRACK_A_RESOLUTION == (512, 512)
    assert len(prompt_kit.PROMPTS) == 5


def test_prompt_ids_are_unique():
    ids = [prompt.id for prompt in prompt_kit.PROMPTS]
    assert len(ids) == len(set(ids))


def test_style_prompts_use_the_dataset_caption_template():
    """Coupling the kit to the training caption template is intentional."""
    assert prompt_kit.prompt_by_id("P1-poster").text.startswith("retro silkscreen poster style")
    assert prompt_kit.prompt_by_id("P2-geo").text.startswith("minimal geometric abstract style")
    assert prompt_kit.prompt_by_id("P3-ukiyo").text.startswith("ukiyo-e woodblock print style")
    for prompt_id in ("P1-poster", "P2-geo", "P3-ukiyo", "P4-deck"):
        assert "skateboard decal artwork," in prompt_kit.prompt_by_id(prompt_id).text


def test_control_prompt_carries_no_style_phrase():
    control = prompt_kit.prompt_by_id("P5-control").text
    assert control == "skateboard decal artwork, a flaming skull"
    for phrase in ("silkscreen", "geometric", "ukiyo-e"):
        assert phrase not in control


def test_no_prompt_reintroduces_the_retracted_comic_label():
    """Regression guard tied to the 2026-07-30 style relabel."""
    for prompt in prompt_kit.PROMPTS:
        assert "comic" not in prompt.text.lower()
        assert "halftone" not in prompt.text.lower()


def test_unknown_prompt_id_raises():
    with pytest.raises(KeyError, match="unknown prompt id"):
        prompt_kit.prompt_by_id("P9-nope")


def test_text_sha256_is_stable_and_distinct():
    first = prompt_kit.text_sha256("abc")
    assert first == prompt_kit.text_sha256("abc")
    assert first != prompt_kit.text_sha256("abd")
    assert len(first) == 64
