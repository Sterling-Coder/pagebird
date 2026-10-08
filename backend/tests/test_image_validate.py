"""Upload validation: the content decides, never the name or the client's MIME."""

import io

import pytest
from PIL import Image

from pagebirdy.image.validate import (ImageValidationError, safe_filename, supported_formats,
                                  validate_image_bytes)


def _encode(fmt, size=(64, 48), mode="RGB", **kw):
    buf = io.BytesIO()
    Image.new(mode, size, (200, 100, 50) if mode == "RGB" else 128).save(buf, fmt, **kw)
    return buf.getvalue()


@pytest.mark.parametrize("fmt,ext", [("PNG", ".png"), ("JPEG", ".jpg"), ("WEBP", ".webp")])
def test_supported_formats_are_accepted(fmt, ext):
    info = validate_image_bytes(_encode(fmt))
    assert (info.format, info.extension, info.width, info.height) == (fmt, ext, 64, 48)


def test_advertised_formats_are_exactly_what_validation_accepts():
    names = {f["format"] for f in supported_formats()}
    assert {"PNG", "JPEG"} <= names
    assert "GIF" not in names


def test_unsupported_format_is_rejected():
    with pytest.raises(ImageValidationError, match="Unsupported image format"):
        validate_image_bytes(_encode("GIF"))


def test_non_image_is_rejected_whatever_it_is_called():
    with pytest.raises(ImageValidationError, match="not a readable image"):
        validate_image_bytes(b"%PDF-1.7 definitely not a png")


def test_truncated_image_is_rejected():
    data = _encode("PNG", size=(400, 400))
    with pytest.raises(ImageValidationError):
        validate_image_bytes(data[: len(data) // 2])


def test_empty_and_oversized_files_are_rejected(monkeypatch):
    with pytest.raises(ImageValidationError, match="empty"):
        validate_image_bytes(b"")
    monkeypatch.setenv("BABEL_IMAGE_MAX_BYTES", "100")
    with pytest.raises(ImageValidationError, match="too large"):
        validate_image_bytes(_encode("PNG"))


def test_pixel_limit_is_checked_before_decoding(monkeypatch):
    monkeypatch.setenv("BABEL_IMAGE_MAX_PIXELS", "1000")
    with pytest.raises(ImageValidationError, match="too many pixels"):
        validate_image_bytes(_encode("PNG", size=(100, 100)))


def test_tiny_image_is_rejected():
    with pytest.raises(ImageValidationError, match="too small"):
        validate_image_bytes(_encode("PNG", size=(8, 8)))


def test_safe_filename_strips_paths_and_unsafe_characters():
    assert safe_filename("../../etc/passwd.png") == "passwd.png"
    assert safe_filename("C:\\Users\\x\\a b.jpg") == "a b.jpg"
    assert safe_filename('evil"\r\nname.png') == "evil___name.png"
    assert safe_filename("") == "image"
