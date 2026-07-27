"""Image validation: decodability, format allowlist, minimum resolution."""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

ALLOWED_FORMATS = {"PNG", "JPEG"}
MIN_SHORT_SIDE = 512


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    width: int
    height: int
    format: str
    reason: str

    @property
    def short_side(self) -> int:
        return min(self.width, self.height)


def validate_image(path: str | Path, min_short_side: int = MIN_SHORT_SIDE) -> ValidationResult:
    """Fully decode the image and check format and minimum resolution."""
    path = Path(path)
    try:
        with Image.open(path) as img:
            img_format = img.format or ""
            # load() forces a full decode, catching truncated/corrupt data
            # that a header-only open would miss.
            img.load()
            width, height = img.size
    except (UnidentifiedImageError, OSError, ValueError) as err:
        return ValidationResult(False, 0, 0, "", f"decode failed: {err}")

    if img_format not in ALLOWED_FORMATS:
        return ValidationResult(False, width, height, img_format, f"format {img_format!r} not allowed")
    if min(width, height) < min_short_side:
        return ValidationResult(
            False, width, height, img_format,
            f"short side {min(width, height)} below minimum {min_short_side}",
        )
    return ValidationResult(True, width, height, img_format, "")
