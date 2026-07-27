"""Template captioning for training items.

Captions pair a human-readable style phrase with a short content phrase.
Final trigger-token design for LoRA training is decided in Prototypes 3-4;
these templates are the M2 baseline and are manually reviewed per item.
"""

STYLE_PHRASES = {
    "retro-comic": "retro comic poster style",
    "minimal-geometric": "minimal geometric abstract style",
    "ukiyo-e": "ukiyo-e woodblock print style",
}


def build_caption(style: str, content_phrase: str) -> str:
    if style not in STYLE_PHRASES:
        raise ValueError(f"unknown style {style!r}; expected one of {sorted(STYLE_PHRASES)}")
    content = " ".join(content_phrase.split()).strip().rstrip(".")
    if not content:
        raise ValueError("content phrase must not be empty")
    return f"{STYLE_PHRASES[style]} skateboard decal artwork, {content}"
