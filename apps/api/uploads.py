"""Reference-image upload validation. Every upload is untrusted input.

The limits are frozen here, in code, ahead of the implementation that uses them,
so "we validate uploads" is a specific claim rather than a general one.

The ordering matters and is deliberate: cheap checks reject obvious junk before
anything expensive touches it, but the DECODE is what actually decides. An
extension and a Content-Type header are both attacker-controlled strings; the
only trustworthy statement about a byte stream is what happens when a decoder
reads it.
"""

import io

from PIL import Image, UnidentifiedImageError

# --- Frozen limits -----------------------------------------------------------

ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"png", "jpg", "jpeg", "webp"})
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {"image/png", "image/jpeg", "image/webp"}
)
# What the decoder must report. This is the authoritative allowlist.
ALLOWED_DECODED_FORMATS: frozenset[str] = frozenset({"PNG", "JPEG", "WEBP"})

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # matches MAX_UPLOAD_SIZE_MB=10

# 4096 px per side. The project's own ukiyo-e sources reach about 4000 px, so a
# lower cap would reject exactly the material this tool is meant to accept.
MAX_DIMENSION = 4096
MAX_TOTAL_PIXELS = MAX_DIMENSION * MAX_DIMENSION  # 16 777 216

# Pillow's own decompression-bomb guard, aligned with the cap above rather than
# left at the library default.
Image.MAX_IMAGE_PIXELS = MAX_TOTAL_PIXELS


class UploadRejected(Exception):
    """A rejection with a message that is safe to return to the browser.

    `reason` never contains a filesystem path, a stack trace or a library
    message - those go to the server log, not to the client.
    """

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(f"{field}: {reason}")
        self.field = field
        self.reason = reason


def _extension_of(filename: str) -> str:
    # rsplit on the LAST dot only, and never treat this as a path. A user
    # filename is a label; it must not reach the filesystem in any form, so it is
    # not sanitised for reuse - it is read for its extension and discarded.
    _, _, ext = filename.rpartition(".")
    return ext.lower().strip()


def validate_reference_upload(
    filename: str | None,
    content_type: str | None,
    data: bytes,
) -> Image.Image:
    """Validate an uploaded reference and return a decoded RGB image.

    Raises `UploadRejected` with a safe message. The returned image is fully
    loaded into memory and detached from the input buffer, so the caller can
    drop the bytes immediately.
    """
    if not data:
        raise UploadRejected("reference_image", "the uploaded file is empty")

    if len(data) > MAX_UPLOAD_BYTES:
        limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise UploadRejected(
            "reference_image", f"the image is larger than the {limit_mb} MB limit"
        )

    extension = _extension_of(filename or "")
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise UploadRejected(
            "reference_image", f"unsupported file type; allowed types are {allowed}"
        )

    if content_type and content_type.split(";")[0].strip().lower() not in ALLOWED_CONTENT_TYPES:
        raise UploadRejected(
            "reference_image", "the file type and its content type do not agree"
        )

    # Decode validation, in two passes. `verify()` detects a corrupt or truncated
    # stream but leaves the image unusable afterwards, which is why the bytes are
    # opened a second time for the real read.
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
    except Image.DecompressionBombError:
        raise UploadRejected(
            "reference_image", "the image dimensions are unreasonably large"
        ) from None
    except (UnidentifiedImageError, OSError, ValueError):
        raise UploadRejected(
            "reference_image", "the file could not be read as an image"
        ) from None

    try:
        with Image.open(io.BytesIO(data)) as opened:
            decoded_format = (opened.format or "").upper()
            width, height = opened.size

            if decoded_format not in ALLOWED_DECODED_FORMATS:
                raise UploadRejected(
                    "reference_image",
                    "the file contents are not a supported image format",
                )
            if width > MAX_DIMENSION or height > MAX_DIMENSION:
                raise UploadRejected(
                    "reference_image",
                    f"the image is larger than {MAX_DIMENSION} pixels on a side",
                )
            if width * height > MAX_TOTAL_PIXELS:
                raise UploadRejected(
                    "reference_image", "the image has too many pixels in total"
                )

            # `.copy()` after `.load()` detaches the pixels from the file object,
            # so the caller holds a normal in-memory image and the buffer can go.
            opened.load()
            return opened.convert("RGB").copy()
    except UploadRejected:
        raise
    except Image.DecompressionBombError:
        raise UploadRejected(
            "reference_image", "the image dimensions are unreasonably large"
        ) from None
    except (UnidentifiedImageError, OSError, ValueError):
        raise UploadRejected(
            "reference_image", "the file could not be read as an image"
        ) from None
