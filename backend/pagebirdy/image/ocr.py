"""OCR for image translation, on the Vision integration `ingest/ocr.py` owns.

The client, the billing-propagation retry and the availability check are that
module's, unchanged; only the reading of the response differs. `ingest/ocr.py`
turns a paragraph into a PDF `Line` and *discards* one below its confidence
floor, which is right for a page where OCR is a supplement to real text. Here
OCR is the only source of text, so every paragraph is kept with what an image
needs and a page does not — its words, its visual lines, its language and its
angle — and a weak reading is flagged downstream instead of silently dropped.

Engine order: Google Cloud Vision, then the local RapidOCR model, then none.
Document AI is skipped on purpose — it is the PDF path's full-page-scan
engine, and Vision is the one built for stylised text in pictures.
"""

from __future__ import annotations

import io
import logging
import math
import os
import time

from PIL import Image

from pagebirdy.image.regions import TextRegion, Word
from pagebirdy.ingest import ocr as base_ocr

logger = logging.getLogger("pagebirdy.image.ocr")

# Vision rejects requests over 20 MB / 75 MP and reads text no better above a
# few thousand pixels, so OCR runs on a copy scaled to fit these and the boxes
# are scaled back. The output image itself is never resized.
_OCR_MAX_SIDE = 4096
_OCR_MAX_BYTES = 15 * 1024 * 1024

# Vision's `DetectedBreak.BreakType`.
_SPACE_BREAKS = {1, 2, 3, 5}  # SPACE, SURE_SPACE, EOL_SURE_SPACE, LINE_BREAK
_HYPHEN_BREAK = 4  # an end-of-line hyphen the text itself does not contain


class OcrError(RuntimeError):
    """OCR could not run at all (as opposed to running and finding nothing)."""


def ocr_engine() -> str:
    """vision | rapidocr | none. `BABEL_IMAGE_OCR_ENGINE` forces a choice."""
    forced = os.getenv("BABEL_IMAGE_OCR_ENGINE", "").lower()
    if forced in ("vision", "rapidocr", "none"):
        return forced
    if base_ocr.vision_status():
        return "vision"
    if base_ocr.rapidocr_available():
        return "rapidocr"
    return "none"


def _ocr_copy(img: Image.Image) -> tuple[bytes, float]:
    """The bytes sent to the OCR engine and the factor its boxes are in.

    Encoded from the decoded pixels rather than the uploaded file, so EXIF
    orientation is never applied on one side and not the other: the boxes come
    back in the same pixel grid the reconstruction draws into.
    """
    rgb = img.convert("RGB")
    scale = min(1.0, _OCR_MAX_SIDE / max(rgb.size))
    if scale < 1.0:
        rgb = rgb.resize((max(1, round(rgb.width * scale)), max(1, round(rgb.height * scale))),
                         Image.LANCZOS)
    buf = io.BytesIO()
    rgb.save(buf, "PNG")
    data = buf.getvalue()
    if len(data) > _OCR_MAX_BYTES:
        buf = io.BytesIO()
        rgb.save(buf, "JPEG", quality=92)
        data = buf.getvalue()
    return data, scale


def run_ocr(img: Image.Image, engine: str | None = None) -> tuple[list[TextRegion], str]:
    """Every text region in `img`, in image pixels, and the engine that read it."""
    engine = engine or ocr_engine()
    if engine == "none":
        raise OcrError("No OCR engine is configured on this server.")
    data, scale = _ocr_copy(img)
    if engine == "vision":
        return _vision_regions(data, scale), engine
    if engine == "rapidocr":
        return _rapidocr_regions(data, scale), engine
    raise OcrError(f"unknown OCR engine {engine!r}")


# --- Google Cloud Vision ------------------------------------------------------


def _vision_regions(data: bytes, scale: float) -> list[TextRegion]:
    from google.cloud import vision  # type: ignore[import-not-found]

    client = base_ocr._VisionClient.get()

    def call():
        response = client.document_text_detection(image=vision.Image(content=data))
        if response.error.message:
            raise RuntimeError(response.error.message)
        return response

    started = time.time()
    try:
        response = base_ocr._call_with_billing_retry(call)
    except Exception as exc:  # noqa: BLE001 — quota, auth, network: all one outcome
        logger.error("image OCR: Vision call failed: %s", exc)
        raise OcrError("The OCR service could not read this image.") from exc
    logger.info("image OCR: Vision responded in %.2fs", time.time() - started)
    return parse_vision_response(response, scale)


def _box(vertices, scale: float):
    xs = [float(getattr(v, "x", 0) or 0) / scale for v in vertices]
    ys = [float(getattr(v, "y", 0) or 0) / scale for v in vertices]
    return (min(xs), min(ys), max(xs), max(ys))


def _angle(vertices) -> float:
    """Direction of the text baseline in degrees. Vision lists a box's vertices
    starting at the text's own top-left and going clockwise *in reading
    order*, so the first edge runs along the baseline whatever the rotation."""
    if len(vertices) < 2:
        return 0.0
    dx = float(getattr(vertices[1], "x", 0) or 0) - float(getattr(vertices[0], "x", 0) or 0)
    dy = float(getattr(vertices[1], "y", 0) or 0) - float(getattr(vertices[0], "y", 0) or 0)
    if dx == 0 and dy == 0:
        return 0.0
    return math.degrees(math.atan2(dy, dx))


def _language(prop) -> str | None:
    langs = list(getattr(prop, "detected_languages", None) or [])
    if not langs:
        return None
    best = max(langs, key=lambda l: float(getattr(l, "confidence", 0) or 0))
    return getattr(best, "language_code", None) or None


def _word_text(word) -> tuple[str, str]:
    """A word's characters and what follows it.

    Vision marks a break only where there is one: a space or line break after
    the word, or an end-of-line hyphen the text does not contain. No marker
    means the next word runs straight on — Vision reads "50%" as the words
    "50" and "%" and "5." as "5" and ".", and a space between them would come
    back as "50 %" and reach the engine that way."""
    chars, tail = [], ""
    for sym in word.symbols:
        chars.append(sym.text)
        brk = getattr(getattr(getattr(sym, "property", None), "detected_break", None), "type_", None)
        if brk is None:
            brk = getattr(getattr(getattr(sym, "property", None), "detected_break", None), "type", None)
        if brk is not None:
            brk = int(brk)
            tail = "" if brk == _HYPHEN_BREAK else " " if brk in _SPACE_BREAKS else tail
    return "".join(chars), tail


def group_lines(words: list[Word]) -> list[tuple[float, float, float, float]]:
    """Visual lines from word boxes: words whose vertical extents overlap by
    half the smaller height sit on one line."""
    lines: list[list[Word]] = []
    for w in sorted(words, key=lambda w: (w.bbox[1] + w.bbox[3]) / 2):
        h = w.bbox[3] - w.bbox[1]
        for line in lines:
            ly0 = min(x.bbox[1] for x in line)
            ly1 = max(x.bbox[3] for x in line)
            overlap = min(ly1, w.bbox[3]) - max(ly0, w.bbox[1])
            if overlap >= 0.5 * min(h, ly1 - ly0):
                line.append(w)
                break
        else:
            lines.append([w])
    boxes = [(min(x.bbox[0] for x in ln), min(x.bbox[1] for x in ln),
              max(x.bbox[2] for x in ln), max(x.bbox[3] for x in ln)) for ln in lines]
    return sorted(boxes, key=lambda b: b[1])


def parse_vision_response(response, scale: float = 1.0) -> list[TextRegion]:
    """`DOCUMENT_TEXT_DETECTION` -> one region per Vision paragraph.

    Paragraphs rather than words or blocks: a paragraph is what reads as one
    unit ("Welcome to our store"), and what has to be translated together for
    the sentence to come back as a sentence. Nothing is dropped for low
    confidence here — that is classify.py's decision, and it flags rather than
    discards.
    """
    regions: list[TextRegion] = []
    annotation = response.full_text_annotation
    for page in annotation.pages:
        page_lang = _language(getattr(page, "property", None))
        for bi, block in enumerate(page.blocks):
            block_lang = _language(getattr(block, "property", None)) or page_lang
            for pi, para in enumerate(block.paragraphs):
                words: list[Word] = []
                parts: list[str] = []
                for word in para.words:
                    text, tail = _word_text(word)
                    if not text:
                        continue
                    words.append(Word(text=text, bbox=_box(word.bounding_box.vertices, scale),
                                      confidence=float(getattr(word, "confidence", 0) or 0)))
                    parts.append(text + tail)
                text = "".join(parts).strip()
                if not text:
                    continue
                verts = para.bounding_box.vertices
                regions.append(TextRegion(
                    id=f"r{len(regions) + 1}",
                    text=text,
                    bbox=_box(verts, scale),
                    confidence=float(getattr(para, "confidence", 0) or 0),
                    language=_language(getattr(para, "property", None)) or block_lang,
                    words=words,
                    lines=group_lines(words),
                    block=bi,
                    paragraph=pi,
                    angle=_angle(verts),
                ))
    logger.info("image OCR: %d region(s)", len(regions))
    return regions


# --- RapidOCR (offline fallback) ---------------------------------------------


def _rapidocr_regions(data: bytes, scale: float) -> list[TextRegion]:
    """RapidOCR reads one line per box and reports no words or language, so
    each line is its own region and its own single word."""
    try:
        raw = base_ocr._RapidOCR.read(data)
    except Exception as exc:  # noqa: BLE001
        logger.error("image OCR: RapidOCR failed: %s", exc)
        raise OcrError("The OCR engine could not read this image.") from exc
    regions: list[TextRegion] = []
    for box, text, confidence in raw:
        text = (text or "").strip()
        if not text:
            continue
        xs = [p[0] / scale for p in box]
        ys = [p[1] / scale for p in box]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        dx, dy = box[1][0] - box[0][0], box[1][1] - box[0][1]
        regions.append(TextRegion(
            id=f"r{len(regions) + 1}", text=text, bbox=bbox,
            confidence=float(confidence or 0),
            words=[Word(text=text, bbox=bbox, confidence=float(confidence or 0))],
            lines=[bbox], block=len(regions),
            angle=math.degrees(math.atan2(dy, dx)) if (dx or dy) else 0.0,
        ))
    return regions
