from PIL import Image

from ml.dataset.contact_sheet import make_contact_sheet
from ml.dataset.normalize import normalize_image
from ml.dataset.stats import compute_stats, render_stats_markdown
from ml.dataset.tests.conftest import make_image, valid_row


def test_compute_stats_counts():
    rows = [
        valid_row(),
        valid_row(id="DS-0002", sha256="b" * 64, style="retro-comic", licence="public domain", split="val"),
        valid_row(id="DS-0003", sha256="c" * 64, style="retro-comic"),
    ]
    stats = compute_stats(rows)
    assert stats["total"] == 3
    assert stats["styles"] == {"ukiyo-e": 1, "retro-comic": 2}
    assert stats["licences"] == {"CC0": 2, "public domain": 1}
    assert stats["splits"] == {"train": 2, "val": 1}
    assert stats["min_short_side"] == 600


def test_render_stats_markdown_contains_tables():
    md = render_stats_markdown(compute_stats([valid_row()]))
    assert "| ukiyo-e | 1 |" in md
    assert "**Total items:** 1" in md


def test_normalize_downscales_short_side_to_target(tmp_path):
    big = make_image(tmp_path / "big.png", size=(1200, 2400))
    out_big = tmp_path / "out_big.png"
    assert normalize_image(big, out_big) == (512, 1024)


def test_normalize_never_upscales(tmp_path):
    small = make_image(tmp_path / "smallish.png", size=(400, 800))
    out = tmp_path / "out_small.png"
    assert normalize_image(small, out) == (400, 800)


def test_contact_sheet_grid_dimensions(tmp_path):
    paths = [make_image(tmp_path / f"img{i}.png", size=(300, 300), color=(i * 12, 80, 120)) for i in range(10)]
    sheet_path = make_contact_sheet(paths, tmp_path / "sheet.jpg", thumb_size=64, columns=4)
    with Image.open(sheet_path) as sheet:
        assert sheet.size == (4 * 64, 3 * 64)  # 10 images in 4 columns -> 3 rows
