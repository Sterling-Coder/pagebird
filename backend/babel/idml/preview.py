"""Render an IDML to a PDF you can actually look at — without InDesign.

Reviewing an IDML is otherwise painful: InDesign is licensed, Scribus's importer
is partial, and VS Code only shows the raw XML. This module reads the package
the same way a layout engine would (spreads → pages, TextFrames → boxes,
Stories → text, linked Images → pictures) and draws it with PyMuPDF.

It is a **proof, not a proof of print**: it shows position, size, content and
overflow, which is what you need to answer "did the conversion work and does the
Spanish still fit?". Final typographic fidelity still comes from InDesign.

    python -m babel.cli preview-idml out/doc.idml --out out/doc.preview.pdf

Geometry mirrors `idml/build.py`: a single-page spread is centred on x=0, so
page-space = spread-space + (W/2, H/2).
"""

from __future__ import annotations

import os
import zipfile
from urllib.parse import unquote, urlparse

import fitz
from lxml import etree


def _localname(el) -> str:
    if not isinstance(el.tag, str):
        return ""
    return etree.QName(el).localname


def _iter(el, name: str):
    for node in el.iter():
        if _localname(node) == name:
            yield node


def _floats(value: str | None) -> list[float]:
    if not value:
        return []
    out = []
    for part in value.replace(",", " ").split():
        try:
            out.append(float(part))
        except ValueError:
            pass
    return out


def _local_path(uri: str, base_dir: str) -> str | None:
    """Resolve a Link URI to something on disk, tolerating relative links."""
    if not uri:
        return None
    if uri.startswith("file:"):
        parsed = urlparse(uri)
        path = unquote(parsed.path)
        if os.name == "nt" and path.startswith("/") and len(path) > 2 and path[2] == ":":
            path = path[1:]
    else:
        path = uri
    if os.path.isabs(path) and os.path.exists(path):
        return path
    candidate = os.path.join(base_dir, os.path.basename(path))
    return candidate if os.path.exists(candidate) else None


def _story_texts(z: zipfile.ZipFile) -> dict[str, list[str]]:
    """story Self -> list of paragraphs."""
    out: dict[str, list[str]] = {}
    for name in z.namelist():
        if not (name.startswith("Stories/") and name.endswith(".xml")):
            continue
        root = etree.fromstring(z.read(name))
        for story in _iter(root, "Story"):
            # the idPkg:Story package root has the same localname as the Story
            # content node; only the content node carries a Self id
            if not story.get("Self"):
                continue
            paras: list[str] = []
            for psr in _iter(story, "ParagraphStyleRange"):
                text = "".join(c.text or "" for c in _iter(psr, "Content"))
                paras.append(text)
            if not paras:
                paras = ["".join(c.text or "" for c in _iter(story, "Content"))]
            out[story.get("Self")] = paras
    return out


def _item_box(item, page_w: float, page_h: float) -> fitz.Rect | None:
    """Page-space rect of a spread item, from its transform + path points."""
    tr = _floats(item.get("ItemTransform"))
    if len(tr) < 6:
        return None
    tx, ty = tr[4], tr[5]
    xs: list[float] = []
    ys: list[float] = []
    for pt in _iter(item, "PathPointType"):
        anchor = _floats(pt.get("Anchor"))
        if len(anchor) == 2:
            xs.append(anchor[0])
            ys.append(anchor[1])
    if not xs:
        return None
    return fitz.Rect(
        tx + min(xs) + page_w / 2.0,
        ty + min(ys) + page_h / 2.0,
        tx + max(xs) + page_w / 2.0,
        ty + max(ys) + page_h / 2.0,
    )


def _grow_downwards(box: "fitz.Rect", occupied: list, page_rect: "fitz.Rect",
                    limit: float = 3.0) -> "fitz.Rect":
    """Extend a frame down until it would touch the next one below it.

    InDesign auto-height does this for real; the preview approximates it so the
    overflow numbers it reports mean the same thing.
    """
    ceiling = page_rect.y1
    for other in occupied:
        if other.y0 <= box.y0 or other is box:
            continue
        if other.x1 <= box.x0 or other.x0 >= box.x1:
            continue  # no horizontal overlap, cannot collide
        ceiling = min(ceiling, other.y0)
    room = max(box.height, min(ceiling - box.y0 - 1.0, box.height * limit))
    return fitz.Rect(box.x0, box.y0, box.x1, box.y0 + room)


def render_idml(idml_path: str, out_pdf: str, dpi: int = 0,
                draw_frames: bool = False) -> dict:
    """Draw `idml_path` into `out_pdf`. Returns a small stats dict.

    `draw_frames=True` outlines every text frame — useful when debugging
    placement. `dpi>0` also writes one PNG per page next to the PDF.
    """
    base_dir = os.path.dirname(os.path.abspath(idml_path))
    z = zipfile.ZipFile(idml_path)
    try:
        stories = _story_texts(z)
        spread_names = sorted(n for n in z.namelist() if n.startswith("Spreads/"))

        out = fitz.open()
        stats = {"pages": 0, "frames": 0, "images": 0, "overflow": 0, "missing_images": 0}

        for name in spread_names:
            root = etree.fromstring(z.read(name))
            for page_el in _iter(root, "Page"):
                gb = _floats(page_el.get("GeometricBounds"))
                if len(gb) < 4:
                    continue
                top, left, bottom, right = gb
                page_w, page_h = right - left, bottom - top
                page = out.new_page(width=page_w, height=page_h)
                stats["pages"] += 1

                spread = page_el.getparent()

                # images first (backgrounds), then text on top
                for rect_el in _iter(spread, "Rectangle"):
                    box = _item_box(rect_el, page_w, page_h)
                    if box is None:
                        continue
                    link = next(_iter(rect_el, "Link"), None)
                    if link is None:
                        continue
                    path = _local_path(link.get("LinkResourceURI", ""), base_dir)
                    if not path:
                        stats["missing_images"] += 1
                        page.draw_rect(box, color=(0.8, 0.2, 0.2), width=0.5)
                        continue
                    try:
                        page.insert_image(box, filename=path)
                        stats["images"] += 1
                    except Exception:
                        stats["missing_images"] += 1

                # every frame already placed on this page, so growth never
                # pushes text over a neighbour
                occupied: list[fitz.Rect] = []
                frames = []
                for tf in _iter(spread, "TextFrame"):
                    box = _item_box(tf, page_w, page_h)
                    if box is not None:
                        frames.append((tf, box))
                # top-to-bottom, so each frame only grows into space still free
                frames.sort(key=lambda fb: (fb[1].y0, fb[1].x0))
                occupied.extend(b for _, b in frames)

                for tf, box in frames:
                    paras = stories.get(tf.get("ParentStory"), [])
                    text = "\n".join(paras).strip()
                    stats["frames"] += 1
                    if draw_frames:
                        page.draw_rect(box, color=(0.6, 0.6, 0.9), width=0.3)
                    if not text:
                        continue
                    size, fill = _story_style(z, tf.get("ParentStory"))
                    size = size or 10.0

                    # An axis label is set sideways: its box is tall and narrow.
                    # Wrapped as prose it spells the word downwards, one letter
                    # per line, so draw it rotated the way the source has it.
                    # Only a single run of text can be sideways. A tall, narrow
                    # frame holding several paragraphs is a column of axis
                    # labels stacked vertically — rotating that lays the whole
                    # scale on its side across the chart.
                    rotate = 0
                    natural = fitz.get_text_length(text.strip(), fontname="helv",
                                                   fontsize=size or 10.0)
                    if (len(paras) == 1 and box.height > box.width * 1.5
                            and len(text.strip()) > 2
                            and natural > box.width * 1.8):
                        # insert_textbox rotates *inside* the rect, so the box
                        # itself stays exactly where the source put it.
                        rotate = 90

                    # A lone token ("1,400", "350") must never be broken across
                    # lines — widen the box instead of wrapping mid-number.
                    if rotate == 0 and " " not in text.strip():
                        needed = fitz.get_text_length(text.strip(), fontname="helv",
                                                      fontsize=size) + 2.0
                        if needed > box.width:
                            box = fitz.Rect(box.x0, box.y0, box.x0 + needed, box.y1)

                    # Mirror InDesign's auto-height: grow the box downward into
                    # free space before touching the type size, so longer
                    # Spanish reflows instead of being shrunk to illegibility.
                    grown = box if rotate else _grow_downwards(box, occupied, page.rect)
                    left_over = page.insert_textbox(
                        grown, text, fontsize=size, fontname="helv",
                        color=fill, align=fitz.TEXT_ALIGN_LEFT, rotate=rotate,
                    )
                    if left_over < 0:
                        stats["overflow"] += 1
                        shrunk = size
                        while left_over < 0 and shrunk > 4.0:
                            shrunk -= 0.5
                            left_over = page.insert_textbox(
                                grown, text, fontsize=shrunk, fontname="helv",
                                color=fill, align=fitz.TEXT_ALIGN_LEFT,
                                rotate=rotate,
                            )
                    occupied.append(grown)

        os.makedirs(os.path.dirname(os.path.abspath(out_pdf)), exist_ok=True)
        # Page backgrounds are full-page bitmaps; without deflate PyMuPDF stores
        # them as raw RGB and a 31-page preview balloons to hundreds of MB.
        out.save(out_pdf, deflate=True, deflate_images=True, garbage=4)

        if dpi:
            stem = os.path.splitext(out_pdf)[0]
            for i, page in enumerate(out, start=1):
                page.get_pixmap(dpi=dpi).save(f"{stem}_p{i:03d}.png")

        out.close()
        stats["output"] = out_pdf
        return stats
    finally:
        z.close()


_STYLE_CACHE: dict[str, tuple[float | None, tuple[float, float, float]]] = {}

_BLACK = (0.0, 0.0, 0.0)
_WHITE = (1.0, 1.0, 1.0)


def _story_style(z: zipfile.ZipFile,
                 story_id: str | None) -> tuple[float | None, tuple[float, float, float]]:
    """(point size, fill colour) of a story's first styled run.

    Colour matters: knockout problem numbers are set in Color/Paper and must
    render white, not black, or they sit as dark blobs on the dark disc behind
    them.
    """
    if not story_id:
        return None, _BLACK
    if story_id in _STYLE_CACHE:
        return _STYLE_CACHE[story_id]

    result: tuple[float | None, tuple[float, float, float]] = (None, _BLACK)
    for name in z.namelist():
        if not (name.startswith("Stories/") and name.endswith(".xml")):
            continue
        root = etree.fromstring(z.read(name))
        for story in _iter(root, "Story"):
            if not story.get("Self") or story.get("Self") != story_id:
                continue
            for csr in _iter(story, "CharacterStyleRange"):
                size = None
                try:
                    size = float(csr.get("PointSize")) if csr.get("PointSize") else None
                except ValueError:
                    size = None
                fill = _WHITE if csr.get("FillColor") == "Color/Paper" else _BLACK
                result = (size, fill)
                _STYLE_CACHE[story_id] = result
                return result
    _STYLE_CACHE[story_id] = result
    return result
