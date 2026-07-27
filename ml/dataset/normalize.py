"""Preprocessing: resize originals into the training working set.

Originals in data/raw/ are never modified; normalized copies go to
data/processed/ (git-ignored). Short side is scaled to the target size with
Lanczos resampling, aspect ratio preserved. Cropping strategy (square crops
vs. aspect buckets) is decided with the training pipeline in Prototype 3.
"""

from pathlib import Path

from PIL import Image

TARGET_SHORT_SIDE = 512


def normalize_image(src: str | Path, dst: str | Path, target_short_side: int = TARGET_SHORT_SIDE) -> tuple[int, int]:
    """Resize so the short side equals target (never upscales). Returns new size."""
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = img.convert("RGB")
        width, height = img.size
        scale = target_short_side / min(width, height)
        if scale < 1:
            img = img.resize((round(width * scale), round(height * scale)), Image.LANCZOS)
        img.save(dst, "PNG")
        return img.size
