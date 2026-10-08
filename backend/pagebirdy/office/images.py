"""Text in a document's pictures: OCR it, translate it with the document, redraw it.

Format-independent: an adapter finds its pictures and hands each media part
over as a `Media`; this module decides whether it can be read, OCRs it through
the image pipeline's own stages (`image.pipeline.analyze_raster`), turns the
regions into `Segment`s that go to the engine and the review store with the
document's own text, and at rebuild redraws a picture from whatever targets
those segments hold (`image.pipeline.render_raster`). The picture is written
back in its own format at its own pixel size, so nothing that places it on the
page has to change.

OCR is a paid network call and is not deterministic, while an office rebuild
re-extracts its source (`office.pipeline.rebuild_from_review`). So OCR runs
once per picture and its regions are kept in a sidecar next to the source
(`<src>.ocr.json`, keyed by the picture's SHA-1); a rebuild reads only that.
A picture with no cached regions is left exactly as it was.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import re
from dataclasses import dataclass, field

from PIL import Image

from pagebirdy.models import Segment
from pagebirdy.office.adapter import Issue, writable

logger = logging.getLogger("pagebirdy.office.images")

CACHE_VERSION = 1
_RASTER_TYPES = {"image/png": "PNG", "image/jpeg": "JPEG", "image/jpg": "JPEG"}
# Smaller than this, in either dimension, a picture is an icon or a bullet.
MIN_PIXELS = 48
# Smaller than this on the page (EMU; 457200 = half an inch), nobody reads it.
MIN_DISPLAY_EMU = 457200


def enabled() -> bool:
    """On unless `BABEL_OFFICE_IMAGE_OCR` turns it off, and only when the
    server has an OCR engine at all."""
    if os.getenv("BABEL_OFFICE_IMAGE_OCR", "1").lower() in ("0", "false", "no", "off"):
        return False
    from pagebirdy.image.ocr import ocr_engine

    return ocr_engine() != "none"


def max_images() -> int:
    """Pictures OCR'd per document: each is one OCR call."""
    try:
        return max(0, int(os.getenv("BABEL_OFFICE_IMAGE_MAX", "50")))
    except ValueError:
        return 50


@dataclass
class Media:
    """One picture part, however many places show it."""
    partname: str                   # "/ppt/media/image3.png"
    blob: bytes
    content_type: str
    where: list[str] = field(default_factory=list)   # "slide 4", one per use
    pages: list[int] = field(default_factory=list)
    # Visible fraction of the picture per use: (left, top, right, bottom) cropped off.
    crops: list[tuple[float, float, float, float]] = field(default_factory=list)
    # Largest size it is shown at on the page, in EMU.
    display_emu: tuple[int, int] = (0, 0)

    @property
    def key(self) -> str:
        """The part's name as a segment-id component: no "/" (ids travel in a
        URL path segment), unique per part."""
        return re.sub(r"[^A-Za-z0-9_-]+", "-", os.path.basename(self.partname)).strip("-")

    @property
    def sha1(self) -> str:
        return hashlib.sha1(self.blob).hexdigest()

    @property
    def label(self) -> str:
        return (self.where[0] if self.where else "document") + " image"


def eligible(media: Media) -> str | None:
    """Why this picture is not read, or None when it is."""
    fmt = _RASTER_TYPES.get(media.content_type.lower())
    if fmt is None:
        return f"{media.content_type} pictures are not translated"
    w, h = media.display_emu
    if w and h and (w < MIN_DISPLAY_EMU or h < MIN_DISPLAY_EMU):
        return "picture is too small on the page to hold readable text"
    from pagebirdy.image.validate import ImageValidationError, validate_image_bytes

    try:
        meta = validate_image_bytes(media.blob)
    except ImageValidationError as e:
        return str(e)
    if meta.format != fmt:
        return f"picture is stored as {meta.format}, not the {fmt} its type declares"
    if meta.width < MIN_PIXELS or meta.height < MIN_PIXELS:
        return "picture is too small to hold readable text"
    return None


# --- OCR cache ----------------------------------------------------------------


def cache_path(src: str) -> str:
    return f"{src}.ocr.json"


def _read_cache(src: str) -> dict:
    try:
        with open(cache_path(src), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data.get("pictures", {}) if data.get("version") == CACHE_VERSION else {}


def _write_cache(src: str, pictures: dict) -> None:
    tmp = cache_path(src) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"version": CACHE_VERSION, "pictures": pictures}, f, ensure_ascii=False)
    os.replace(tmp, cache_path(src))


def _ocr(work: Image.Image):
    """The OCR and classification every picture goes through. Classification
    needs a language only for its size estimate, which reads the Latin face
    alone: the source is English whatever the target, so any language with a
    face will do. Tests replace this function."""
    from pagebirdy import languages
    from pagebirdy.image.pipeline import analyze_raster

    return analyze_raster(work, languages.get("es"))


def load_regions(src: str, pictures: list[Media], *, allow_ocr: bool) -> tuple[dict, list[Issue]]:
    """{sha1: [TextRegion]} for every picture: cached, or read now when
    `allow_ocr` and the cache has none. A picture OCR fails on is reported and
    left out."""
    from pagebirdy.image.ocr import OcrError
    from pagebirdy.image.regions import TextRegion

    cached = _read_cache(src)
    out: dict = {}
    issues: list[Issue] = []
    dirty = False
    for m in pictures:
        if m.sha1 in out:
            continue
        if m.sha1 in cached:
            out[m.sha1] = [TextRegion.from_dict(d) for d in cached[m.sha1]]
            continue
        if not allow_ocr:
            continue
        try:
            img = Image.open(io.BytesIO(m.blob))
            img.load()
            from pagebirdy.image.pipeline import work_image

            regions = _ocr(work_image(img))
        except OcrError as e:
            issues.append(Issue("warning", "image", m.label, f"OCR failed, picture kept: {e}"))
            continue
        except Exception:  # noqa: BLE001 — one unreadable picture never fails the document
            logger.exception("office images: OCR failed for %s", m.partname)
            issues.append(Issue("warning", "image", m.label, "picture could not be read; kept"))
            continue
        out[m.sha1] = regions
        cached[m.sha1] = [r.to_dict() for r in regions]
        dirty = True
    if dirty:
        try:
            _write_cache(src, cached)
        except OSError:
            logger.exception("office images: could not write OCR cache for %s", src)
    return out, issues


# --- segments -----------------------------------------------------------------


def _visible(region, size: tuple[int, int], crops) -> bool:
    """Whether the region's centre is inside what any use of the picture shows."""
    w, h = size
    cx = (region.bbox[0] + region.bbox[2]) / 2
    cy = (region.bbox[1] + region.bbox[3]) / 2
    for left, top, right, bottom in crops or [(0.0, 0.0, 0.0, 0.0)]:
        if left * w <= cx <= (1 - right) * w and top * h <= cy <= (1 - bottom) * h:
            return True
    return False


def segment_id(prefix: str, media: Media, region_id: str) -> str:
    return f"{prefix}:img.{media.key}.{region_id}"


def segments_for(prefix: str, media: Media, regions) -> list[Segment]:
    """One segment per region to translate that a reader can see, protected the
    way the image pipeline protects it (URLs, emails, numbers)."""
    from pagebirdy.image.translate import to_segment

    with Image.open(io.BytesIO(media.blob)) as img:
        size = img.size
    out = []
    for r in regions:
        if r.action != "translate" or not _visible(r, size, media.crops):
            continue
        seg = to_segment(r)
        seg.id = segment_id(prefix, media, r.id)
        seg.page = media.pages[0] if media.pages else 0
        out.append(seg)
    return out


# --- rebuild ------------------------------------------------------------------


def render(prefix: str, media: Media, regions, segments: dict, lang) -> tuple[bytes | None, list[Issue]]:
    """The picture redrawn from the writable segments in `segments` (by id), in
    its own format, or None when nothing was redrawn — the part then stays
    byte for byte."""
    from pagebirdy.image.pipeline import encode_like_source, render_raster

    by_region = {}
    for r in regions:
        seg = segments.get(segment_id(prefix, media, r.id))
        r.target = None
        if writable(seg):
            r.target = seg.restored_target()
            by_region[r.id] = seg
    if not by_region:
        return None, []
    try:
        img = Image.open(io.BytesIO(media.blob))
        fmt = img.format
        img.load()
        info = dict(img.info)
        result = render_raster(img, regions, by_region, lang)
        data, _ = encode_like_source(result.final, fmt, info, result.from_source)
    except Exception:  # noqa: BLE001 — a picture that cannot be redrawn keeps its English
        logger.exception("office images: rendering failed for %s", media.partname)
        return None, [Issue("warning", "image", media.label, "picture could not be redrawn; kept")]
    issues = [Issue("warning", "image", media.label, w)
              for r in regions if r.id in by_region for w in r.warnings]
    return (data if result.drawn_boxes else None), issues


def same_pixels_size(a: bytes, b: bytes) -> bool:
    with Image.open(io.BytesIO(a)) as x, Image.open(io.BytesIO(b)) as y:
        return x.size == y.size and x.format == y.format
