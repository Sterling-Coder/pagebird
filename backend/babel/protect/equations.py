"""Equation extraction — recognise the math, don't just hide it.

`mathguard.py` protects math by masking it: the translator never sees it and it
is restored verbatim. That is enough to be *safe*, but not enough to be
*correct* on this content. Extracting a worksheet PDF gives text like:

    "6⁴ · 6⁴"          ->  "64 • 64"
    "2⁹ / 2⁵"          ->  "29 ·· 25"
    "8ˣ/8⁵ = 8⁷"       ->  "8x ·· 85 5 87"     ('=' comes through as '5')

Superscripts collapse into the baseline and fraction bars become filler dots, so
the "protected literal" that gets restored is already wrong. This module renders
each equation region and sends it to Mathpix, which returns real LaTeX. The
LaTeX becomes the segment's source of truth, and the region is still masked from
the translator.

    MATHPIX_APP_ID=...   MATHPIX_APP_KEY=...

No credentials → regions are still detected and cropped (so you can see what
*would* be sent, and a human can fill them in), LaTeX is left None, and the
pipeline continues. Same graceful-degradation contract as the OCR layer.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field

import fitz

from babel.models import Line

# Glyphs that only appear in mathematical settings.
_MATH_CHARS = set("÷×±≤≥≠≈√∑∫∞πθαβγλμσΔ∂∇⁄·−–°∠⊥∥→⇒∈∉⊂∪∩")
_SUPERSCRIPT = set("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ⁿ")
_SUBSCRIPT = set("₀₁₂₃₄₅₆₇₈₉")
# "2x = 10", "y < 3" — a relational operator between operands.
_RELATION_RE = re.compile(r"[A-Za-z0-9)\]]\s*[=<>]\s*[-+(\[A-Za-z0-9]")
# The extractor's tell-tale fraction filler ("·····", "-----").
_FRACTION_FILLER_RE = re.compile(r"[·•.\-–—]{3,}")

MATHPIX_ENDPOINT = "https://api.mathpix.com/v3/text"

# Render resolution, per consumer. These are not interchangeable:
#   * Mathpix wants detail and improves with resolution.
#   * pix2tex was trained on arXiv-sized snippets and degrades badly when the
#     glyphs are large. Measured on grade8 p3 — at 110 dpi it reads
#     6^4*6^4 and \frac{2^9}{2^5} correctly; at 400 dpi the same crops come
#     back as \textstyle\bigcap\cdots and \underline{{{\gg}}} noise.
#   * The saved crop is human evidence, so it stays legible regardless.
MATHPIX_DPI = 400
PIX2TEX_DPI = 110      # swept 100-400; 110-120 peaks, 130+ degrades sharply
REVIEW_DPI = 300

# Digits the math font substitutes for symbols in the extracted text, so a
# mismatch on them means nothing: '2' is really a minus sign, '5' an equals.
_MATH_FONT_DIGIT_ARTEFACTS = ("2", "5")

# Worksheet problem numbers are knockout text: a white glyph on a dark circle.
# They sit immediately left of the expression, so a naive crop swallows them and
# the recogniser emits junk for the badge (pix2tex reads the disc as \oplus,
# \bigoplus, \stackrel...). Any near-white glyph is knockout by definition —
# white-on-white would be invisible — so colour is a reliable discriminator.
_KNOCKOUT_MIN_CHANNEL = 0xF0
# Clearance past the badge's right edge, in points — the disc overhangs the glyph.
_BADGE_MARGIN = 2.5


def is_badge_span(span) -> bool:
    """True for knockout glyphs (problem-number badges), not real content."""
    colour = int(span.color)
    r, g, b = (colour >> 16) & 0xFF, (colour >> 8) & 0xFF, colour & 0xFF
    return min(r, g, b) >= _KNOCKOUT_MIN_CHANNEL


def content_spans(line: Line) -> list:
    """The line's spans with problem-number badges removed."""
    return [s for s in line.spans if s.text.strip() and not is_badge_span(s)]


def content_bbox(line: Line):
    """Bbox of the real content, excluding any leading badge."""
    spans = content_spans(line)
    if not spans:
        return None
    return (
        min(s.bbox[0] for s in spans),
        min(s.bbox[1] for s in spans),
        max(s.bbox[2] for s in spans),
        max(s.bbox[3] for s in spans),
    )


def content_text(line: Line) -> str:
    return "".join(s.text for s in content_spans(line)).strip()


def badge_right_edge(line: Line) -> float | None:
    """Right edge of the problem-number badge, if this line starts with one.

    The dark disc is vector art drawn *behind* the white glyph and extends past
    it on both sides, so padding the crop left of the glyph drags the disc back
    in. Callers clamp their left edge to this value plus a small margin.
    """
    badges = [s for s in line.spans if s.text.strip() and is_badge_span(s)]
    if not badges:
        return None
    return max(s.bbox[2] for s in badges)


@dataclass
class EquationRegion:
    page: int
    bbox: tuple[float, float, float, float]
    raw_text: str
    latex: str | None = None
    confidence: float | None = None
    crop: str | None = None
    # Exact page rect the crop covers (padding and badge clamp applied), so the
    # image can be placed back at the position it was taken from.
    crop_bbox: tuple[float, float, float, float] | None = None
    engine: str | None = None
    lines: list[Line] = field(default_factory=list)
    # Hard left boundary for the crop: padding must not reach back over a
    # problem-number disc sitting immediately left of the expression.
    left_limit: float | None = None
    # False when the recognised LaTeX disagrees with the digits the PDF itself
    # reports — the segment is still usable, but a human should confirm it.
    verified: bool = True
    review_reason: str | None = None


def mathpix_configured() -> bool:
    return bool(os.getenv("MATHPIX_APP_ID") and os.getenv("MATHPIX_APP_KEY"))


def pix2tex_available() -> bool:
    """Local LaTeX-OCR — the no-key fallback named in the layer plan."""
    try:
        import pix2tex.cli  # noqa: F401  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001 — torch import can fail loudly, not just ImportError
        return False
    return True


def active_engine() -> str:
    """Which recogniser a run uses: structural | mathpix | pix2tex | none.

    `structural` reads the equation out of the PDF's own layout (see
    latex_builder) and is both exact and instant when the document uses a font
    family we have a glyph table for, so it leads. Image recognisers are the
    fallback for everything else.
    """
    forced = os.getenv("BABEL_EQUATION_ENGINE", "").lower()
    if forced in ("structural", "mathpix", "pix2tex", "none"):
        return forced
    return "structural"


def _fallback_engine() -> str:
    """Recogniser to use when structural reconstruction cannot read a region."""
    if mathpix_configured():
        return "mathpix"
    return "pix2tex" if pix2tex_available() else "none"


# --------------------------------------------------------------------------
# detection
# --------------------------------------------------------------------------

def badge_discs(page: fitz.Page) -> list[fitz.Rect]:
    """Filled problem-number discs on this page.

    The white glyph's bbox is narrower than the disc drawn behind it, so
    clamping to the glyph still leaves a dark crescent in the crop — which the
    recogniser dutifully turns into \\stackrel{\\wedge}{\\sim}. Match the disc
    itself: a small, filled, roughly square piece of vector art.
    """
    discs = []
    for drawing in page.get_drawings():
        if not drawing.get("fill"):
            continue
        rect = fitz.Rect(drawing["rect"])
        if not (6.0 <= rect.width <= 26.0 and 6.0 <= rect.height <= 26.0):
            continue
        if abs(rect.width - rect.height) > 4.0:  # discs are round, rules are not
            continue
        discs.append(rect)
    return discs


def fraction_bars(page: fitz.Page) -> list[fitz.Rect]:
    """Thin, short horizontal rules — in math typesetting, fraction bars."""
    bars = []
    for drawing in page.get_drawings():
        rect = fitz.Rect(drawing["rect"])
        if rect.height <= 2.5 and 3.0 <= rect.width <= 90.0:
            bars.append(rect)
    return bars


# A line with this many ordinary words is prose, whatever symbols it contains.
# "…that has a value of 10 at x = 10" trips the relational-operator test but is
# a sentence, and cropping it as an equation replaces readable text with a
# picture that can never be translated.
_MAX_PROSE_WORDS = 4


def is_prose(text: str) -> bool:
    words = [w for w in re.findall(r"[A-Za-z]{2,}", text)]
    return len(words) > _MAX_PROSE_WORDS


def looks_like_math(line: Line) -> bool:
    text = line.raw_text
    if not text.strip():
        return False
    if is_prose(text):
        return False
    if any(c in _MATH_CHARS or c in _SUPERSCRIPT or c in _SUBSCRIPT for c in text):
        return True
    if _FRACTION_FILLER_RE.search(text):
        return True
    if _RELATION_RE.search(text):
        return True
    if line.has_math_font:
        return True
    # A baseline shift inside one line means super/subscripts were flattened.
    sizes = {round(s.size, 1) for s in line.spans if s.text.strip()}
    return len(sizes) >= 2 and (max(sizes) - min(sizes)) >= 1.5 and len(text) < 200


def detect_regions(pdf_path: str, lines: list[Line]) -> list[EquationRegion]:
    """Group math-looking lines into regions, one per expression.

    Lines are clustered by touching (padded) boxes so a numerator, its fraction
    bar and the denominator end up in a single crop, while two problems printed
    side by side stay separate — Mathpix is markedly more accurate on one
    expression at a time.
    """
    doc = fitz.open(pdf_path)
    regions: list[EquationRegion] = []
    try:
        by_page: dict[int, list[Line]] = {}
        for ln in lines:
            if looks_like_math(ln):
                by_page.setdefault(ln.page, []).append(ln)

        for pno, page_lines in sorted(by_page.items()):
            page = doc.load_page(pno)
            bars = fraction_bars(page)
            discs = badge_discs(page)
            clusters: list[dict] = []
            for ln in sorted(page_lines, key=lambda l: (l.bbox[1], l.bbox[0])):
                # crop from the expression, not from the problem-number badge
                base = content_bbox(ln)
                if base is None:
                    continue
                rect = fitz.Rect(base) + (-7.0, -3.0, 7.0, 3.0)

                # never reach back over a problem-number badge
                limit: float | None = None
                edge = badge_right_edge(ln)
                if edge is not None:
                    limit = edge + _BADGE_MARGIN
                for disc in discs:
                    # same row, and sitting left of the expression
                    if disc.y1 < base[1] or disc.y0 > base[3]:
                        continue
                    if disc.x1 <= base[0] + _BADGE_MARGIN:
                        limit = max(limit or 0.0, disc.x1 + _BADGE_MARGIN)
                if limit is not None:
                    rect.x0 = max(rect.x0, limit)
                # a fraction bar glues the halves of a stacked fraction together
                for bar in bars:
                    if rect.intersects(bar):
                        rect |= bar + (-2.0, -4.0, 2.0, 4.0)
                hits = [c for c in clusters if c["rect"].intersects(rect)]
                if hits:
                    first = hits[0]
                    for other in hits[1:]:
                        first["rect"] |= other["rect"]
                        first["lines"] += other["lines"]
                        first["limit"] = _max_opt(first["limit"], other["limit"])
                        clusters.remove(other)
                    first["rect"] |= rect
                    first["lines"].append(ln)
                    first["limit"] = _max_opt(first["limit"], limit)
                else:
                    clusters.append({"rect": rect, "lines": [ln], "limit": limit})

            # Absorb stray fragments that touch a cluster. A trailing exponent
            # like the outer square of (7^5/7^2)^2 is its own tiny line holding
            # just "2"; nothing about it looks mathematical in isolation, so it
            # never gets flagged and the expression loses its exponent.
            flagged = {id(ln) for ln in page_lines}
            for ln in lines:
                if ln.page != pno or id(ln) in flagged:
                    continue
                base = content_bbox(ln)
                if base is None:
                    continue
                rect = fitz.Rect(base)
                if rect.width > 40.0 or len(content_text(ln)) > 6:
                    continue  # too big to be a fragment; leave prose alone
                for cluster in clusters:
                    if cluster["rect"].intersects(rect + (-3.0, -3.0, 3.0, 3.0)):
                        cluster["rect"] |= rect
                        cluster["lines"].append(ln)
                        break

            for cluster in clusters:
                tight = fitz.Rect()
                for ln in cluster["lines"]:
                    box = content_bbox(ln)
                    if box:
                        tight |= fitz.Rect(box)
                if tight.is_empty:
                    continue
                # A cluster of nothing but fraction-bar glyphs is a stray rule,
                # not an expression; cropping it yields a picture of a dash.
                from babel.protect.latex_builder import is_fraction_bar

                if all(is_fraction_bar(s)
                       for ln in cluster["lines"] for s in content_spans(ln)):
                    continue
                regions.append(EquationRegion(
                    page=pno,
                    bbox=tuple(tight),
                    raw_text=" ".join(
                        t for t in (content_text(l) for l in cluster["lines"]) if t
                    ).strip(),
                    lines=cluster["lines"],
                    left_limit=cluster["limit"],
                ))
    finally:
        doc.close()
    return regions


# --------------------------------------------------------------------------
# recognition
# --------------------------------------------------------------------------

def verify_against_pdf(region: EquationRegion) -> tuple[bool, str | None]:
    """Cross-check recognised LaTeX against the digits the PDF reports.

    Neither source is ground truth: the PDF text is structurally corrupt (it
    flattens superscripts and renders math-font glyphs as the wrong ASCII —
    'minus' arrives as '2', '=' as '5'), and the recogniser mis-reads digits
    inside superscripts. But they fail *independently*, so a disagreement is a
    reliable signal that one of them is wrong, which is what a reviewer needs.

    Digits that the math font is known to corrupt are excluded before
    comparing, so the usual '2'-for-minus artefact does not raise a false alarm.
    """
    if not region.latex:
        return True, None

    pdf_digits = Counter(re.findall(r"\d", region.raw_text))
    tex_digits = Counter(re.findall(r"\d", region.latex))

    # The math font substitutes these; ignore them on both sides.
    for artefact in _MATH_FONT_DIGIT_ARTEFACTS:
        pdf_digits.pop(artefact, None)
        tex_digits.pop(artefact, None)

    if pdf_digits == tex_digits:
        return True, None
    missing = pdf_digits - tex_digits
    extra = tex_digits - pdf_digits
    parts = []
    if missing:
        parts.append(f"digits in PDF not in LaTeX: {sorted(missing.elements())}")
    if extra:
        parts.append(f"digits in LaTeX not in PDF: {sorted(extra.elements())}")
    return False, "; ".join(parts)


def _max_opt(a: float | None, b: float | None) -> float | None:
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


def _clip_rect(page: fitz.Page, region: EquationRegion, pad: float = 4.0) -> fitz.Rect:
    rect = (fitz.Rect(region.bbox) + (-pad, -pad, pad, pad)) & page.rect
    if region.left_limit is not None:
        rect.x0 = max(rect.x0, region.left_limit)
    return rect


def _crop(pdf_path: str, region: EquationRegion, out_dir: str,
          dpi: int = REVIEW_DPI, pad: float = 4.0) -> str:
    """Write the reviewable crop and return its path."""
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    try:
        page = doc.load_page(region.page)
        path = os.path.join(
            out_dir,
            f"eq_p{region.page + 1:03d}_{int(region.bbox[1])}_{int(region.bbox[0])}.png",
        )
        clip = _clip_rect(page, region, pad)
        region.crop_bbox = tuple(clip)
        page.get_pixmap(clip=clip, dpi=dpi).save(path)
        return path
    finally:
        doc.close()


def _render_png(pdf_path: str, region: EquationRegion, dpi: int,
                pad: float = 4.0) -> bytes:
    """Render the region at an engine-specific resolution, in memory."""
    doc = fitz.open(pdf_path)
    try:
        page = doc.load_page(region.page)
        pix = page.get_pixmap(clip=_clip_rect(page, region, pad), dpi=dpi)
        return pix.tobytes("png")
    finally:
        doc.close()


def _mathpix(data: bytes, cache: dict, key: str) -> dict | None:
    import requests  # type: ignore[import-not-found]

    if key in cache:
        return cache[key]

    resp = requests.post(
        MATHPIX_ENDPOINT,
        headers={
            "app_id": os.getenv("MATHPIX_APP_ID"),
            "app_key": os.getenv("MATHPIX_APP_KEY"),
            "Content-Type": "application/json",
        },
        json={
            "src": "data:image/png;base64," + base64.b64encode(data).decode(),
            "formats": ["text", "latex_styled"],
            "data_options": {"include_latex": True},
            "rm_spaces": True,
        },
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()
    out = {
        "latex": payload.get("latex_styled") or payload.get("text") or "",
        "confidence": payload.get("confidence"),
    }
    cache[key] = out
    return out


class _Pix2Tex:
    """Lazy singleton around LaTeX-OCR: the model loads once, then runs per crop.

    First use downloads model weights (~100 MB) into the pix2tex package dir.
    CPU inference is roughly 0.3-1 s per equation, so a 200-equation packet is
    a couple of minutes — slower than Mathpix, but free and offline.
    """

    _model = None

    @classmethod
    def get(cls):
        if cls._model is None:
            from pix2tex.cli import LatexOCR  # type: ignore[import-not-found]

            cls._model = LatexOCR()
        return cls._model

    @classmethod
    def latex(cls, png_bytes: bytes) -> str:
        import io

        from PIL import Image  # type: ignore[import-not-found]

        with Image.open(io.BytesIO(png_bytes)) as img:
            return cls.get()(img.convert("RGB"))


def recognise(pdf_path: str, regions: list[EquationRegion], out_dir: str,
              limit: int | None = None, engine: str | None = None) -> str:
    """Crop every region and recognise it. Returns a status note.

    Engine order: Mathpix when its keys are set (fastest, best accuracy), else
    local pix2tex (no key, no network), else crops only. Crops are always
    written — they are the evidence a reviewer needs and the input for a later
    re-run. `limit` caps how many crops get recognised (Mathpix billing, or
    pix2tex runtime).
    """
    if not regions:
        return "equations: none detected"

    crop_dir = os.path.join(out_dir, "equations")
    cache_path = os.path.join(out_dir, "equation_cache.json")
    cache: dict = {}
    if os.path.exists(cache_path):
        try:
            cache = json.loads(open(cache_path, encoding="utf-8").read())
        except (ValueError, OSError):
            cache = {}

    engine = engine or active_engine()
    if engine == "mathpix":
        try:
            import requests  # noqa: F401  # type: ignore[import-not-found]
        except ImportError:
            engine = "pix2tex" if pix2tex_available() else "none"

    done = 0
    failures = 0
    structural = 0
    for region in regions:
        region.crop = _crop(pdf_path, region, crop_dir)
        if engine == "none" or (limit is not None and done >= limit):
            continue

        if engine == "structural":
            from babel.protect.latex_builder import build_latex, latex_confidence

            latex = build_latex(region.lines)
            if latex and latex_confidence(latex, region.raw_text) >= 0.8:
                region.latex = latex
                region.confidence = 1.0
                region.engine = "structural"
                # No cross-check here: this LaTeX was read from the same spans
                # the check would compare it against, so the test is circular.
                # Worse, it would fire constantly by design — structural output
                # correctly renders the math-font digit '3' as \times, which
                # reads as a "missing digit" to a digit-multiset comparison.
                region.verified, region.review_reason = True, None
                for ln in region.lines:
                    ln.latex = latex
                structural += 1
                done += 1
                continue
            # unreadable structurally — fall through to an image recogniser
            fallback = _fallback_engine()
            if fallback == "none":
                continue
            region.engine = fallback
            dpi = MATHPIX_DPI if fallback == "mathpix" else PIX2TEX_DPI
            png = _render_png(pdf_path, region, dpi)
            key = f"{fallback}:{hashlib.sha1(png).hexdigest()}"
            try:
                if key in cache:
                    result = cache[key]
                elif fallback == "mathpix":
                    result = _mathpix(png, cache, key)
                else:
                    result = {"latex": _Pix2Tex.latex(png), "confidence": None}
                    cache[key] = result
            except Exception:  # noqa: BLE001
                failures += 1
                continue
            region.latex = (result or {}).get("latex") or None
            region.confidence = (result or {}).get("confidence")
            if region.latex:
                region.verified, region.review_reason = verify_against_pdf(region)
                for ln in region.lines:
                    ln.latex = region.latex
                done += 1
            continue

        dpi = MATHPIX_DPI if engine == "mathpix" else PIX2TEX_DPI
        png = _render_png(pdf_path, region, dpi)
        # engine is part of the key: the two read different renders
        key = f"{engine}:{hashlib.sha1(png).hexdigest()}"
        if key in cache:
            region.latex = cache[key].get("latex") or None
            region.confidence = cache[key].get("confidence")
        else:
            try:
                if engine == "mathpix":
                    result = _mathpix(png, cache, key)
                else:
                    result = {"latex": _Pix2Tex.latex(png), "confidence": None}
                    cache[key] = result
            except Exception:  # noqa: BLE001 — a bad crop must not kill the run
                failures += 1
                continue
            region.latex = (result or {}).get("latex") or None
            region.confidence = (result or {}).get("confidence")

        if region.latex:
            region.verified, region.review_reason = verify_against_pdf(region)
            for ln in region.lines:
                ln.latex = region.latex
            done += 1

    if cache:
        os.makedirs(out_dir, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)

    got = sum(1 for r in regions if r.latex)
    if engine == "none":
        hint = ("set MATHPIX_APP_ID/MATHPIX_APP_KEY, or `pip install pix2tex` "
                "for the free local model")
        return (f"equations: {len(regions)} detected, crops in {crop_dir}; "
                f"no recogniser available — {hint}")
    flagged = sum(1 for r in regions if r.latex and not r.verified)
    if engine == "structural" and structural < got:
        engine = f"structural ({structural}) + fallback ({got - structural})"
    note = f"equations: {len(regions)} detected, {got} recognised via {engine}"
    if flagged:
        note += f", {flagged} disagree with the PDF text (review these)"
    if failures:
        note += f" ({failures} failed)"
    return note


def extract_equations(pdf_path: str, lines: list[Line], out_dir: str,
                      limit: int | None = None,
                      engine: str | None = None) -> tuple[list[EquationRegion], str]:
    """Detect + recognise in one call. Mutates `lines` to carry their LaTeX."""
    regions = detect_regions(pdf_path, lines)
    note = recognise(pdf_path, regions, out_dir, limit=limit, engine=engine)
    return regions, note
