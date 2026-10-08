"""Set translated text into a region and rasterise it as a coverage mask.

Type is set by MuPDF (`insert_htmlbox`), the engine the PDF path already draws
every target script with: it shapes Arabic and Hebrew, applies the bidi
algorithm, joins letters and wraps on spaces. Pillow cannot do any of that
without libraqm, which the deployed wheels do not ship.

The text is drawn alone, on a transparent page exactly the size of the region,
at one PDF point per image pixel, and only its alpha channel is kept. The
colour is applied when the mask is composited, so the rasteriser's
premultiplied colour never enters the image.
"""

from __future__ import annotations

import html
import os
from dataclasses import dataclass
from functools import lru_cache

import fitz
import numpy as np

from pagebirdy import fonts as pagebirdy_fonts
from pagebirdy.image import rtl

_LATIN = (["LiberationSans-Regular.ttf", "C:/Windows/Fonts/arial.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
          ["LiberationSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"])
# Tolerance, in pixels, for a glyph's box grazing the region edge.
_EDGE_SLACK = 0.75


@dataclass(frozen=True)
class FontSet:
    regular: str | None
    bold: str | None
    latin_regular: str | None
    latin_bold: str | None


def font_set(lang) -> FontSet:
    """The target language's own faces (languages.py), plus a Latin face for
    the URLs, numbers and names that stay in Latin inside any translation.
    `BABEL_IMAGE_FONT` overrides the target face for every language."""
    override = os.getenv("BABEL_IMAGE_FONT")
    regular = override if override and os.path.exists(override) else \
        pagebirdy_fonts.resolve(lang.fonts.get("regular", ()))
    bold = pagebirdy_fonts.resolve(lang.fonts.get("bold", ())) or regular
    return FontSet(regular=regular, bold=bold,
                   latin_regular=pagebirdy_fonts.resolve(_LATIN[0]),
                   latin_bold=pagebirdy_fonts.resolve(_LATIN[1]))


@lru_cache(maxsize=16)
def _archive(fs: FontSet) -> tuple[fitz.Archive, str]:
    """The font files as an HTML archive, and the @font-face CSS naming them."""
    arch = fitz.Archive()
    css = []
    for family, weight, path in (("tgt", "normal", fs.regular), ("tgt", "bold", fs.bold),
                                 ("lat", "normal", fs.latin_regular), ("lat", "bold", fs.latin_bold)):
        if not path:
            continue
        name = f"{family}-{weight}{os.path.splitext(path)[1]}"
        with open(path, "rb") as f:
            arch.add(f.read(), name)
        css.append(f"@font-face {{font-family: {family}; font-weight: {weight}; src: url({name});}}")
    return arch, "\n".join(css)


@lru_cache(maxsize=16)
def _font(path: str) -> fitz.Font:
    return fitz.Font(fontfile=path)


def missing_glyphs(text: str, fs: FontSet) -> str:
    """Characters neither the target face nor the Latin face can draw."""
    faces = [_font(p) for p in (fs.regular, fs.latin_regular) if p]
    out = []
    for ch in text:
        if ch.isspace() or ch in (rtl.LRE, rtl.PDF) or ch in out:
            continue
        if not any(f.has_glyph(ord(ch)) for f in faces):
            out.append(ch)
    return "".join(out)


@dataclass
class Style:
    fonts: FontSet
    bold: bool
    align: str  # left | right | center
    direction: str  # ltr | rtl


def _runs(text: str, fonts: FontSet) -> list[tuple[str, str]]:
    """`text` split into (family, run) by which face can draw each character.

    MuPDF takes only the first family of a CSS font list and fills any glyph
    that face lacks from its own built-in serif, so a URL inside Arabic came
    out in Times. Choosing the face per character is what keeps it in the
    Latin face the rest of the image's Latin text is set in.
    """
    target = _font(fonts.regular) if fonts.regular else None
    faces = {"tgt": target, "lat": _font(fonts.latin_regular) if fonts.latin_regular else None}
    runs: list[tuple[str, str]] = []
    for ch in text:
        current = runs[-1][0] if runs else None
        if target is None:
            family = "lat"
        elif ch.isspace() or ch in (rtl.LRE, rtl.PDF):
            family = current or "tgt"
        elif not ch.isalpha() and current and faces[current] and faces[current].has_glyph(ord(ch)):
            # Punctuation and digits belong to the run they sit in: the dots
            # of a URL stay in the URL's face.
            family = current
        elif target.has_glyph(ord(ch)):
            family = "tgt"
        else:
            family = "lat"
        if runs and runs[-1][0] == family:
            runs[-1] = (family, runs[-1][1] + ch)
        else:
            runs.append((family, ch))
    return runs


def _css_align(style: Style) -> str:
    """`style.align` is physical (left means the left edge of the box). MuPDF
    reads `text-align` against the paragraph's direction under `dir="rtl"` —
    measured on 1.26: `right` set Arabic against the box's left edge — so a
    physical side is handed to it mirrored for RTL."""
    if style.direction == "rtl":
        return {"left": "right", "right": "left"}.get(style.align, style.align)
    return style.align


def _html(text: str, style: Style, px: float, line_height: float) -> tuple[str, str]:
    arch_css = _archive(style.fonts)[1]
    css = (f"{arch_css}\n* {{margin: 0; padding: 0;}}\n"
           f"div {{font-family: tgt; font-size: {px:.2f}px; line-height: {line_height};"
           f" font-weight: {'bold' if style.bold else 'normal'}; text-align: {_css_align(style)};}}\n"
           f".lat {{font-family: lat;}}")
    inner = "".join(html.escape(run) if family == "tgt" else
                    f'<span class="lat">{html.escape(run)}</span>'
                    for family, run in _runs(text, style.fonts))
    body = f'<div dir="{style.direction}">{inner}</div>'
    return body, css


@dataclass
class Layout:
    fits: bool
    spare: float  # unused height under the text, px
    scale: float  # < 1 only for a forced fit


def layout(text: str, w: float, h: float, style: Style, px: float,
           line_height: float, force: bool = False) -> Layout:
    """Set `text` into a w×h box without drawing it, and say whether it fits.

    Fits means: every line inside the box's height *and* no glyph past its
    sides — MuPDF lets an unbreakable word run out sideways rather than
    reporting it, so the glyph boxes are read back and checked. `force` lets
    MuPDF scale the text down until it fits, the last resort.
    """
    margin = max(w, h)
    doc = fitz.open()
    try:
        page = doc.new_page(width=w + 2 * margin, height=h + 2 * margin)
        rect = fitz.Rect(margin, margin, margin + w, margin + h)
        body, css = _html(text, style, px, line_height)
        spare, scale = page.insert_htmlbox(rect, body, css=css, archive=_archive(style.fonts)[0],
                                           scale_low=0 if force else 1)
        if spare < 0:
            return Layout(False, spare, scale)
        xs = [(c["bbox"][0], c["bbox"][2])
              for b in page.get_text("rawdict")["blocks"]
              for ln in b.get("lines", ()) for s in ln["spans"] for c in s["chars"]
              if c["c"].strip()]
        inside = all(x0 >= rect.x0 - _EDGE_SLACK and x1 <= rect.x1 + _EDGE_SLACK for x0, x1 in xs)
        return Layout(inside or force, spare, scale)
    finally:
        doc.close()


def coverage(text: str, w: int, h: int, style: Style, px: float, line_height: float,
             force: bool = False) -> np.ndarray:
    """The text's coverage mask (h×w, 0..1), vertically centred in the box."""
    probe = layout(text, w, h, style, px, line_height, force=force)
    dy = max(0.0, probe.spare) / 2
    doc = fitz.open()
    try:
        page = doc.new_page(width=w, height=h)
        body, css = _html(text, style, px, line_height)
        page.insert_htmlbox(fitz.Rect(0, dy, w, h), body, css=css,
                            archive=_archive(style.fonts)[0], scale_low=0 if force else 1)
        pix = page.get_pixmap(alpha=True, matrix=fitz.Identity)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        alpha = arr[..., -1].astype(np.float32) / 255.0
    finally:
        doc.close()
    out = np.zeros((h, w), dtype=np.float32)
    hh, ww = min(h, alpha.shape[0]), min(w, alpha.shape[1])
    out[:hh, :ww] = alpha[:hh, :ww]
    return out


def _em_fraction(text: str) -> float:
    """How much of the em the OCR box of this text spans: capitals and
    ascenders reach ~0.73em above the baseline, x-height only ~0.52em, and
    descenders add ~0.21em below it."""
    asc = any(c.isupper() or c.isdigit() or c in "bdfhklt'\"" for c in text)
    desc = any(c in "gjpqy,;()" for c in text)
    return (0.73 if asc else 0.52) + (0.21 if desc else 0.0)


def estimate_font_px(text: str, lines: list, fonts: FontSet) -> float:
    """The source's type size in pixels, from two independent readings.

    Height: one line's box over the share of the em its letters span. Width:
    the size at which the source, set in the Latin face on as many lines as it
    had, fills the width it occupied. Each is off by the gap between the
    source's face and ours; averaging them, with the width reading kept within
    a quarter of the height reading, holds up for both all-caps banners
    (height alone undershoots) and condensed faces (width alone undershoots).
    """
    heights = sorted(b[3] - b[1] for b in lines) or [12.0]
    line_h = heights[len(heights) // 2]
    by_height = line_h / _em_fraction(text)
    path = fonts.latin_regular
    if not path or not text.strip():
        return by_height
    unit = _font(path).text_length(text, fontsize=1.0)
    if unit <= 0:
        return by_height
    by_width = sum(b[2] - b[0] for b in lines) / unit
    by_width = min(max(by_width, by_height * 0.75), by_height * 1.25)
    return (by_height + by_width) / 2


def looks_bold(text: str, w: int, h: int, fonts: FontSet, px: float, observed_stroke: float) -> bool:
    """Whether the source was set in a bold weight.

    The source text is set again in the Latin face at the estimated size, once
    regular and once bold, and the source's stroke width is compared with
    both: whichever weight it is nearer to (by ratio) is the one it was set
    in. Stroke width, not ink area — area grows with the square of the size
    estimate, and measured on real Vision boxes an 8% size overestimate was
    enough to read a bold heading as regular by area.
    """
    from pagebirdy.image.background import stroke_width

    if not fonts.latin_regular or not fonts.latin_bold or observed_stroke <= 0:
        return False
    latin = FontSet(fonts.latin_regular, fonts.latin_bold, fonts.latin_regular, fonts.latin_bold)
    try:
        strokes = [stroke_width(coverage(text, w, h, Style(latin, weight, "left", "ltr"),
                                         px, 1.0, force=True) > 0.5)
                   for weight in (False, True)]
    except Exception:  # noqa: BLE001 — a heuristic, never a failure
        return False
    regular, bold = strokes
    if regular <= 0 or bold <= 0:
        return False
    # Nearest wins. Below ~16px the two weights are under a pixel apart and
    # the call is unreliable either way; measured, biasing towards regular
    # there only trades misread regular text for misread bold text.
    return bool(abs(np.log(observed_stroke / bold)) < abs(np.log(observed_stroke / regular)))


def composite(region_px: np.ndarray, background: np.ndarray, mask: np.ndarray,
              color: tuple[int, ...]) -> np.ndarray:
    """Draw `color` over the rebuilt background through the coverage mask."""
    a = mask[..., None]
    c = region_px.shape[2]
    ink = np.zeros((1, 1, c), dtype=np.float32)
    ink[..., :3] = np.array(color[:3], dtype=np.float32)
    if c == 4:
        ink[..., 3] = 255.0
    return background * (1 - a) + ink * a
