"""Translate image regions through the document pipeline's own core.

Each translatable region becomes an ordinary `Segment` and goes through the
same `Translator` the PDF and IDML paths use: translation memory, dedup, the
primary + secondary engines from `build_engines`, the placeholder integrity
gate and the glossary. Numbers, math, sub-part labels and never-translate names
are lifted out by `mathguard.protect_text`, exactly as on a page; a URL or an
email address inside a sentence is lifted out the same way, as a value-visible
name, so the engine can see it and cannot change it.
"""

from __future__ import annotations

import logging
import re

from pagebirdy.image.classify import EMAIL_RE, URL_RE
from pagebirdy.image.regions import TextRegion
from pagebirdy.models import Segment
from pagebirdy.protect.mathguard import Allocator, protect_text
from pagebirdy.translate.engine import build_engines
from pagebirdy.translate.translator import Translator

logger = logging.getLogger("pagebirdy.image.translate")

_TOKEN = re.compile(r"(⟦[^⟧]*⟧)")


def protect_region_text(text: str) -> tuple[str, dict[str, str]]:
    """`text` with every protected literal replaced by a placeholder."""
    alloc = Allocator()
    # Each pass runs only on the text between tokens already taken: the URL
    # pattern would otherwise find "shop2.com" inside "⟦~help@shop2.com⟧", and
    # the number scan would bite the "2" out of it.
    for step in (lambda p: EMAIL_RE.sub(lambda m: alloc.take_name(m.group(0)), p),
                 lambda p: URL_RE.sub(lambda m: alloc.take_name(m.group(0)), p),
                 lambda p: protect_text(p, alloc)):
        parts = _TOKEN.split(text)
        text = "".join(p if i % 2 else step(p) for i, p in enumerate(parts))
    return text, alloc.map


def to_segment(region: TextRegion) -> Segment:
    source, placeholders = protect_region_text(region.text)
    return Segment(
        id=region.id,
        page=0,
        bbox=region.bbox,
        font="OCR",
        size=float(region.render.get("font_px") or region.line_height),
        color=0,
        source=source,
        placeholders=placeholders,
        bboxes=list(region.lines) or [region.bbox],
        from_ocr=True,
        in_image=True,
    )


def _doc_context(regions: list[TextRegion]) -> str:
    """The largest text in the image — a title the engine can read the rest by."""
    if not regions:
        return ""
    return max(regions, key=lambda r: r.line_height).text[:120]


def translate_regions(regions: list[TextRegion], lang, *, engines=None) -> tuple[list[Segment], dict]:
    """Translate every region marked `translate`, in place.

    Returns the segments (for the review store) and engine metadata for the
    report. A region whose translation failed keeps `target=None` and is never
    redrawn — the original pixels stay rather than English being written back
    over English.
    """
    todo = [r for r in regions if r.action == "translate"]
    segments = [to_segment(r) for r in todo]
    if not segments:
        return [], {"engine_primary": None, "engine_secondary": None, "engine_failures": []}

    primary, secondary = engines or build_engines(doc_context=_doc_context(todo),
                                                  target_lang=lang.code)
    Translator(primary, secondary, target_lang=lang.code).run(segments)

    by_id = {s.id: s for s in segments}
    for r in todo:
        seg = by_id[r.id]
        r.engine = seg.engine
        r.notes = list(seg.notes)
        if seg.target is None:
            # The engine call itself failed, so nothing exists to draw.
            if seg.status == "needs_human":
                r.status = "needs_human"
                r.warnings.append("Translation rejected for review (" + "; ".join(seg.notes[-1:])
                                  + "); original text kept")
            else:
                r.status = "failed"
                r.warnings.append("Translation failed; original text kept")
            continue
        r.target = seg.restored_target()
        r.status = "needs_human" if seg.status == "needs_human" else "translated"
        if seg.status == "needs_human":
            r.warnings.append("Translation flagged for review: " + "; ".join(seg.notes[-2:]))

    meta = {
        "engine_primary": primary.name,
        "engine_secondary": secondary.name if secondary else None,
        "engine_failures": list(getattr(primary, "failures", []))[:10],
    }
    return segments, meta
