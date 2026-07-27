import pytest

from ml.dataset.captions import build_caption


def test_builds_expected_template():
    caption = build_caption("ukiyo-e", "great wave crashing over boats")
    assert caption == "ukiyo-e woodblock print style skateboard decal artwork, great wave crashing over boats"


def test_normalizes_whitespace_and_trailing_dot():
    assert build_caption("retro-comic", "  bold  hero.  ").endswith("artwork, bold hero")


def test_unknown_style_raises():
    with pytest.raises(ValueError, match="unknown style"):
        build_caption("graffiti", "tag")


def test_empty_content_raises():
    with pytest.raises(ValueError, match="content phrase"):
        build_caption("minimal-geometric", "   ")
