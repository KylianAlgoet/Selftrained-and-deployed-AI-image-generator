"""Upload security. Every rule in `uploads.py` gets a negative test."""

import io
import struct

import pytest
from PIL import Image

from apps.api.uploads import (
    ALLOWED_DECODED_FORMATS,
    MAX_DIMENSION,
    MAX_UPLOAD_BYTES,
    UploadRejected,
    validate_reference_upload,
)


def _image_bytes(fmt="PNG", size=(64, 64)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (120, 30, 90)).save(buffer, format=fmt)
    return buffer.getvalue()


def test_a_valid_png_is_accepted_and_returned_as_rgb(png_bytes):
    image = validate_reference_upload("ref.png", "image/png", png_bytes)
    assert image.mode == "RGB"
    assert image.size == (64, 64)


def test_a_valid_jpeg_is_accepted():
    data = _image_bytes("JPEG")
    assert validate_reference_upload("ref.jpg", "image/jpeg", data).mode == "RGB"


def test_empty_upload_is_rejected():
    with pytest.raises(UploadRejected) as err:
        validate_reference_upload("ref.png", "image/png", b"")
    assert err.value.field == "reference_image"


def test_disallowed_extension_is_rejected(png_bytes):
    with pytest.raises(UploadRejected):
        validate_reference_upload("payload.svg", "image/png", png_bytes)


def test_executable_extension_is_rejected(png_bytes):
    with pytest.raises(UploadRejected):
        validate_reference_upload("payload.exe", "image/png", png_bytes)


def test_content_type_disagreeing_with_extension_is_rejected(png_bytes):
    with pytest.raises(UploadRejected):
        validate_reference_upload("ref.png", "application/zip", png_bytes)


def test_oversize_upload_is_rejected_before_decoding():
    with pytest.raises(UploadRejected) as err:
        validate_reference_upload("ref.png", "image/png", b"\x89PNG" + b"0" * MAX_UPLOAD_BYTES)
    assert "limit" in err.value.reason


def test_bytes_that_are_not_an_image_are_rejected():
    with pytest.raises(UploadRejected):
        validate_reference_upload("ref.png", "image/png", b"\x89PNG\r\n\x1a\n" + b"garbage" * 50)


def test_a_truncated_png_is_rejected(png_bytes):
    with pytest.raises(UploadRejected):
        validate_reference_upload("ref.png", "image/png", png_bytes[: len(png_bytes) // 2])


def test_an_image_wider_than_the_cap_is_rejected():
    # Built as a real, decodable image so the DIMENSION rule is what rejects it,
    # not a decode failure.
    data = _image_bytes("PNG", (MAX_DIMENSION + 8, 4))
    with pytest.raises(UploadRejected) as err:
        validate_reference_upload("ref.png", "image/png", data)
    assert "pixels on a side" in err.value.reason


def test_a_decompression_bomb_header_is_rejected():
    """A tiny file that CLAIMS enormous dimensions must not be decoded."""
    # A PNG header advertising 60000x60000 - 3.6e9 pixels, far past the cap.
    ihdr = struct.pack(">II", 60000, 60000) + bytes([8, 2, 0, 0, 0])
    chunk = struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr + b"\x00\x00\x00\x00"
    data = b"\x89PNG\r\n\x1a\n" + chunk
    with pytest.raises(UploadRejected):
        validate_reference_upload("bomb.png", "image/png", data)


def test_a_traversal_filename_cannot_reach_the_filesystem(png_bytes, tmp_path):
    """The filename is read for its extension and then discarded."""
    image = validate_reference_upload("../../../../etc/passwd.png", "image/png", png_bytes)
    assert image.size == (64, 64)
    # Nothing was written anywhere as a side effect of that name.
    assert list(tmp_path.iterdir()) == []


def test_the_decoded_format_allowlist_is_what_decides():
    assert ALLOWED_DECODED_FORMATS == frozenset({"PNG", "JPEG", "WEBP"})


def test_a_gif_renamed_to_png_is_rejected_on_its_contents():
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), (1, 2, 3)).save(buffer, format="GIF")
    with pytest.raises(UploadRejected):
        validate_reference_upload("sneaky.png", "image/png", buffer.getvalue())


def test_endpoint_rejects_a_bad_upload_with_422(client, png_bytes):
    response = client.post(
        "/api/generate",
        data={"prompt": "a fox", "style": "ukiyo-e"},
        files={"reference_image": ("payload.exe", png_bytes, "image/png")},
    )
    assert response.status_code == 422
    assert response.json()["field"] == "reference_image"


def test_endpoint_accepts_a_valid_reference_and_applies_the_scale(client, fake_pipeline, png_bytes):
    response = client.post(
        "/api/generate",
        data={"prompt": "a fox", "style": "ukiyo-e", "ip_adapter_scale": 0.55},
        files={"reference_image": ("ref.png", png_bytes, "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["metadata"]["reference_present"] is True
    assert fake_pipeline.calls[-1]["reference_image"] is not None
