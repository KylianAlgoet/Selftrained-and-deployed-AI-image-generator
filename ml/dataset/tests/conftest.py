import pytest
from PIL import Image, ImageDraw


def make_image(path, size=(600, 700), color=(200, 60, 40), fmt="PNG", detail=True):
    img = Image.new("RGB", size, color)
    if detail:
        draw = ImageDraw.Draw(img)
        draw.ellipse([size[0] // 4, size[1] // 4, 3 * size[0] // 4, 3 * size[1] // 4], fill=(30, 30, 80))
        draw.rectangle([10, 10, size[0] // 3, size[1] // 5], fill=(240, 220, 90))
    img.save(path, fmt)
    return path


@pytest.fixture
def valid_png(tmp_path):
    return make_image(tmp_path / "valid.png")


@pytest.fixture
def valid_jpeg(tmp_path):
    return make_image(tmp_path / "valid.jpg", fmt="JPEG")


@pytest.fixture
def small_png(tmp_path):
    return make_image(tmp_path / "small.png", size=(100, 900))


@pytest.fixture
def corrupt_png(tmp_path):
    path = tmp_path / "corrupt.png"
    path.write_bytes(b"this is not an image at all" * 10)
    return path


@pytest.fixture
def truncated_png(tmp_path, valid_png):
    data = valid_png.read_bytes()
    path = tmp_path / "truncated.png"
    path.write_bytes(data[: len(data) // 3])
    return path


def valid_row(**overrides):
    row = {
        "id": "DS-0001",
        "filename": "valid.png",
        "style": "ukiyo-e",
        "caption": "ukiyo-e woodblock skateboard decal artwork, great wave",
        "source": "https://example.org/item/1",
        "author": "Hokusai",
        "licence": "CC0",
        "collection_date": "2026-07-27",
        "permitted_use": "unrestricted, including ML training",
        "width": "600",
        "height": "700",
        "sha256": "a" * 64,
        "split": "train",
        "notes": "",
    }
    row.update(overrides)
    return row
