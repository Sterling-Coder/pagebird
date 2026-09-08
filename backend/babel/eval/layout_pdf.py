"""Layout-fidelity metrics for the PDF path — axis C.

Compares a source PDF against the translated PDF the reassembly stage produced.
Four measurements, kept separate on purpose:

  * `vector_preservation` — vector art (rules, diagrams, charts) that survived as
    vectors instead of being flattened to a raster. Not theoretical in this
    repo: `pipeline.pdf_to_idml` places equations as image crops and
    `reassemble.pdf` lifts stacked fractions off the page at 400 DPI. Anything
    rasterized is unusable for print and un-editable in InDesign.
  * `masked_pixel_similarity` — SSIM between rendered pages with *text regions
    masked out on both sides*. The masking is the whole point: the text is
    supposed to differ (it is Spanish now), so unmasked SSIM would score
    "how little did you translate". Masked, it scores what we mean — rules,
    images, tables, column structure, whitespace.
  * `block_iou` — did each source text box keep its position? Boxes are matched
    greedily by best overlap within a page, since translated lines re-wrap and
    will not be 1:1 with source lines.
  * `tofu` — characters the target font cannot render. These ship as empty boxes
    on the page while the extracted text still reads correctly, so no
    text-level check can see them. Mandatory before claiming a CJK target works.

`numpy` + `scikit-image` are needed only for `masked_pixel_similarity`; without
them that one metric reports `available: false` and the rest still run.
"""

from __future__ import annotations

import os

import fitz

from babel import languages
from babel.eval.integrity import restored

BBox = tuple[float, float, float, float]


# A matched box may sit lower than its source without overflowing: a taller
# script simply reports a taller line box. Half a line is the dividing line --
# below it the glyphs grew, above it the text gained a line.
_OVERFLOW_SLACK = 0.5


def _iou(a: BBox, b: BBox) -> float:
    ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
    ix1, iy1 = min(a[2], b[2]), min(a[3], b[3])
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _text_rects(page) -> list[BBox]:
    """Line-level bboxes of every text block on the page."""
    out: list[BBox] = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            if line.get("spans"):
                out.append(tuple(line["bbox"]))
    return out


# --- vector preservation ---------------------------------------------------


def vector_preservation(src_pdf: str, out_pdf: str) -> dict:
    """Vector drawing survival, plus how much content got rasterized.

    A drop in drawing count means redaction ate line art — exactly what
    `PDF_REDACT_LINE_ART_NONE` in `reassemble.pdf` exists to prevent, so this
    doubles as a regression check on that flag.
    """
    src, out = fitz.open(src_pdf), fitz.open(out_pdf)
    try:
        pages = min(src.page_count, out.page_count)
        per_page, src_draw, out_draw, src_img, out_img = [], 0, 0, 0, 0
        for pno in range(pages):
            sp, op = src.load_page(pno), out.load_page(pno)
            sd, od = len(sp.get_drawings()), len(op.get_drawings())
            si, oi = len(sp.get_images(full=True)), len(op.get_images(full=True))
            src_draw += sd
            out_draw += od
            src_img += si
            out_img += oi
            per_page.append({
                "page": pno + 1, "src_drawings": sd, "out_drawings": od,
                "lost_drawings": max(0, sd - od), "added_images": max(0, oi - si),
            })
        rate = min(1.0, out_draw / src_draw) if src_draw else None
        worst = sorted(per_page, key=lambda p: -p["lost_drawings"])[:10]
        return {
            "rate": round(rate, 4) if rate is not None else None,
            "src_drawings": src_draw,
            "out_drawings": out_draw,
            "lost_drawings": max(0, src_draw - out_draw),
            # New images in the output are content that used to be vector or live
            # text and is now a picture — the print-quality and editability risk.
            "rasterized_regions": max(0, out_img - src_img),
            "src_images": src_img,
            "out_images": out_img,
            "pages_compared": pages,
            "page_count_match": src.page_count == out.page_count,
            "worst_pages": [p for p in worst if p["lost_drawings"] or p["added_images"]],
        }
    finally:
        src.close()
        out.close()


# --- masked pixel similarity -----------------------------------------------


def masked_pixel_similarity(src_pdf: str, out_pdf: str, dpi: int = 100,
                            pages: int | None = None) -> dict:
    """SSIM per page with text regions masked to flat grey on both renders.

    The mask is the *union* of source and output text rects, applied to both
    images, so a Spanish line that grew wider cannot leak into the score through
    either side.
    """
    try:
        import numpy as np
        from skimage.metrics import structural_similarity
    except ImportError as exc:
        return {"mean": None, "available": False,
                "reason": f"pip install numpy scikit-image ({exc})"}

    src, out = fitz.open(src_pdf), fitz.open(out_pdf)
    try:
        count = min(src.page_count, out.page_count)
        if pages:
            count = min(count, pages)
        scale = dpi / 72.0
        scores, skipped = [], []

        def grey(page):
            pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
            buf = np.frombuffer(pix.samples, dtype=np.uint8)
            # Pixmap rows can be padded, so index through the real stride.
            return buf.reshape(pix.height, pix.stride)[:, : pix.width].copy()

        for pno in range(count):
            sp, op = src.load_page(pno), out.load_page(pno)
            a, b = grey(sp), grey(op)
            if a.shape != b.shape:
                skipped.append({"page": pno + 1, "reason": f"size {a.shape} vs {b.shape}"})
                continue
            h, w = a.shape
            for rect in _text_rects(sp) + _text_rects(op):
                x0 = max(0, int(rect[0] * scale) - 1)
                y0 = max(0, int(rect[1] * scale) - 1)
                x1 = min(w, int(rect[2] * scale) + 2)
                y1 = min(h, int(rect[3] * scale) + 2)
                if x1 > x0 and y1 > y0:
                    a[y0:y1, x0:x1] = 128
                    b[y0:y1, x0:x1] = 128
            scores.append({"page": pno + 1,
                           "ssim": round(float(structural_similarity(a, b, data_range=255)), 4)})

        vals = [s["ssim"] for s in scores]
        return {
            "mean": round(sum(vals) / len(vals), 4) if vals else None,
            "available": True,
            "dpi": dpi,
            "pages_scored": len(scores),
            "pages_skipped": skipped,
            "worst_pages": sorted(scores, key=lambda s: s["ssim"])[:10],
        }
    finally:
        src.close()
        out.close()


# --- block geometry --------------------------------------------------------


def block_iou(src_pdf: str, out_pdf: str, min_iou: float = 0.5) -> dict:
    """Per-page greedy best-overlap matching of source text boxes to output ones.

    Greedy rather than optimal (Hungarian) assignment: the boxes are already
    near-identical in position, so the assignment is not contested, and greedy
    avoids a scipy dependency for a division. `unmatched` counts source boxes
    with no output box above `min_iou` — text that moved, vanished, or merged.

    `overflow_estimate` counts matched boxes whose output text now extends below
    the source box, which is the reassembly overflow signal recomputed from the
    rendered document rather than trusted from the pipeline's own report.
    """
    src, out = fitz.open(src_pdf), fitz.open(out_pdf)
    try:
        pages = min(src.page_count, out.page_count)
        ious, unmatched, overflowed = [], [], 0
        for pno in range(pages):
            src_boxes = _text_rects(src.load_page(pno))
            out_boxes = _text_rects(out.load_page(pno))
            used: set[int] = set()
            for sb in src_boxes:
                best, best_i = 0.0, -1
                for i, ob in enumerate(out_boxes):
                    if i in used:
                        continue
                    score = _iou(sb, ob)
                    if score > best:
                        best, best_i = score, i
                if best_i >= 0 and best >= min_iou:
                    used.add(best_i)
                    # Tolerance scales with the line, not a fixed point value.
                    # Scripts differ in how tall a line box is for the same type
                    # size -- Devanagari carries vowel marks above and below the
                    # baseline -- so a fixed 1pt allowance reported a seventh of
                    # a Hindi page as overflowing when the median box sat only
                    # 1.6pt lower than its English source, on a 13.5pt line.
                    # Real overflow means the text gained a line, which puts the
                    # bottom edge a full line height lower, well past this.
                    height = sb[3] - sb[1]
                    if out_boxes[best_i][3] > sb[3] + max(1.0, height * _OVERFLOW_SLACK):
                        overflowed += 1
                else:
                    unmatched.append({"page": pno + 1, "bbox": [round(v, 1) for v in sb]})
                ious.append(best)
        total = len(ious)
        return {
            "mean": round(sum(ious) / total, 4) if total else None,
            "matched_rate": round((total - len(unmatched)) / total, 4) if total else None,
            "min_iou": min_iou,
            "src_boxes": total,
            "unmatched": len(unmatched),
            "overflow_estimate": round(overflowed / total, 4) if total else None,
            "overflowed_boxes": overflowed,
            "pages_compared": pages,
            "examples_unmatched": unmatched[:20],
        }
    finally:
        src.close()
        out.close()


# --- glyph coverage --------------------------------------------------------


def _first_existing(paths: list[str]) -> str | None:
    return next((p for p in paths if os.path.exists(p)), None)


# The metric has to model what reassembly does, so it uses reassembly's own
# substitution rather than a copy of it -- a second copy would drift.
from babel.reassemble.pdf import _drawable  # noqa: E402


def tofu(segments: list[dict], lang: str = "es") -> dict:
    """Characters the target's own face cannot render.

    Checks against the exact font `languages.py` resolves for this language —
    the same face `reassemble.pdf` would have drawn with — so a hit here is a
    character that shipped as an empty box. Math-font segments are excluded:
    the PDF path deliberately leaves those lines untouched.

    Reassembly substitutes a plain equivalent for any character the face cannot
    draw, so the question is what actually reaches the page, not what the stored
    target happens to contain. Testing the raw text reported the minus sign in
    "8 − 3 = 5" as unprintable on a page where it had already been drawn as a
    hyphen — a defect the pipeline had fixed, still being scored as present.
    """
    lang_def = languages.get(lang)
    path = _first_existing(lang_def.fonts.get("regular", []))
    if not path:
        return {"rate": None, "available": False,
                "reason": f"no font on this machine for {lang_def.code!r}: "
                          f"{lang_def.fonts.get('regular', [])}"}
    try:
        font = fitz.Font(fontfile=path)
    except Exception as exc:
        return {"rate": None, "available": False, "reason": f"{path}: {exc}"}

    missing: dict[str, int] = {}
    offenders, applicable = [], 0
    for s in segments:
        if s.get("has_math_font") or not (s.get("target") or "").strip():
            continue
        applicable += 1
        # Exactly what reassembly will draw, fallbacks already applied.
        text = _drawable(restored(s["target"], s["placeholders"]), font)
        bad = {ch for ch in text if not ch.isspace() and not font.has_glyph(ord(ch))}
        if bad:
            for ch in bad:
                missing[ch] = missing.get(ch, 0) + 1
            offenders.append({"seg_id": s["seg_id"], "page": s["page"],
                              "chars": sorted(bad), "target": text[:120]})
    return {
        "rate": round((applicable - len(offenders)) / applicable, 4) if applicable else None,
        "available": True,
        "font": os.path.basename(path),
        "applicable": applicable,
        "segments_with_tofu": len(offenders),
        "missing_chars": dict(sorted(missing.items(), key=lambda kv: -kv[1])[:20]),
        "examples": offenders[:20],
    }


# --- roll-up ---------------------------------------------------------------


def evaluate(src_pdf: str, out_pdf: str, segments: list[dict] | None = None,
             lang: str = "es", dpi: int = 100, pages: int | None = None,
             report: dict | None = None) -> dict:
    """Every axis-C PDF metric.

    `report` is an optional pipeline QA report (the `.report.json` written by the
    CLI). Its `overflow` list is ground truth from the reassembly stage; without
    it, `block_iou.overflow_estimate` stands in and is labelled as an estimate.
    """
    result = {
        "src": src_pdf,
        "out": out_pdf,
        "vector_preservation": vector_preservation(src_pdf, out_pdf),
        "masked_pixel_similarity": masked_pixel_similarity(src_pdf, out_pdf, dpi=dpi, pages=pages),
        "block_iou": block_iou(src_pdf, out_pdf),
        "tofu": tofu(segments or [], lang) if segments else
                {"rate": None, "available": False, "reason": "no segments supplied"},
    }
    if report is not None and "overflow" in report:
        total = report.get("segments_total") or len(report.get("overflow", [])) or 1
        result["overflow"] = {
            "rate": round(len(report["overflow"]) / total, 4),
            "count": len(report["overflow"]),
            "of_segments": total,
            "source": "pipeline report",
        }
    else:
        result["overflow"] = {
            "rate": result["block_iou"]["overflow_estimate"],
            "count": result["block_iou"]["overflowed_boxes"],
            "of_segments": result["block_iou"]["src_boxes"],
            "source": "estimated from rendered geometry — pass the pipeline "
                      "report for exact reassembly outcomes",
        }
    return result
