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


# --- M8: the filename is a label, and this proves it ------------------------
#
# The rules above already establish WHAT is accepted. This section establishes
# something narrower and more important: that a hostile *filename* has no
# mechanism to act, because `validate_reference_upload` never touches the
# filesystem at all. The earlier traversal test asserts an empty tmp_path, which
# only shows nothing landed in ONE directory. These assert the stronger property.


HOSTILE_FILENAMES = [
    pytest.param("../../../../etc/passwd.png", id="posix-traversal"),
    pytest.param("..\\..\\..\\windows\\win.ini.png", id="windows-traversal"),
    pytest.param("C:\\Windows\\System32\\config.png", id="absolute-windows"),
    pytest.param("/etc/shadow.png", id="absolute-posix"),
    pytest.param("\\\\server\\share\\evil.png", id="unc-path"),
    pytest.param(
        "outputs/lora/EXP-027__style-full/step00300/pytorch_lora_weights.png",
        id="looks-like-a-checkpoint-path",
    ),
    pytest.param("ref\x00.png", id="null-byte"),
    pytest.param("ref\r\n.png", id="control-characters"),
    pytest.param("\u202eevil\u202c.png", id="rtl-override"),
    pytest.param("decal-\U0001f6f9-\u65e5\u672c\u8a9e.png", id="emoji-and-cjk"),
    pytest.param("a" * 300 + ".png", id="overlong"),
    pytest.param(".png", id="extension-only"),
]


@pytest.fixture
def no_filesystem(monkeypatch):
    """Make ANY filesystem access during validation an immediate failure.

    This is the whole point of the section. Asserting that a traversal filename
    did not create a file in one temporary directory proves very little - the
    interesting question is whether the name can reach an OS call anywhere.
    Patching the three entry points it would have to go through turns "the
    filename is discarded" from a claim in a docstring into something the test
    suite can fail on.
    """
    import builtins
    import pathlib

    def forbidden(*args, **kwargs):  # pragma: no cover - only runs on a failure
        raise AssertionError(f"upload validation touched the filesystem: {args!r}")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(pathlib.Path, "open", forbidden)
    monkeypatch.setattr(pathlib.Path, "write_bytes", forbidden)
    monkeypatch.setattr(pathlib.Path, "mkdir", forbidden)


@pytest.mark.parametrize("filename", HOSTILE_FILENAMES)
def test_a_hostile_filename_never_reaches_the_filesystem(filename, png_bytes, no_filesystem):
    """Accepted or rejected, the name is only ever read for its extension."""
    try:
        image = validate_reference_upload(filename, "image/png", png_bytes)
    except UploadRejected:
        return  # rejected without an OS call, which is also a pass
    assert image.size == (64, 64)


def test_the_no_filesystem_guard_is_actually_sensitive(tmp_path, no_filesystem):
    """The guard above is only evidence if it can fail. Prove it can.

    A patched-out check that silently permits everything passes just as happily
    as a real one, and the hash-lock tests in this project carry the same
    companion assertion for the same reason.
    """
    with pytest.raises(AssertionError, match="touched the filesystem"):
        (tmp_path / "should-not-happen.txt").write_bytes(b"x")


def test_a_filename_with_no_extension_is_rejected(png_bytes):
    with pytest.raises(UploadRejected):
        validate_reference_upload("passwd", "image/png", png_bytes)


def test_a_missing_filename_is_rejected_by_the_extension_rule(png_bytes):
    with pytest.raises(UploadRejected):
        validate_reference_upload(None, "image/png", png_bytes)


@pytest.mark.parametrize("filename", ["REF.PNG", "ref.PnG", "photo.JPEG", "art.WebP"])
def test_uppercase_and_mixed_case_extensions_are_accepted(filename):
    """A rule that only worked in lowercase would reject perfectly valid files."""
    fmt = "PNG" if filename.lower().endswith("png") else (
        "JPEG" if "jpeg" in filename.lower() else "WEBP"
    )
    content_type = f"image/{fmt.lower()}"
    assert validate_reference_upload(filename, content_type, _image_bytes(fmt)).mode == "RGB"


def test_only_the_last_extension_decides(png_bytes):
    """Asserted in both directions, so the `rpartition` semantics are deliberate."""
    with pytest.raises(UploadRejected):
        validate_reference_upload("decal.png.exe", "image/png", png_bytes)
    assert validate_reference_upload("decal.exe.png", "image/png", png_bytes).mode == "RGB"


@pytest.mark.parametrize(
    "content_type",
    ["image/png; charset=binary", "image/png;charset=utf-8", "IMAGE/PNG", " image/png "],
)
def test_a_content_type_with_parameters_or_casing_is_normalised(content_type, png_bytes):
    assert validate_reference_upload("ref.png", content_type, png_bytes).mode == "RGB"


def test_a_valid_webp_is_accepted():
    """The third allowed format had no positive test until M8."""
    assert validate_reference_upload("ref.webp", "image/webp", _image_bytes("WEBP")).mode == "RGB"


def test_an_absent_content_type_falls_through_to_the_decode(png_bytes):
    """A missing header is not a rejection reason - the bytes still decide."""
    assert validate_reference_upload("ref.png", None, png_bytes).mode == "RGB"


def test_the_upload_is_closed_on_every_path():
    """Structural, because the close happens on a path no HTTP test can observe.

    The endpoint reads the upload inside a `try` and closes it in `finally`, so a
    rejected upload releases its temporary storage exactly like an accepted one.
    Parsed rather than text-scanned, following the import-boundary precedent: a
    comment saying "closed on every path" is not evidence, and a future edit that
    moved the close into the success branch would leave a temp file behind on
    every rejection while every existing test still passed.
    """
    import ast
    from pathlib import Path as _Path

    source = (_Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    tries = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Try)]

    upload_try = [
        node
        for node in tries
        if any(
            isinstance(h.type, ast.Name) and h.type.id == "UploadRejected"
            for h in node.handlers
        )
    ]
    assert len(upload_try) == 1, "expected exactly one UploadRejected handler"

    finalbody = upload_try[0].finalbody
    assert finalbody, "the upload must be closed in a finally block, not in the success path"
    closes = [
        node
        for node in ast.walk(ast.Module(body=finalbody, type_ignores=[]))
        if isinstance(node, ast.Attribute) and node.attr == "close"
    ]
    assert closes, "no .close() call found in the finally block"


# --- M8: endpoint-level provenance -------------------------------------------


def test_the_users_filename_never_appears_in_the_response_or_on_disk(
    client, service, png_bytes
):
    """The name is not echoed back and does not become a stored filename."""
    secret_name = "kylian-private-photo-2026.png"
    response = client.post(
        "/api/generate",
        data={"prompt": "a fox", "style": "ukiyo-e"},
        files={"reference_image": (secret_name, png_bytes, "image/png")},
    )
    assert response.status_code == 200
    assert "kylian-private-photo" not in response.text

    stored = list(service.settings.generated_dir.iterdir())
    assert stored, "the generation should have written exactly one PNG"
    assert all("kylian-private-photo" not in path.name for path in stored)


def test_two_uploads_with_the_same_filename_do_not_collide(client, service, png_bytes):
    """Nothing is keyed by a user-supplied name, so a repeat cannot overwrite."""
    ids = []
    for _ in range(2):
        response = client.post(
            "/api/generate",
            data={"prompt": "a fox", "style": "ukiyo-e"},
            files={"reference_image": ("same-name.png", png_bytes, "image/png")},
        )
        assert response.status_code == 200
        ids.append(response.json()["generation_id"])

    assert ids[0] != ids[1]
    assert len(list(service.settings.generated_dir.iterdir())) == 2


def test_a_generation_is_written_only_inside_the_configured_output_dir(
    client, service, png_bytes
):
    """The positive half of the traversal claim: output stays where it belongs."""
    response = client.post(
        "/api/generate",
        data={"prompt": "a fox", "style": "ukiyo-e"},
        files={"reference_image": ("ref.png", png_bytes, "image/png")},
    )
    generation_id = response.json()["generation_id"]
    path = service.resolve(generation_id)

    assert path is not None
    assert path.parent == service.settings.generated_dir
    assert path.name == f"{generation_id}.png"
