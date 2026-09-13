"""Best-effort IDML -> PDF preview (NO InDesign).

A faithful IDML render needs InDesign; this is a *draft* renderer for a quick
visual/printable proof of the translation. It lays out each spread's text frames
at their real geometry and flows the (already translated) story text into them
with an auto-shrunk font, and places linked raster images where it can. It does
NOT reproduce InDesign's composition exactly — line breaking, leading, tracking,
vector `.ai` art, text wrap, and overset handling all differ. Treat the output
as a legibility check, not a deliverable; the `.idml`/INDD remains the real one.

Geometry model (see a Spread_*.xml):
  * Page `GeometricBounds="y1 x1 y2 x2"` -> width=x2-x1, height=y2-y1.
  * Every page item carries `ItemTransform="a b c d tx ty"`; a point (x,y) maps
    to (a*x + c*y + tx, b*x + d*y + ty). Text-frame corners come from its
    `<PathPointType Anchor="x y">` nodes; the page's own ItemTransform places the
    page inside the spread. We invert the (near-identity) page transform to get
    frame coordinates local to the page, which is what PyMuPDF draws in.
"""

from __future__ import annotations

import logging
import os
import zipfile

import fitz
from lxml import etree

from babel import fonts as babel_fonts
from babel import languages

logger = logging.getLogger("babel.idml.render")

_RASTER_EXTS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".gif", ".bmp")


def _ln(el) -> str:
    return etree.QName(el).localname if isinstance(el.tag, str) else ""


def _nums(s: str) -> list[float]:
    out = []
    for tok in (s or "").split():
        try:
            out.append(float(tok))
        except ValueError:
            pass
    return out


def _apply(m: list[float], x: float, y: float) -> tuple[float, float]:
    a, b, c, d, tx, ty = m
    return a * x + c * y + tx, b * x + d * y + ty


def _story_texts(z: zipfile.ZipFile) -> dict[str, str]:
    """Map Story Self -> its full text (paragraphs joined by newlines)."""
    texts: dict[str, str] = {}
    for name in z.namelist():
        if not (name.startswith("Stories/") and name.endswith(".xml")):
            continue
        tree = etree.fromstring(z.read(name))
        for story in tree.iter():
            if _ln(story) != "Story":
                continue
            paras: list[str] = []
            for para in story.iter():
                if _ln(para) != "ParagraphStyleRange":
                    continue
                buf = "".join(
                    c.text or "" for c in para.iter() if _ln(c) == "Content"
                )
                if buf.strip():
                    paras.append(buf)
            text = "\n".join(paras)
            text = text.replace(" ", "\n").replace(" ", "\n")
            if text.strip():
                texts[story.get("Self", "")] = text
    return texts


def _frame_bbox(tf) -> tuple[float, float, float, float] | None:
    """Absolute (spread-space) bbox of a text frame from its path + transform."""
    m = _nums(tf.get("ItemTransform", "1 0 0 1 0 0"))
    if len(m) != 6:
        return None
    xs: list[float] = []
    ys: list[float] = []
    for pp in tf.iter():
        if _ln(pp) != "PathPointType":
            continue
        a = _nums(pp.get("Anchor", ""))
        if len(a) == 2:
            X, Y = _apply(m, a[0], a[1])
            xs.append(X)
            ys.append(Y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _linked_image(rect_el) -> str | None:
    for img in rect_el.iter():
        if _ln(img) not in ("Image", "EPS", "PDF", "WMF"):
            continue
        for link in img.iter():
            if _ln(link) == "Link":
                uri = link.get("LinkResourceURI", "")
                from babel.idml.graphics import _resolve_uri
                p = _resolve_uri(uri)
                if p and p.lower().endswith(_RASTER_EXTS) and os.path.isfile(p):
                    return p
    return None


def render_idml_to_pdf(idml_path: str, out_pdf: str, target_lang: str = "") -> str:
    """Render a draft PDF of a (translated) IDML. Returns out_pdf path."""
    lang = languages.get(target_lang or None)
    rtl = lang.direction == "rtl"
    font_path = babel_fonts.resolve(lang.fonts.get("regular", ())) or None

    with zipfile.ZipFile(idml_path) as z:
        stories = _story_texts(z)
        spreads = sorted(n for n in z.namelist()
                         if n.startswith("Spreads/") and n.endswith(".xml"))
        doc = fitz.open()
        for sname in spreads:
            tree = etree.fromstring(z.read(sname))
            # Pages of this spread, with their spread-space placement.
            pages = []
            for pg in tree.iter():
                if _ln(pg) != "Page":
                    continue
                gb = _nums(pg.get("GeometricBounds", "0 0 0 0"))
                it = _nums(pg.get("ItemTransform", "1 0 0 1 0 0"))
                if len(gb) != 4 or len(it) != 6:
                    continue
                y1, x1, y2, x2 = gb
                w, h = x2 - x1, y2 - y1
                tx, ty = it[4], it[5]
                pages.append({
                    "w": w, "h": h, "tx": tx, "ty": ty,
                    "sx1": tx + x1, "sx2": tx + x2,  # spread-space x range
                })
            pages.sort(key=lambda p: p["sx1"])
            # Store page NUMBERS, not Page objects: held PyMuPDF Page handles go
            # stale after later document mutations, so we re-fetch doc[n] at draw.
            for p in pages:
                p["num"] = doc.new_page(width=p["w"], height=p["h"]).number

            for tf in tree.iter():
                if _ln(tf) != "TextFrame":
                    continue
                text = stories.get(tf.get("ParentStory", ""), "")
                if not text.strip():
                    continue
                bb = _frame_bbox(tf)
                if bb is None:
                    continue
                cx = (bb[0] + bb[2]) / 2
                idx = next((i for i, p in enumerate(pages)
                            if p["sx1"] - 1 <= cx <= p["sx2"] + 1), None)
                if idx is None:
                    continue
                p = pages[idx]
                rect = fitz.Rect(bb[0] - p["tx"], bb[1] - p["ty"],
                                 bb[2] - p["tx"], bb[3] - p["ty"])
                _draw_textbox(doc[p["num"]], rect, text, font_path, rtl)

            # Best-effort raster images (skip .ai/.eps vector art).
            for rect_el in tree.iter():
                if _ln(rect_el) not in ("Rectangle", "Polygon", "GraphicLine"):
                    continue
                img = _linked_image(rect_el)
                if not img:
                    continue
                bb = _frame_bbox(rect_el)
                if bb is None:
                    continue
                cx = (bb[0] + bb[2]) / 2
                idx = next((i for i, p in enumerate(pages)
                            if p["sx1"] - 1 <= cx <= p["sx2"] + 1), None)
                if idx is None:
                    continue
                p = pages[idx]
                rect = fitz.Rect(bb[0] - p["tx"], bb[1] - p["ty"],
                                 bb[2] - p["tx"], bb[3] - p["ty"])
                try:
                    doc[p["num"]].insert_image(rect, filename=img, keep_proportion=True)
                except Exception:
                    pass  # draft: a bad image must not kill the render

        os.makedirs(os.path.dirname(os.path.abspath(out_pdf)), exist_ok=True)
        doc.save(out_pdf, deflate=True)
        doc.close()
    logger.info("render_idml_to_pdf: wrote draft %s", out_pdf)
    return out_pdf


def _draw_textbox(page, rect, text, font_path, rtl) -> None:
    """Flow text into rect at an auto-shrunk size, via MuPDF's HTML/CSS text
    layout (`insert_htmlbox`) rather than `insert_textbox`.

    `insert_textbox` only *positions* text — `align=TEXT_ALIGN_RIGHT` anchors
    it to the right edge but performs no bidi reordering and no Arabic/Hebrew
    glyph shaping. For RTL scripts that draws the logical-order codepoints,
    unjoined, left where they'd sit for LTR text: a garbled, unshaped result,
    not a real preview. `insert_htmlbox` goes through MuPDF's proper text
    layout engine, which does both — `direction: rtl` in the CSS is enough.
    """
    import html as _html

    paragraphs = [p for p in text.split("\n") if p.strip()]
    body = "".join(f"<p>{_html.escape(p)}</p>" for p in paragraphs) or "<p></p>"

    css_rules = ["body { margin: 0; padding: 0; font-size: 11pt; }"]
    archive = None
    if font_path:
        archive = fitz.Archive()
        archive.add(font_path, "target-font")
        css_rules.append("@font-face { font-family: target; src: url(target-font); }")
        css_rules.append("body { font-family: target; }")
    if rtl:
        css_rules.append("body { direction: rtl; text-align: right; }")
    css = " ".join(css_rules)

    # scale_low=0: shrink as far as needed to fit rather than overflow, the
    # same "auto-shrunk font" intent the old insert_textbox loop had.
    page.insert_htmlbox(rect, body, css=css, archive=archive, scale_low=0)
