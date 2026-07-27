import shutil

from PIL import Image, ImageEnhance

from ml.dataset.hashing import (
    dhash_file,
    find_exact_duplicates,
    find_near_duplicates,
    sha256_file,
)
from ml.dataset.tests.conftest import make_image


def test_sha256_stable_and_copy_sensitive(tmp_path, valid_png):
    copy = tmp_path / "copy.png"
    shutil.copy(valid_png, copy)
    assert sha256_file(valid_png) == sha256_file(copy)
    other = make_image(tmp_path / "other.png", color=(10, 200, 10))
    assert sha256_file(valid_png) != sha256_file(other)


def test_find_exact_duplicates_groups_only_shared_hashes():
    groups = find_exact_duplicates({"a": "h1", "b": "h1", "c": "h2", "d": "h1"})
    assert groups == [["a", "b", "d"]]
    assert find_exact_duplicates({"a": "h1", "b": "h2"}) == []


def test_near_duplicates_detects_brightness_variant(tmp_path, valid_png):
    variant = tmp_path / "variant.png"
    with Image.open(valid_png) as img:
        ImageEnhance.Brightness(img).enhance(1.08).save(variant, "PNG")
    distinct = make_image(tmp_path / "distinct.png", color=(5, 5, 5), size=(640, 640))

    hashes = {
        "orig": dhash_file(valid_png),
        "variant": dhash_file(variant),
        "distinct": dhash_file(distinct),
    }
    pairs = find_near_duplicates(hashes)
    assert ("orig", "variant") in [(a, b) for a, b, _ in pairs]
    involved = {name for a, b, _ in pairs for name in (a, b)}
    assert "distinct" not in involved
