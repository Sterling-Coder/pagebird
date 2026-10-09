"""Fit translated text inside the shape the designer drew.

In order: the source size wrapped across the frame's own width; then line
spacing down to 90%; then whole-point shrink, never more than 30% below the
source and never under 8pt; anything still over is reported as a warning
("Text overflow on slide N"), not hidden. A shape is never moved or resized.
Frames PowerPoint fits itself (`normAutofit`), frames the designer set to grow
(`spAutofit`), unwrapped and vertical text are left alone.

Measurement uses the target language's bundled face (bold where the
paragraph is mostly bold) at 95% of the usable width, without shaping, so it
errs towards shrinking rather than towards overflowing. Text in a table cell
is not fitted: PowerPoint grows the row to its text.
"""

from __future__ import annotations

import math
from functools import lru_cache

from lxml import etree
from PIL import ImageFont

from pagebirdy import fonts as pagebirdy_fonts
from pagebirdy.office.adapter import Issue

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
EMU_PER_PT = 12700
MIN_PT, MAX_SHRINK, MIN_SPACING, WIDTH_MARGIN = 8.0, 0.30, 0.90, 0.95
DEFAULT_PT = 18.0
LINE = 1.2  # single line spacing as a multiple of the type size
_INSETS = {"lIns": 91440, "tIns": 45720, "rIns": 91440, "bIns": 45720}


# --- what PowerPoint would use when a paragraph does not say ----------------

def _lvl(p) -> int:
    ppr = p.find(A + "pPr") if p is not None else None
    return int(ppr.get("lvl", "0")) + 1 if ppr is not None else 1


def _levels(container, lvl: int):
    """`a:lvlNpPr` of a list style (`a:lstStyle`, `p:titleStyle`…), then lvl1."""
    if container is None:
        return
    for tag in dict.fromkeys((f"{A}lvl{lvl}pPr", f"{A}lvl1pPr")):
        el = container.find(tag)
        if el is not None:
            yield el


def _placeholder_body(shape):
    body = shape._element.find(f".//{P}txBody")
    return body if body is not None else shape._element.find(f".//{A}txBody")


def _inherited_levels(slide, shape, p):
    """Every paragraph-level style a paragraph inherits from, nearest first:
    its frame's list style, the matching layout and master placeholders, then
    the master's title/body/other text style."""
    lvl = _lvl(p)
    yield from _levels(p.getparent().find(A + "lstStyle"), lvl)
    kind = "other"
    try:
        if shape.is_placeholder:
            fmt = shape.placeholder_format
            ptype = str(getattr(fmt.type, "name", "") or "").lower()
            kind = "title" if "title" in ptype else "body"
            layout = slide.slide_layout
            for holder in (layout.placeholders, layout.slide_master.placeholders):
                for ph in holder:
                    if ph.placeholder_format.idx == fmt.idx or (
                            kind == "title" and ph.placeholder_format.type == fmt.type):
                        body = _placeholder_body(ph)
                        if body is not None:
                            yield from _levels(body.find(A + "lstStyle"), lvl)
                        break
        styles = slide.slide_layout.slide_master._element.find(P + "txStyles")
        if styles is not None:
            tag = {"title": "titleStyle", "body": "bodyStyle"}.get(kind, "otherStyle")
            yield from _levels(styles.find(P + tag), lvl)
    except (AttributeError, ValueError, KeyError):
        return


def resolved_size(slide, shape, run) -> float:
    """The size a run renders at: its own `sz`, else what its paragraph and
    the styles above it say, else PowerPoint's 18pt."""
    rpr = run.find(A + "rPr")
    if rpr is not None and rpr.get("sz"):
        return int(rpr.get("sz")) / 100.0
    p = run.getparent()
    ppr = p.find(A + "pPr")
    candidates = [ppr] if ppr is not None else []
    for level in candidates + list(_inherited_levels(slide, shape, p)):
        d = level.find(A + "defRPr")
        if d is not None and d.get("sz"):
            return int(d.get("sz")) / 100.0
    return DEFAULT_PT


def resolved_algn(slide, shape, p) -> str:
    """The alignment a paragraph renders with (`l`, `ctr`, `r`, `just`…):
    its own `algn`, else the nearest style's, else PowerPoint's `l`."""
    ppr = p.find(A + "pPr")
    if ppr is not None and ppr.get("algn"):
        return ppr.get("algn")
    for level in _inherited_levels(slide, shape, p):
        if level.get("algn"):
            return level.get("algn")
    return "l"


# --- measuring ---------------------------------------------------------------

@lru_cache(maxsize=64)
def _font(path: str, size10: int):
    return ImageFont.truetype(path, size10)


@lru_cache(maxsize=32)
def _face(code: str, bold: bool) -> str | None:
    from pagebirdy import languages
    lang = languages.get(code)
    for style in (("bold", "regular") if bold else ("regular",)):
        path = pagebirdy_fonts.resolve(tuple(lang.fonts.get(style, ())))
        if path:
            return path
    return pagebirdy_fonts.resolve(("LiberationSans-Regular.ttf",))


def _width(text: str, size: float, face: str | None) -> float:
    if not face:
        return len(text) * size * 0.55
    return _font(face, max(10, int(round(size * 10)))).getlength(text) / 10.0


def _lines(text: str, size: float, width: float, face, char_wrap: bool) -> int:
    count = 0
    for para in text.split("\n"):
        units = list(para) if char_wrap else para.split(" ")
        joiner = "" if char_wrap else " "
        line, n = "", 1
        for u in units:
            trial = (line + joiner + u) if line else u
            if not line or _width(trial, size, face) <= width:
                line = trial
            else:
                n, line = n + 1, u
        count += n
    return count


def _spacing_pct(p) -> float:
    el = p.find(f"{A}pPr/{A}lnSpc/{A}spcPct")
    return int(el.get("val")) / 100000.0 if el is not None else 1.0


def _space_pts(p, tag: str) -> float:
    el = p.find(f"{A}pPr/{A}{tag}/{A}spcPts")
    return int(el.get("val")) / 100.0 if el is not None else 0.0


class _Frame:
    """A text frame measured the way `fit_frame` measures it."""

    def __init__(self, slide, shape, body, lang):
        self.ok = False
        body_pr = body.find(A + "bodyPr")
        if body_pr is not None and (
                body_pr.find(A + "normAutofit") is not None or body_pr.find(A + "spAutofit") is not None
                or body_pr.get("wrap") == "none" or body_pr.get("vert", "horz") != "horz"):
            return
        ins = {k: int(body_pr.get(k, d)) if body_pr is not None else d for k, d in _INSETS.items()}
        if not shape.width or not shape.height:
            return
        self.width = (shape.width - ins["lIns"] - ins["rIns"]) / EMU_PER_PT * WIDTH_MARGIN
        self.height = (shape.height - ins["tIns"] - ins["bIns"]) / EMU_PER_PT
        if self.width <= 0 or self.height <= 0:
            return
        self.paras, self.runs = [], []
        for p in body.findall(A + "p"):
            rs = p.findall(A + "r")
            text = "".join(r.findtext(A + "t") or "" for r in rs)
            sizes = [resolved_size(slide, shape, r) for r in rs]
            bold_chars = sum(len(r.findtext(A + "t") or "") for r in rs
                             if r.find(A + "rPr") is not None and r.find(A + "rPr").get("b") == "1")
            self.paras.append((p, text, max(sizes) if sizes else DEFAULT_PT, bold_chars * 2 > len(text)))
            self.runs.extend(zip(rs, sizes))
        self.lang = lang
        self.ok = bool(self.runs)

    def total(self, scale: float, spacing: float) -> float:
        h = 0.0
        char_wrap = self.lang.wrapping == "char"
        for p, text, size, bold in self.paras:
            s = size * scale
            n = _lines(text, s, self.width, _face(self.lang.code, bold), char_wrap) if text else 1
            h += n * s * LINE * _spacing_pct(p) * spacing + _space_pts(p, "spcBef") + _space_pts(p, "spcAft")
        return h


def needed_height(slide, shape, body, lang) -> float | None:
    """What the frame's current text needs, by the same estimate fitting uses
    — called on the source before it is rewritten."""
    frame = _Frame(slide, shape, body, lang)
    return frame.total(1.0, 1.0) if frame.ok else None


def fit_frame(slide, shape, body, slide_no: int, lang, source_needed: float | None = None
              ) -> Issue | None:
    """Fit the frame's (translated) text. `source_needed` is what the source
    text measured at: the room a frame has is never less than that, so an
    estimate that already called the English too tall cannot shrink a
    translation that is no longer than it."""
    frame = _Frame(slide, shape, body, lang)
    if not frame.ok:
        return None
    height = max(frame.height, source_needed or 0.0)
    runs, paras, total = frame.runs, frame.paras, frame.total
    largest = max(size for _, _, size, _ in paras)

    if total(1.0, 1.0) <= height:
        return None
    if total(1.0, MIN_SPACING) <= height:
        _apply(body, runs, 1.0, MIN_SPACING)
        return None
    floor = max(largest * (1 - MAX_SHRINK), MIN_PT)
    for pt in range(math.ceil(largest) - 1, math.ceil(floor) - 1, -1):
        if pt < floor:
            break
        if total(pt / largest, MIN_SPACING) <= height:
            _apply(body, runs, pt / largest, MIN_SPACING)
            return None
    _apply(body, runs, floor / largest, MIN_SPACING)
    return Issue("warning", "overflow", f"slide {slide_no}",
                 f"text in shape {shape.shape_id} still overflows at {round(floor, 1)}pt")


def _apply(body, runs, scale: float, spacing: float) -> None:
    if spacing < 1.0:
        for p in body.findall(A + "p"):
            ppr = p.find(A + "pPr")
            if ppr is None:
                ppr = etree.Element(A + "pPr")
                p.insert(0, ppr)
            ln = ppr.find(A + "lnSpc")
            if ln is None:
                ln = etree.Element(A + "lnSpc")
                ppr.insert(0, ln)
                etree.SubElement(ln, A + "spcPct", val=str(int(spacing * 100000)))
            else:
                pct = ln.find(A + "spcPct")
                if pct is not None:
                    pct.set("val", str(int(int(pct.get("val")) * spacing)))
    if scale < 1.0:
        for r, size in runs:
            rpr = r.find(A + "rPr")
            if rpr is None:
                rpr = etree.Element(A + "rPr")
                r.insert(0, rpr)
            rpr.set("sz", str(int(round(size * scale * 100))))
