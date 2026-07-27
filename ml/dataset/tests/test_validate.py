from ml.dataset.validate import validate_image


def test_accepts_valid_png(valid_png):
    result = validate_image(valid_png)
    assert result.ok
    assert result.format == "PNG"
    assert (result.width, result.height) == (600, 700)


def test_accepts_valid_jpeg(valid_jpeg):
    assert validate_image(valid_jpeg).ok


def test_rejects_below_minimum_resolution(small_png):
    result = validate_image(small_png)
    assert not result.ok
    assert "short side" in result.reason


def test_rejects_corrupt_file(corrupt_png):
    result = validate_image(corrupt_png)
    assert not result.ok
    assert "decode failed" in result.reason


def test_rejects_truncated_file(truncated_png):
    assert not validate_image(truncated_png).ok


def test_rejects_disallowed_format(tmp_path, valid_png):
    from PIL import Image

    gif = tmp_path / "anim.gif"
    with Image.open(valid_png) as img:
        img.save(gif, "GIF")
    result = validate_image(gif)
    assert not result.ok
    assert "not allowed" in result.reason


def test_custom_minimum_can_pass(small_png):
    assert validate_image(small_png, min_short_side=50).ok
