"""Upload validation for image translation.

Raster images (PNG, JPEG, WEBP), Photoshop documents (PSD/PSB, flattened to
their composite) and Illustrator artwork (a PDF-compatible .ai, kept vector)
are accepted.

Nothing the client says about the file is trusted: not its extension, not its
MIME type, not its metadata. The format is whatever Pillow's own content
sniffing decodes, the size limits are checked against the header before a
single pixel is decoded (a decompression bomb is a small file with a huge
header), and the whole image is then decoded once so a truncated or corrupt
file fails here rather than half-way through OCR.
"""

from __future__ import annotations

import io
import os
import re
import struct
import warnings
from dataclasses import dataclass

import fitz
from PIL import Image, features

# Pillow format name -> (canonical extension, MIME type, Pillow feature that
# must be compiled in to decode *and* encode it). Only formats the output can
# be written back in are accepted, so a translated image never comes back in a
# format the user did not send.
_FORMATS = {
    "PNG": (".png", "image/png", None),
    "JPEG": (".jpg", "image/jpeg", "jpg"),
    "WEBP": (".webp", "image/webp", "webp"),
}
_EXTENSIONS = {"PNG": [".png"], "JPEG": [".jpg", ".jpeg"], "WEBP": [".webp"],
               "AI": [".ai"], "PSD": [".psd", ".psb"]}

_MIN_SIDE = 16
# An artboard larger than this (points) is not a picture; Illustrator's own
# maximum canvas is 16383pt.
_MAX_ARTBOARD_PT = 16383
_MAX_ARTBOARDS = 20


def max_bytes() -> int:
    return int(os.getenv("BABEL_IMAGE_MAX_BYTES", str(20 * 1024 * 1024)))


def max_pixels() -> int:
    return int(os.getenv("BABEL_IMAGE_MAX_PIXELS", str(40_000_000)))


class ImageValidationError(ValueError):
    """A user-facing rejection — the message is safe to show as-is."""


@dataclass
class ImageInfo:
    format: str  # PNG | JPEG | WEBP | PSD | AI
    extension: str  # what the upload is stored as
    mime: str
    width: int  # pixels; points for AI
    height: int
    mode: str
    # "raster" runs the pixel pipeline; "vector" (AI) the live-text one.
    kind: str = "raster"
    # The output's extension. A PSD comes back as PNG: its layers cannot be
    # written back, and the composite is what was translated.
    output_extension: str = ""
    pages: int = 1


def psd_available() -> bool:
    try:
        import psd_tools  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    return True


def supported_formats() -> list[dict]:
    """Formats this server can actually decode and write back."""
    out = []
    for name, (_ext, mime, feature) in _FORMATS.items():
        if feature and not features.check(feature):
            continue
        out.append({"format": name, "mime": mime, "extensions": _EXTENSIONS[name]})
    out.append({"format": "AI", "mime": "application/illustrator", "extensions": _EXTENSIONS["AI"]})
    if psd_available():
        out.append({"format": "PSD", "mime": "image/vnd.adobe.photoshop",
                    "extensions": _EXTENSIONS["PSD"]})
    return out


def _validate_psd(data: bytes) -> ImageInfo:
    if not psd_available():
        raise ImageValidationError("Photoshop files are not supported on this server.")
    try:
        _sig, version, _res, _channels, height, width, _depth, _mode = \
            struct.unpack(">4sH6sHIIHH", data[:26])
    except struct.error:
        raise ImageValidationError("The Photoshop file is corrupt or truncated.") from None
    if version not in (1, 2):
        raise ImageValidationError("The Photoshop file is corrupt or truncated.")
    # From the header, before anything is decoded.
    _check_dimensions(width, height)
    try:
        from psd_tools import PSDImage

        PSDImage.open(io.BytesIO(data))
    except Exception:
        raise ImageValidationError("The Photoshop file is corrupt or truncated.") from None
    return ImageInfo(format="PSD", extension=".psb" if version == 2 else ".psd",
                     mime="image/vnd.adobe.photoshop", width=width, height=height,
                     mode="PSD", output_extension=".png")


def _is_illustrator(data: bytes, doc) -> bool:
    meta = doc.metadata or {}
    named = " ".join(str(meta.get(k) or "") for k in ("creator", "producer")).lower()
    return b"AIPrivateData" in data or b"Adobe Illustrator" in data or "illustrator" in named


def _validate_ai(data: bytes) -> ImageInfo:
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        raise ImageValidationError("The file is not a readable image.") from None
    try:
        if doc.needs_pass or doc.is_encrypted:
            raise ImageValidationError("The Illustrator file is password-protected.")
        if not _is_illustrator(data, doc):
            # A plain PDF belongs to the document pipeline, which reflows pages.
            raise ImageValidationError(
                "This is a PDF document, not Illustrator artwork - translate it under Documents.")
        if doc.page_count < 1:
            raise ImageValidationError("The Illustrator file has no artboard.")
        if doc.page_count > _MAX_ARTBOARDS:
            raise ImageValidationError(
                f"The Illustrator file has {doc.page_count} artboards; the limit is {_MAX_ARTBOARDS}.")
        rect = doc[0].rect
        if max(rect.width, rect.height) > _MAX_ARTBOARD_PT or min(rect.width, rect.height) < 1:
            raise ImageValidationError("The Illustrator artboard size is not supported.")
        pages = doc.page_count
    finally:
        doc.close()
    return ImageInfo(format="AI", extension=".ai", mime="application/illustrator",
                     width=round(rect.width), height=round(rect.height), mode="vector",
                     kind="vector", output_extension=".ai", pages=pages)


def _check_dimensions(width: int, height: int) -> None:
    if width < _MIN_SIDE or height < _MIN_SIDE:
        raise ImageValidationError(
            f"The image is too small ({width}×{height}px); "
            f"each side must be at least {_MIN_SIDE}px.")
    if width * height > max_pixels():
        raise ImageValidationError(
            f"The image has too many pixels ({width}×{height}); "
            f"the limit is {max_pixels() / 1e6:.0f} megapixels.")


def safe_filename(name: str) -> str:
    """A basename with no path, no control characters and nothing a header or
    a filesystem would choke on. Path traversal ends here: `../../x.png`
    becomes `x.png`."""
    base = os.path.basename((name or "").replace("\\", "/"))
    base = re.sub(r"[^\w.\- ]", "_", base).strip(" .")
    return base[:120] or "image"


def validate_image_bytes(data: bytes) -> ImageInfo:
    if not data:
        raise ImageValidationError("The file is empty.")
    limit = max_bytes()
    if len(data) > limit:
        raise ImageValidationError(
            f"The image is too large ({len(data) / 1_048_576:.1f} MB); "
            f"the limit is {limit / 1_048_576:.0f} MB.")

    # Format by signature, never by name.
    if data[:4] == b"8BPS":
        return _validate_psd(data)
    if data[:5] == b"%PDF-":
        return _validate_ai(data)
    if data[:11] == b"%!PS-Adobe-" and b"Illustrator" in data[:4096]:
        raise ImageValidationError(
            "This Illustrator file was saved without PDF compatibility. Re-save it "
            "with 'Create PDF Compatible File' turned on and upload it again.")

    allowed = {f["format"] for f in supported_formats()}
    try:
        with Image.open(io.BytesIO(data)) as probe:
            fmt = probe.format
            width, height = probe.size
            frames = getattr(probe, "n_frames", 1)
    except Exception:
        raise ImageValidationError("The file is not a readable image.") from None

    if fmt not in allowed:
        names = ", ".join(sorted(allowed))
        raise ImageValidationError(f"Unsupported image format; upload {names}.")
    if frames > 1:
        raise ImageValidationError("Animated images are not supported.")
    _check_dimensions(width, height)

    # Decode every pixel now. A truncated file opens fine (only the header is
    # read) and fails later, so this is the check that actually catches it.
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as img:
                img.load()
                mode = img.mode
    except Exception:
        raise ImageValidationError("The image is corrupt or truncated.") from None

    ext, mime, _ = _FORMATS[fmt]
    return ImageInfo(format=fmt, extension=ext, mime=mime,
                     width=width, height=height, mode=mode, output_extension=ext)
