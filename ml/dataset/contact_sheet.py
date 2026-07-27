"""Contact sheets: thumbnail grids per style for visual inspection and jury evidence."""

import math
from pathlib import Path

from PIL import Image

THUMB_SIZE = 128
COLUMNS = 8


def make_contact_sheet(
    image_paths: list[str | Path],
    out_path: str | Path,
    thumb_size: int = THUMB_SIZE,
    columns: int = COLUMNS,
) -> Path:
    if not image_paths:
        raise ValueError("no images given")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = math.ceil(len(image_paths) / columns)
    sheet = Image.new("RGB", (columns * thumb_size, rows * thumb_size), (245, 245, 245))
    for index, path in enumerate(image_paths):
        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((thumb_size, thumb_size), Image.LANCZOS)
            x = (index % columns) * thumb_size + (thumb_size - img.width) // 2
            y = (index // columns) * thumb_size + (thumb_size - img.height) // 2
            sheet.paste(img, (x, y))
    sheet.save(out_path, "JPEG", quality=80, optimize=True)
    return out_path
