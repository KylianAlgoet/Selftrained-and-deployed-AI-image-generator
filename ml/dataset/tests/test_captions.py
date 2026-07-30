import pytest

from ml.dataset.captions import STYLE_PHRASES, build_caption


def test_builds_expected_template():
    caption = build_caption("ukiyo-e", "great wave crashing over boats")
    assert caption == "ukiyo-e woodblock print style skateboard decal artwork, great wave crashing over boats"


def test_normalizes_whitespace_and_trailing_dot():
    assert build_caption("retro-poster", "  bold  hero.  ").endswith("artwork, bold hero")


def test_retro_poster_phrase_matches_wpa_poster_evidence():
    """Guard against the 2026-07-30 relabel regressing to the inaccurate term."""
    assert build_caption("retro-poster", "a wolf head").startswith("retro silkscreen poster style")
    assert "comic" not in STYLE_PHRASES["retro-poster"]
    assert "retro-comic" not in STYLE_PHRASES


def test_unknown_style_raises():
    with pytest.raises(ValueError, match="unknown style"):
        build_caption("graffiti", "tag")


def test_empty_content_raises():
    with pytest.raises(ValueError, match="content phrase"):
        build_caption("minimal-geometric", "   ")
