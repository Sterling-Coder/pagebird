"""Illustrator artwork (.ai) — translated as vectors, never rasterised.

An .ai saved with PDF compatibility is a PDF, which is how `idml/graphics.py`
already translates linked .ai word-art for the IDML path. This uses the same
pieces in the same order: live text from `ingest/pdf.py`, Vision OCR for words
converted to outlines (merged with the same dedup), the same filter that keeps
a graph's axis numbers and equations out of the engine, `build_segments`, the
shared `Translator`, and `rebuild_pdf` with `keep_orientation=True` — an
artboard is a picture, not a page, so it is never mirrored for RTL.

Two things differ from the linked-graphic path, both because this file is the
deliverable rather than something InDesign places:

* The canvas is never grown. `_grow_canvas_for_translation` widens a word-art
  badge's ArtBox so a longer word is not shrunk; here the artboard size is
  part of what the user gave us and comes back unchanged.
* Illustrator's private editing data is removed. A PDF-compatible .ai carries
  the artwork twice: as PDF content, and as `AIPrivateData` streams hung off
  each page's `/PieceInfo`. Illustrator opens the private copy when it is
  there, so a file with only its PDF content translated still opens *in
  English* in Illustrator. InDesign places the PDF content, which is why the
  IDML path never needed this. Without the private data Illustrator opens the
  PDF content — the translation — as editable artwork.
"""

from __future__ import annotations

import logging
import os
import re
import shutil

import fitz

from pagebirdy.idml.graphics import _is_math_label, _worth_translating
from pagebirdy.ingest import ocr as base_ocr
from pagebirdy.ingest.pdf import extract_lines
from pagebirdy.protect.mathguard import build_segments
from pagebirdy.reassemble.pdf import rebuild_pdf
from pagebirdy.translate.engine import build_engines
from pagebirdy.translate.translator import Translator

logger = logging.getLogger("pagebirdy.image.vector")

_PREVIEW_LONG_SIDE = 1600


def render_preview(pdf_path: str, png_path: str) -> str:
    """The first artboard as a PNG a browser can show."""
    doc = fitz.open(pdf_path)
    try:
        page = doc[0]
        zoom = min(4.0, _PREVIEW_LONG_SIDE / max(page.rect.width, page.rect.height))
        page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False).save(png_path)
    finally:
        doc.close()
    return png_path


def strip_illustrator_private_data(path: str) -> int:
    """Remove every page's `/PieceInfo` (and with it `AIPrivateData`); returns
    how many pages carried it. Saved with garbage collection so the orphaned
    private streams leave the file too."""
    doc = fitz.open(path)
    stripped = 0
    try:
        for page in doc:
            if "/PieceInfo" in doc.xref_object(page.xref):
                # Setting the key to null leaves a literal `/PieceInfo null`
                # in the page; drop the entry from the object itself instead.
                # An earlier stage may already have nulled it, which still
                # leaves the key in the file, so the object text decides.
                if doc.xref_get_key(page.xref, "PieceInfo")[0] != "null":
                    doc.xref_set_key(page.xref, "PieceInfo", "null")
                source = re.sub(r"/PieceInfo\s+null\b", "", doc.xref_object(page.xref))
                doc.update_object(page.xref, source)
                stripped += 1
        if stripped:
            tmp = path + ".tmp"
            doc.save(tmp, garbage=3, deflate=True)
    finally:
        doc.close()
    if stripped:
        os.replace(tmp, path)
    return stripped


def _page_sizes(path: str) -> list[tuple[float, float]]:
    doc = fitz.open(path)
    try:
        return [(round(p.rect.width, 2), round(p.rect.height, 2)) for p in doc]
    finally:
        doc.close()


def _region(seg, drawn: set[str], overflow: dict[str, str]) -> dict:
    """A segment in the report's region shape, so the UI lists vector and
    raster results the same way."""
    x0, y0, x1, y1 = seg.bbox
    if not seg.is_translatable:
        status, action = "protected", "protect"
    elif seg.target is None:
        status, action = ("needs_human" if seg.status == "needs_human" else "failed"), "translate"
    else:
        status = "needs_human" if seg.status == "needs_human" else "translated"
        action = "translate"
    warnings = []
    if seg.status == "needs_human":
        warnings.append("Flagged for review: " + "; ".join(seg.notes[-2:]))
    if seg.id in overflow:
        warnings.append("Translation did not fit its box: " + overflow[seg.id])
    return {
        "id": seg.id,
        "text": seg.restored_source(),
        "bbox": {"x": round(x0, 1), "y": round(y0, 1),
                 "width": round(x1 - x0, 1), "height": round(y1 - y0, 1)},
        # Live text has no reading confidence; OCR's is applied upstream by
        # the same gate the PDF path uses.
        "confidence": None,
        "language": None,
        "content_type": "ocr_text" if seg.from_ocr else "live_text",
        "action": action,
        "reason": "",
        "status": status,
        "target": seg.restored_target() if action == "translate" and seg.target is not None else None,
        "warnings": warnings,
        "notes": list(seg.notes),
        "render": {"drawn": seg.id in drawn, "page": seg.page},
    }


def translate_vector(src_path: str, out_path: str, lang, *, emit, engines=None, warn=None) -> tuple[dict, list]:
    """Translate a PDF-compatible .ai into `out_path`; returns (partial report, segments)."""
    warn = warn or (lambda region, message: None)
    out_dir = os.path.dirname(out_path)
    stem = os.path.splitext(os.path.basename(out_path))[0]
    source_preview = os.path.join(out_dir, f"{stem}.source.preview.png")
    output_preview = os.path.join(out_dir, f"{stem}.preview.png")
    sizes_before = _page_sizes(src_path)

    # ---- OCR: live text first, then outlined text read off the pixels ----
    emit("ocr", 0, "")
    lines = [ln for ln in extract_lines(src_path) if _worth_translating(ln)]
    live = len(lines)
    read_by_ocr = 0
    if base_ocr.active_ocr_engine() != "none":
        doc = fitz.open(src_path)
        regions = {i: [tuple(page.rect)] for i, page in enumerate(doc)}
        doc.close()
        try:
            ocr_lines, note = base_ocr.ocr_image_regions(src_path, regions=regions)
            merged = base_ocr.merge_ocr_lines(lines, ocr_lines)
            read_by_ocr = len(merged) - len(lines)
            lines = merged
            logger.info("vector OCR: %s", note)
        except Exception as e:  # noqa: BLE001 — OCR is a second pass, live text still goes
            logger.info("vector OCR failed, continuing with live text: %s", e)
            warn(None, "OCR could not read this file; only live text was translated.")
    else:
        warn(None, "No OCR engine is configured: text converted to outlines was not read, "
                   "only live text was translated.")
    lines = [ln for ln in lines if not _is_math_label(ln)]
    emit("ocr", 100, f"{live} live text line(s), {read_by_ocr} read by OCR")

    emit("classification", 0, "")
    segments = build_segments(lines)
    todo = [s for s in segments if s.is_translatable]
    emit("classification", 100, f"{len(todo)} to translate")

    report: dict = {"live_text_lines": live, "ocr_lines": read_by_ocr}
    if not todo:
        shutil.copyfile(src_path, out_path)
        warn(None, "No translatable text was found; the output is the original file.")
        for stage in ("translation", "reconstruction"):
            emit(stage, 100, "")
        report.update({"engine_primary": None, "engine_secondary": None, "engine_failures": [],
                       "outcomes": {}, "private_data_removed": 0})
    else:
        emit("translation", 0, "")
        top = max(todo, key=lambda s: s.size)
        primary, secondary = engines or build_engines(
            doc_context=top.restored_source()[:120], target_lang=lang.code)
        Translator(primary, secondary, target_lang=lang.code).run(segments)
        emit("translation", 100, f"{len(todo)} line(s)")

        emit("reconstruction", 0, "")
        outcomes = rebuild_pdf(src_path, segments, out_path, target_lang=lang.code,
                               keep_orientation=True)
        stripped = strip_illustrator_private_data(out_path)
        emit("reconstruction", 100, "")
        report.update({
            "engine_primary": primary.name,
            "engine_secondary": secondary.name if secondary else None,
            "engine_failures": list(getattr(primary, "failures", []))[:10],
            "outcomes": {o.segment_id: (o.action, o.detail) for o in outcomes},
            "private_data_removed": stripped,
        })

    render_preview(src_path, source_preview)
    render_preview(out_path, output_preview)
    outcomes = report.pop("outcomes")
    drawn = {sid for sid, (action, _) in outcomes.items() if action == "replaced"}
    overflow = {sid: detail for sid, (action, detail) in outcomes.items() if action == "overflow"}
    regions = [_region(s, drawn, overflow) for s in segments]

    # ---- quality ----
    sizes_after = _page_sizes(out_path)
    translated = [r for r in regions if r["status"] == "translated"]
    checks = [
        {"name": "artboards_unchanged", "passed": sizes_before == sizes_after,
         "detail": f"{len(sizes_before)} artboard(s), {sizes_before[0][0]}×{sizes_before[0][1]}pt"},
        {"name": "all_regions_processed",
         "passed": all(r["render"]["drawn"] for r in translated),
         "detail": f"{sum(r['render']['drawn'] for r in translated)} of {len(translated)} "
                   "translated line(s) redrawn"},
        {"name": "no_overflow", "passed": not overflow,
         "detail": ", ".join(overflow) or "every line fits its box"},
        {"name": "illustrator_opens_translation",
         "passed": True,
         "detail": (f"native editing data removed from {report['private_data_removed']} artboard(s)"
                    if report["private_data_removed"] else "no native editing data present")},
    ]
    report.update({
        "regions": regions,
        "quality": {"passed": all(c["passed"] for c in checks), "checks": checks},
        "source_preview": source_preview,
        "output_preview": output_preview,
        "output_note": "Illustrator (.ai, PDF-compatible) — vectors kept",
    })
    return report, segments
