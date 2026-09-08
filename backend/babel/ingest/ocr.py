"""OCR ingest — recovers text the PDF does not expose as text.

Two cases, both listed as gaps in CLAUDE.md's "Known limits":

1. **Scanned pages** — the PDF is a picture of a document; `ingest/pdf.py`
   returns nothing for them.
2. **Text baked into diagrams** — axis labels, callouts, figure captions inside
   a raster image. Today `reassemble/pdf.py` only *flags* these pages
   (`detect_graphic_pages`). The client explicitly asked for this: "images with
   text within those images should be kept the same but the text should be
   translated".

Both produce ordinary `Line` objects, so everything downstream — math
protection, glossary, TM, dual-engine translation, integrity gate, review UI —
works unchanged. OCR'd lines are marked `from_ocr` so reassembly can white-out
the original burned-in text before drawing the Spanish over it.

Engine: Google Document AI (primary, per the layer plan). Configure via env:

    GOOGLE_APPLICATION_CREDENTIALS=/path/sa.json
    DOCAI_PROJECT_ID=...   DOCAI_LOCATION=us   DOCAI_PROCESSOR_ID=...

With no credentials the module degrades to a no-op that reports *why*, so the
pipeline still runs offline (same contract as the translation engines).
"""

from __future__ import annotations

import io
import logging
import os
import time
from dataclasses import dataclass
from functools import lru_cache

import fitz

from babel.models import Line, Span

# Engine selection is silent by design (every layer degrades rather than raises),
# which makes "why did it fall back to rapidocr?" impossible to answer from the
# outside. This logger narrates the decision and every Vision call.
#   BABEL_OCR_DEBUG=1  -> per-paragraph detail
logger = logging.getLogger("babel.ocr")

if os.getenv("BABEL_OCR_DEBUG", "").lower() in ("1", "true", "yes", "on"):
    logger.setLevel(logging.DEBUG)

# Document AI's synchronous endpoint caps at 15 pages per call.
SYNC_PAGE_LIMIT = 15
# A page with less real text than this is almost certainly scanned.
SCANNED_CHAR_THRESHOLD = 40
# Ignore OCR blocks below this confidence — they are usually chart noise.
MIN_CONFIDENCE = 0.55
# Estimated point size for OCR'd (image-burned) text is bbox height * 0.8,
# capped here. 24pt used to be the ceiling, which silently shrank large
# decorative banner titles (30-40pt+ display type) down to normal-caption
# size once translated — the box height was measured correctly, the cap just
# discarded it. Raised so genuinely large titles keep their size; small OCR
# captions are unaffected since the cap only ever bound the large end.
OCR_SIZE_CAP = 60.0

# --- what text inside an image is worth replacing ----------------------------
#
# Replacing burned-in text means covering the original pixels and drawing over
# them. That trade is worth making for a label the reader is meant to read — a
# banner, a callout, a speech bubble — and not for text that is part of a
# depicted object: the motto and mint date struck into a photographed coin, a
# brand name on a packet, a street sign in the background. Those are not
# addressed to the reader, and the flat cover patch visibly damages the artwork.
#
# The two classes cannot be told apart from the pixels — the gradient on a
# decorative arrow profiles the same as a coin's relief — but the OCR itself
# separates them cleanly. Measured over a document whose figures are photographed
# pennies: real labels read back at 0.968-1.000 confidence and 10.6-22.5 pt,
# while coin text reads at 0.552-0.965 and almost all of it at 6 pt.
#
# Both bars must be cleared, and anything refused is still ingested and flagged —
# it simply keeps its original pixels instead of being painted over.
MIN_IMAGE_CONFIDENCE = 0.95
# Below this the translation cannot be drawn back legibly anyway: the reassembler
# will not set type under 5 pt, and an RTL face needs about 1.5x the height of the
# Latin it replaces.
MIN_IMAGE_SIZE = 9.5
# How much taller than the text needs it a box may be, per line the text could
# wrap onto. A real label's box measures 0.76-1.03 line heights — it is a line of
# type and little else; a word struck around a coin's rim measures 1.4 and up,
# because the arc inflates its axis-aligned box. The bound sits in that gap.
# Boxes are judged before `_pad_bbox` widens them, so this is the OCR engine's
# own measurement of the text.
_MAX_BOX_STRETCH = 1.2


@dataclass
class OcrStatus:
    available: bool
    reason: str = ""

    def __bool__(self) -> bool:
        return self.available


def docai_status() -> OcrStatus:
    """Whether Document AI is usable right now, and if not, why not."""
    if not os.getenv("DOCAI_PROJECT_ID") or not os.getenv("DOCAI_PROCESSOR_ID"):
        return OcrStatus(False, "DOCAI_PROJECT_ID / DOCAI_PROCESSOR_ID not set")
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return OcrStatus(False, "GOOGLE_APPLICATION_CREDENTIALS not set")
    try:
        import google.cloud.documentai_v1  # noqa: F401  # type: ignore[import-not-found]
    except ImportError:
        return OcrStatus(False, "pip install google-cloud-documentai")
    return OcrStatus(True)


def _vision_import_error() -> str | None:
    """The actual reason the Vision SDK will not import, or None if it does.

    `_vision_importable` throws this detail away, which is why a missing
    `google-cloud-vision` and a broken protobuf/grpc install look identical from
    the outside — both just silently fall back to rapidocr.
    """
    try:
        import google.cloud.vision  # noqa: F401  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001 — grpc/protobuf can fail beyond ImportError
        return f"{type(exc).__name__}: {exc}"
    return None


@lru_cache(maxsize=1)
def _metrics_font():
    """A plain Latin face, used only to ask how wide a string wants to be."""
    return fitz.Font("helv")


def _is_horizontal_setting(text: str, width: float, height: float) -> bool:
    """Could this text be set as horizontal lines inside this box?

    The size at which the text fills the box's width implies a line height. A
    box a couple of line heights tall is a wrapped label; a box many line
    heights tall holding a single unwrappable word is not text laid out on a
    line at all — it is a motto arcing around a coin's rim, whose axis-aligned
    box the curve inflates. Wrapping needs somewhere to break, so the budget is
    counted in words.
    """
    advance = _metrics_font().text_length(text, 1.0)
    if advance <= 0:
        return False
    line_height = (width / advance) * 1.2
    if line_height <= 0:
        return False
    return height / line_height <= max(1, len(text.split())) * _MAX_BOX_STRETCH


def worth_translating(line: Line) -> bool:
    """Is this run worth covering the artwork underneath it to replace?

    Only text recovered from inside a raster image is judged: ordinary PDF text
    has its own glyphs to redact and never reaches this gate. A run that fails
    is still ingested and flagged for review — it simply keeps its original
    pixels rather than being painted over.
    """
    if not line.in_image:
        return True
    text = line.raw_text.strip()
    x0, y0, x1, y1 = line.bbox
    width, height = x1 - x0, y1 - y0
    if not text or width <= 0 or height <= 0:
        return False
    if line.ocr_confidence < MIN_IMAGE_CONFIDENCE:
        return False
    if height * 0.8 < MIN_IMAGE_SIZE:
        return False
    return _is_horizontal_setting(text, width, height)


def _vision_importable() -> bool:
    return _vision_import_error() is None


def vision_status() -> OcrStatus:
    """Whether Google Cloud Vision is usable right now, and if not, why not."""
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds:
        logger.info("vision unavailable: GOOGLE_APPLICATION_CREDENTIALS not set")
        return OcrStatus(False, "GOOGLE_APPLICATION_CREDENTIALS not set")
    if not os.path.exists(creds):
        # Not treated as unavailable — the SDK also accepts other credential
        # sources — but it is the most common misconfiguration, so say so loudly.
        logger.warning(
            "GOOGLE_APPLICATION_CREDENTIALS points at a file that does not exist: %s",
            creds,
        )
    if not _vision_importable():
        detail = _vision_import_error()
        logger.warning("vision unavailable: cannot import google.cloud.vision (%s). "
                       "Fix: pip install google-cloud-vision", detail)
        return OcrStatus(False, f"pip install google-cloud-vision ({detail})")
    logger.info("vision available: credentials=%s", creds)
    return OcrStatus(True)


def ocr_http_url() -> str:
    """Base URL of an external OCR microservice, if one is configured.

    Mirrors the IDP service contract: POST {base}/extract-text with a file part
    and a `language` query param, answering {"status": "success",
    "extracted_text": ...}. Set OCR_API_BASE_URL to enable.
    """
    return os.getenv("OCR_API_BASE_URL", "").rstrip("/")


def ocr_http_healthy(timeout: float = 8.0) -> bool:
    base = ocr_http_url()
    if not base:
        return False
    try:
        import requests  # type: ignore[import-not-found]

        resp = requests.get(f"{base}/health", timeout=timeout,
                            headers={"ngrok-skip-browser-warning": "true"})
        return resp.json().get("status") == "healthy"
    except Exception:  # noqa: BLE001 — an unreachable service is just "not available"
        return False


def _ocr_http_call(content: bytes, filename: str, mime: str,
                   language: str = "en") -> str:
    import requests  # type: ignore[import-not-found]

    timeout = float(os.getenv("OCR_API_TIMEOUT", "120"))
    resp = requests.post(
        f"{ocr_http_url()}/extract-text",
        params={"language": language},
        files={"file": (filename, content, mime)},
        headers={"ngrok-skip-browser-warning": "true"},
        timeout=timeout,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "success":
        raise RuntimeError(f"OCR service returned {payload.get('status')!r}")
    return payload.get("extracted_text", "")


def _http_lines(text: str, page: int, rect: "fitz.Rect") -> list[Line]:
    """A plain-text OCR reply has no geometry, so lay it out down the page.

    Good enough to recover *content* from a scanned page, but the boxes are
    synthetic — do not use this engine when you need to mask burned-in text in
    an image, which needs true coordinates.
    """
    rows = [r.strip() for r in (text or "").splitlines() if r.strip()]
    if not rows:
        return []
    step = rect.height / max(len(rows), 1)
    out: list[Line] = []
    for i, row in enumerate(rows):
        y0 = rect.y0 + i * step
        bbox = (rect.x0, y0, rect.x1, min(y0 + step, rect.y1))
        out.append(
            Line(page=page, bbox=bbox,
                 spans=[Span(text=row, font="OCR", size=10.0, color=0, bbox=bbox)],
                 block=9000, from_ocr=True, ocr_confidence=0.9)
        )
    return out


def rapidocr_available() -> bool:
    """Local OCR fallback — no key, no network, runs on CPU."""
    try:
        from rapidocr_onnxruntime import RapidOCR  # noqa: F401  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001 — onnxruntime can fail loudly on import
        return False
    return True


def ocr_status() -> OcrStatus:
    """The engine that would actually run, and why."""
    engine = active_ocr_engine()
    if engine == "docai":
        return OcrStatus(True, "Document AI")
    if engine == "vision":
        return OcrStatus(True, "Google Cloud Vision")
    if engine == "http":
        return OcrStatus(True, f"OCR service at {ocr_http_url()}")
    if engine == "rapidocr":
        return OcrStatus(True, "local rapidocr (no Document AI / OCR service configured)")
    return OcrStatus(False, docai_status().reason + "; " + vision_status().reason
                     + "; no OCR_API_BASE_URL; pip install rapidocr-onnxruntime")


def ocr_diagnostics() -> dict:
    """Every input to the engine choice, in one call.

    Answers "why is Vision not being used?" without running a translation:
    which engine wins, and the specific reason each other candidate lost.
    """
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    docai, vision = docai_status(), vision_status()
    http_base = ocr_http_url()
    report = {
        "active_engine": active_ocr_engine(),
        "forced_by_env": os.getenv("BABEL_OCR_ENGINE") or None,
        "docai": {"available": bool(docai), "reason": docai.reason,
                  "project": os.getenv("DOCAI_PROJECT_ID"),
                  "processor": os.getenv("DOCAI_PROCESSOR_ID"),
                  "location": os.getenv("DOCAI_LOCATION", "us")},
        "vision": {
            "available": bool(vision),
            "reason": vision.reason,
            "credentials_path": creds,
            "credentials_file_exists": bool(creds and os.path.exists(creds)),
            "sdk_import_error": _vision_import_error(),
        },
        "http": {"base_url": http_base or None,
                 "healthy": bool(http_base and ocr_http_healthy())},
        "rapidocr": {"available": rapidocr_available()},
        "min_confidence": MIN_CONFIDENCE,
    }
    logger.info("ocr diagnostics: %s", report)
    return report


def active_ocr_engine() -> str:
    """docai | vision | http | rapidocr | none.

    Document AI first (best layout accuracy on full-page scans), then Vision
    (best on stylized/decorative graphic text — banners, callouts), then an
    external OCR service if one is configured and healthy, then the local
    model. `BABEL_OCR_ENGINE` forces a specific choice.
    """
    forced = os.getenv("BABEL_OCR_ENGINE", "").lower()
    if forced in ("docai", "vision", "http", "rapidocr", "none"):
        logger.info("ocr engine forced by BABEL_OCR_ENGINE=%s", forced)
        return forced

    docai, vision = docai_status(), vision_status()
    if docai:
        logger.info("ocr engine: docai")
        return "docai"
    if vision:
        logger.info("ocr engine: vision (docai unavailable: %s)", docai.reason)
        return "vision"

    http_base = ocr_http_url()
    if http_base and ocr_http_healthy():
        logger.info("ocr engine: http at %s", http_base)
        return "http"

    engine = "rapidocr" if rapidocr_available() else "none"
    # The line that answers "why is Vision not being used?" — every rejection
    # reason in one place, rather than four silent falsy returns.
    logger.warning(
        "ocr engine: %s — docai unavailable (%s); vision unavailable (%s); "
        "http unavailable (%s)",
        engine, docai.reason, vision.reason,
        f"unhealthy at {http_base}" if http_base else "OCR_API_BASE_URL not set",
    )
    return engine


class _RapidOCR:
    """Lazy singleton; the ONNX models load once and are reused."""

    _engine = None

    @classmethod
    def get(cls):
        if cls._engine is None:
            from rapidocr_onnxruntime import RapidOCR  # type: ignore[import-not-found]

            cls._engine = RapidOCR()
        return cls._engine

    @classmethod
    def read(cls, png_bytes: bytes) -> list[tuple[list, str, float]]:
        """[(box, text, confidence), ...] in pixel coordinates."""
        import numpy as np  # type: ignore[import-not-found]
        from PIL import Image  # type: ignore[import-not-found]

        with Image.open(io.BytesIO(png_bytes)) as img:
            array = np.array(img.convert("RGB"))
        result, _ = cls.get()(array)
        return result or []


def _rapidocr_lines(png_bytes: bytes, page: int, clip: "fitz.Rect",
                    dpi: int) -> list[Line]:
    """RapidOCR output → Lines, mapped from crop pixels back to page points."""
    scale = 72.0 / dpi
    lines: list[Line] = []
    for box, text, confidence in _RapidOCR.read(png_bytes):
        text = (text or "").strip()
        if not text or float(confidence or 0) < MIN_CONFIDENCE:
            continue
        xs = [p[0] * scale + clip.x0 for p in box]
        ys = [p[1] * scale + clip.y0 for p in box]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        size = max(6.0, min(OCR_SIZE_CAP, (bbox[3] - bbox[1]) * 0.8))
        lines.append(
            Line(
                page=page,
                bbox=bbox,
                spans=[Span(text=text, font="OCR", size=size, color=0, bbox=bbox)],
                block=9000,
                from_ocr=True,
                ocr_confidence=float(confidence or 0),
            )
        )
    return lines


class _VisionClient:
    """Lazy singleton; the client opens its transport once and is reused."""

    _client = None

    @classmethod
    def get(cls):
        if cls._client is None:
            from google.cloud import vision  # type: ignore[import-not-found]

            try:
                cls._client = vision.ImageAnnotatorClient()
            except Exception:
                # Bad/expired service-account JSON surfaces here, not at import,
                # and the caller only reports "Vision failed" without the cause.
                logger.error("vision: ImageAnnotatorClient() failed to construct "
                             "(credentials=%s)",
                             os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                             exc_info=True)
                raise
            logger.info("vision: client constructed")
        return cls._client


def _parse_vision_response(response, page: int, clip: "fitz.Rect", dpi: int) -> list[Line]:
    """Vision `DOCUMENT_TEXT_DETECTION` response -> Lines, pixel verts -> PDF points.

    Grouped by paragraph (Vision's line-equivalent) rather than word, so a
    banner like "GO!" comes back as one Line instead of one per glyph run.
    """
    scale = 72.0 / dpi
    lines: list[Line] = []
    annotation = response.full_text_annotation
    seen = low_confidence = empty = 0
    for doc_page in annotation.pages:
        for block in doc_page.blocks:
            for paragraph in block.paragraphs:
                seen += 1
                confidence = float(paragraph.confidence or 0)
                if confidence < MIN_CONFIDENCE:
                    # Vision often *does* read the text and we throw it away
                    # here. Without this line a working call and a
                    # nothing-survived-the-threshold call look the same.
                    low_confidence += 1
                    logger.debug("vision p%d: dropped conf=%.2f < %.2f text=%r",
                                 page + 1, confidence, MIN_CONFIDENCE,
                                 "".join(s.text for w in paragraph.words
                                         for s in w.symbols)[:60])
                    continue
                text = " ".join(
                    "".join(sym.text for sym in word.symbols) for word in paragraph.words
                ).strip()
                if not text:
                    empty += 1
                    continue
                verts = paragraph.bounding_box.vertices
                xs = [v.x * scale + clip.x0 for v in verts]
                ys = [v.y * scale + clip.y0 for v in verts]
                bbox = (min(xs), min(ys), max(xs), max(ys))
                size = max(6.0, min(OCR_SIZE_CAP, (bbox[3] - bbox[1]) * 0.8))
                lines.append(
                    Line(
                        page=page,
                        bbox=bbox,
                        spans=[Span(text=text, font="OCR", size=size, color=0, bbox=bbox)],
                        block=9000,
                        from_ocr=True,
                        ocr_confidence=confidence,
                    )
                )
    logger.info(
        "vision p%d: %d paragraph(s) -> %d line(s) kept, %d below confidence %.2f, "
        "%d empty",
        page + 1, seen, len(lines), low_confidence, MIN_CONFIDENCE, empty,
    )
    if seen and not lines:
        logger.warning("vision p%d: read %d paragraph(s) but kept none — every one "
                       "scored below MIN_CONFIDENCE=%.2f", page + 1, seen, MIN_CONFIDENCE)
    return lines


_BILLING_RETRY_ATTEMPTS = 3
_BILLING_RETRY_DELAY = 5.0


def _call_with_billing_retry(fn, attempts: int = _BILLING_RETRY_ATTEMPTS,
                             delay: float = _BILLING_RETRY_DELAY):
    """Google's own billing-enabled check has a short propagation cache of its
    own — a request can fail with BILLING_DISABLED for a few seconds after
    billing was actually turned on, independent of when the call happens to
    run. Retry through that narrow window instead of failing the whole OCR
    pass on what is, from our side, a pure flake.
    """
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            if "BILLING_DISABLED" not in str(exc) or attempt == attempts - 1:
                logger.error("vision: call failed on attempt %d/%d: %s",
                             attempt + 1, attempts, exc, exc_info=True)
                raise
            logger.warning("vision: BILLING_DISABLED on attempt %d/%d, retrying in %.0fs "
                           "(billing propagation)", attempt + 1, attempts, delay)
            time.sleep(delay)


def _vision_lines(png_bytes: bytes, page: int, clip: "fitz.Rect", dpi: int) -> list[Line]:
    from google.cloud import vision  # type: ignore[import-not-found]

    client = _VisionClient.get()
    logger.info("vision: p%d requesting document_text_detection, %d KB @ %d dpi, "
                "clip=(%.0f,%.0f,%.0f,%.0f)",
                page + 1, len(png_bytes) // 1024, dpi,
                clip.x0, clip.y0, clip.x1, clip.y1)

    def call():
        response = client.document_text_detection(image=vision.Image(content=png_bytes))
        if response.error.message:
            # Quota, billing, bad key and malformed image all arrive here as a
            # field on a 200 response rather than as an exception.
            logger.error("vision: API returned error for p%d: %s",
                         page + 1, response.error.message)
            raise RuntimeError(response.error.message)
        return response

    started = time.time()
    response = _call_with_billing_retry(call)
    logger.info("vision: p%d responded in %.2fs", page + 1, time.time() - started)
    return _parse_vision_response(response, page, clip, dpi)


def _client():
    from google.api_core.client_options import ClientOptions  # type: ignore[import-not-found]
    from google.cloud import documentai_v1 as documentai  # type: ignore[import-not-found]

    location = os.getenv("DOCAI_LOCATION", "us")
    client = documentai.DocumentProcessorServiceClient(
        client_options=ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    )
    name = client.processor_path(
        os.getenv("DOCAI_PROJECT_ID"), location, os.getenv("DOCAI_PROCESSOR_ID")
    )
    return client, name


def detect_scanned_pages(pdf_path: str) -> list[int]:
    """0-based pages that carry (almost) no extractable text."""
    doc = fitz.open(pdf_path)
    try:
        return [
            pno for pno in range(doc.page_count)
            if len(doc.load_page(pno).get_text("text").strip()) < SCANNED_CHAR_THRESHOLD
        ]
    finally:
        doc.close()


def detect_image_regions(pdf_path: str, min_area: float = 1_500.0) -> dict[int, list[tuple]]:
    """Raster images big enough to plausibly contain readable text.

    Returns {page_index: [bbox, ...]} in PDF points.
    """
    doc = fitz.open(pdf_path)
    out: dict[int, list[tuple]] = {}
    try:
        for pno in range(doc.page_count):
            page = doc.load_page(pno)
            boxes = []
            for info in page.get_images(full=True):
                for rect in page.get_image_rects(info[0]):
                    if rect.get_area() >= min_area:
                        boxes.append(tuple(rect))
            if boxes:
                out[pno] = boxes
        return out
    finally:
        doc.close()


def _pdf_bytes_for(pdf_path: str, pages: list[int]) -> bytes:
    """A small PDF holding just `pages`, to stay under the sync page limit."""
    src = fitz.open(pdf_path)
    sub = fitz.open()
    try:
        for pno in pages:
            sub.insert_pdf(src, from_page=pno, to_page=pno)
        return sub.tobytes()
    finally:
        sub.close()
        src.close()


def _lines_from_document(document, doc_page_index: int, pdf_page: int,
                         width: float, height: float) -> list[Line]:
    """Document AI page → babel `Line`s, normalized vertices → PDF points."""
    page = document.pages[doc_page_index]
    text = document.text
    lines: list[Line] = []

    def seg_text(layout) -> str:
        parts = []
        for seg in layout.text_anchor.text_segments:
            parts.append(text[int(seg.start_index or 0):int(seg.end_index or 0)])
        return "".join(parts).strip()

    # `lines` maps to our Line; blocks would merge unrelated labels together
    for ln in page.lines:
        content = seg_text(ln.layout)
        confidence = float(ln.layout.confidence or 0.0)
        if not content or confidence < MIN_CONFIDENCE:
            continue
        verts = ln.layout.bounding_poly.normalized_vertices
        if not verts:
            continue
        xs = [v.x * width for v in verts]
        ys = [v.y * height for v in verts]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        size = max(6.0, min(OCR_SIZE_CAP, (bbox[3] - bbox[1]) * 0.8))
        lines.append(
            Line(
                page=pdf_page,
                bbox=bbox,
                spans=[Span(text=content, font="OCR", size=size, color=0, bbox=bbox)],
                block=9000,  # keep OCR lines in their own paragraph group
                from_ocr=True,
                ocr_confidence=confidence,
            )
        )
    return lines


def ocr_pages(pdf_path: str, pages: list[int] | None = None,
              dpi: int = 200) -> tuple[list[Line], str]:
    """OCR whole pages. Returns (lines, note). Never raises on missing config."""
    engine = active_ocr_engine()
    if engine == "none":
        return [], f"OCR skipped: {ocr_status().reason}"

    if pages is None:
        pages = detect_scanned_pages(pdf_path)
    if not pages:
        return [], "OCR skipped: no scanned pages detected"

    if engine in ("rapidocr", "vision", "http"):
        doc = fitz.open(pdf_path)
        lines: list[Line] = []
        try:
            for pno in pages:
                page = doc.load_page(pno)
                png = page.get_pixmap(dpi=dpi).tobytes("png")
                if engine == "rapidocr":
                    lines.extend(_rapidocr_lines(png, pno, page.rect, dpi))
                elif engine == "vision":
                    try:
                        lines.extend(_vision_lines(png, pno, page.rect, dpi))
                    except Exception as exc:  # noqa: BLE001
                        # One bad page abandons the whole pass, so this is worth
                        # a stack trace rather than a one-line note nobody reads.
                        logger.error("vision: page OCR aborted at p%d — no OCR lines "
                                     "will be produced for this document",
                                     pno + 1, exc_info=True)
                        return [], f"OCR skipped: Vision failed ({exc})"
                else:
                    try:
                        text = _ocr_http_call(png, f"page_{pno + 1}.png", "image/png")
                    except Exception as exc:  # noqa: BLE001
                        return [], f"OCR skipped: OCR service failed ({exc})"
                    lines.extend(_http_lines(text, pno, page.rect))
        finally:
            doc.close()
        return lines, f"OCR ({engine}): {len(lines)} lines from {len(pages)} page(s)"

    from google.cloud import documentai_v1 as documentai  # type: ignore[import-not-found]

    client, name = _client()
    doc = fitz.open(pdf_path)
    sizes = {p: (doc.load_page(p).rect.width, doc.load_page(p).rect.height) for p in pages}
    doc.close()

    lines: list[Line] = []
    for start in range(0, len(pages), SYNC_PAGE_LIMIT):
        chunk = pages[start:start + SYNC_PAGE_LIMIT]
        result = client.process_document(
            request=documentai.ProcessRequest(
                name=name,
                raw_document=documentai.RawDocument(
                    content=_pdf_bytes_for(pdf_path, chunk),
                    mime_type="application/pdf",
                ),
            )
        )
        for idx, pno in enumerate(chunk):
            w, h = sizes[pno]
            lines.extend(_lines_from_document(result.document, idx, pno, w, h))

    return lines, f"OCR: {len(lines)} lines from {len(pages)} page(s)"


_BBOX_PAD_FRACTION = 0.2  # OCR boxes clip ascenders/descenders/punctuation dots short


def _pad_bbox(bbox: tuple[float, float, float, float], fraction: float = _BBOX_PAD_FRACTION
             ) -> tuple[float, float, float, float]:
    """Grow a tight OCR bbox so the redaction rect clears the whole glyph.

    An OCR engine's box is fit to the characters it recognized with
    confidence, not the full ink extent — an exclamation mark's dot or a
    round letter's overshoot can sit just outside it. Left unpadded, the
    redaction leaves a sliver of the original (English) pixels visible at
    the edge, under the newly drawn translation.
    """
    x0, y0, x1, y1 = bbox
    margin = (y1 - y0) * fraction
    return (x0 - margin, y0 - margin, x1 + margin, y1 + margin)


_FOREGROUND_DISTANCE = 60.0  # RGB Euclidean distance from the border average to count as glyph, not fill


def _sample_foreground_color(page, rect: "fitz.Rect", dpi: int = 150) -> int | None:
    """Best-effort text color for an OCR'd line that carries no font metadata.

    A banner/callout's fill is near-uniform, so the border pixels are a good
    estimate of the background; whatever stands out from that estimate is
    the glyphs themselves. Returns None (caller falls back to black) when no
    pixel stands out — a plain white background with black text, say.
    """
    if rect.get_area() <= 0:
        return None
    pix = page.get_pixmap(clip=rect, dpi=dpi)
    w, h = pix.width, pix.height
    if w < 2 or h < 2 or pix.n < 3:
        return None
    stride, n = pix.stride, pix.n
    samples = pix.samples

    def px(x: int, y: int) -> tuple[int, int, int]:
        off = y * stride + x * n
        return samples[off], samples[off + 1], samples[off + 2]

    border = [px(x, 0) for x in range(w)] + [px(x, h - 1) for x in range(w)] \
        + [px(0, y) for y in range(h)] + [px(w - 1, y) for y in range(h)]
    bg = tuple(sum(c[i] for c in border) / len(border) for i in range(3))

    fg = [
        (r, g, b)
        for y in range(h) for x in range(w)
        for r, g, b in [px(x, y)]
        if ((r - bg[0]) ** 2 + (g - bg[1]) ** 2 + (b - bg[2]) ** 2) ** 0.5 > _FOREGROUND_DISTANCE
    ]
    if not fg:
        return None
    r = int(sum(p[0] for p in fg) / len(fg))
    g = int(sum(p[1] for p in fg) / len(fg))
    b = int(sum(p[2] for p in fg) / len(fg))
    return (r << 16) | (g << 8) | b


def ocr_image_regions(pdf_path: str, regions: dict[int, list[tuple]] | None = None,
                      dpi: int = 300) -> tuple[list[Line], str]:
    """OCR the text *inside* raster images, keeping page coordinates.

    This is what makes "keep the image, translate the text in it" possible: the
    returned lines sit exactly where the burned-in text sits, so reassembly can
    cover the original and draw the Spanish in its place.
    """
    engine = active_ocr_engine()
    if engine == "none":
        return [], f"image-OCR skipped: {ocr_status().reason}"

    if regions is None:
        regions = detect_image_regions(pdf_path)
    if not regions:
        return [], "image-OCR skipped: no sizeable images found"

    client = name = None
    if engine == "docai":
        from google.cloud import documentai_v1 as documentai  # type: ignore[import-not-found]

        client, name = _client()

    doc = fitz.open(pdf_path)
    lines: list[Line] = []
    refused: list[str] = []
    try:
        for pno, boxes in sorted(regions.items()):
            page = doc.load_page(pno)
            for box in boxes:
                rect = fitz.Rect(box)
                png = page.get_pixmap(clip=rect, dpi=dpi).tobytes("png")

                if engine == "rapidocr":
                    local = _rapidocr_lines(png, pno, rect, dpi)
                elif engine == "vision":
                    try:
                        local = _vision_lines(png, pno, rect, dpi)
                    except Exception as exc:  # noqa: BLE001
                        logger.error("vision: image OCR aborted at p%d region "
                                     "(%.0f,%.0f,%.0f,%.0f) — no image-OCR lines will "
                                     "be produced for this document",
                                     pno + 1, rect.x0, rect.y0, rect.x1, rect.y1,
                                     exc_info=True)
                        return [], f"image-OCR skipped: Vision failed ({exc})"
                elif engine == "http":
                    # No geometry comes back, so the whole crop is one block.
                    # Fine for reading a figure's text; not precise enough to
                    # mask individual labels inside it.
                    try:
                        text = _ocr_http_call(png, f"img_p{pno + 1}.png", "image/png")
                    except Exception as exc:  # noqa: BLE001
                        return [], f"image-OCR skipped: OCR service failed ({exc})"
                    local = _http_lines(text, pno, rect)
                else:
                    from google.cloud import documentai_v1 as documentai  # type: ignore[import-not-found]

                    result = client.process_document(
                        request=documentai.ProcessRequest(
                            name=name,
                            raw_document=documentai.RawDocument(
                                content=png, mime_type="image/png"
                            ),
                        )
                    )
                    # crop-local coords → page coords
                    local = _lines_from_document(
                        result.document, 0, pno, rect.width, rect.height
                    )
                    for ln in local:
                        x0, y0, x1, y1 = ln.bbox
                        ln.bbox = (x0 + rect.x0, y0 + rect.y0,
                                   x1 + rect.x0, y1 + rect.y0)
                        for sp in ln.spans:
                            sp.bbox = ln.bbox

                for ln in local:
                    ln.in_image = True
                    if not worth_translating(ln):
                        # Part of the picture, not a label on it (a coin's motto,
                        # a mint date). Covering it would damage the artwork for
                        # a translation no reader was meant to read.
                        refused.append(ln.raw_text.strip())
                        continue
                    color = _sample_foreground_color(page, fitz.Rect(ln.bbox))
                    if color is not None:
                        for sp in ln.spans:
                            sp.color = color
                    ln.bbox = _pad_bbox(ln.bbox)
                    for sp in ln.spans:
                        sp.bbox = ln.bbox
                    lines.append(ln)
    finally:
        doc.close()

    count = sum(len(v) for v in regions.values())
    note = f"image-OCR ({engine}): {len(lines)} lines from {count} image(s)"
    if refused:
        # Named in the note so a reviewer can see what was left in place
        # and why, rather than silently finding untranslated text.
        note += (f"; {len(refused)} run(s) left as artwork: "
                 + ", ".join(repr(t) for t in refused[:8])
                 + (" ..." if len(refused) > 8 else ""))
    return lines, note


def merge_ocr_lines(base: list[Line], ocr: list[Line], overlap: float = 0.5) -> list[Line]:
    """Add OCR lines that do not duplicate text the PDF already exposed.

    `ocr_image_regions` reads a RENDER of the image's region rather than the
    image's own bytes, so ordinary PDF text drawn over a photo is read back as
    if it had been burned into it. Such a re-read is a duplicate of a run the
    pipeline already has, and keeping it means translating the same sentence
    twice and drawing both copies on the same spot.

    How much of the OCR line the PDF accounts for is summed over every line it
    covers, not taken from the best single one: OCR returns a wrapped sentence
    as ONE line, so on a real three-line speech bubble no single PDF line
    accounted for even a third of it while together they accounted for three
    quarters. Text genuinely struck into artwork is unaffected — a "GO!" beside
    a headline still scores under a quarter either way.
    """
    if not ocr:
        return base
    kept: list[Line] = []
    for ln in ocr:
        rect = fitz.Rect(ln.bbox)
        if rect.get_area() <= 0:
            continue
        covered = sum((rect & fitz.Rect(existing.bbox)).get_area()
                      for existing in base if existing.page == ln.page)
        if covered < rect.get_area() * overlap:
            kept.append(ln)
    return base + kept
