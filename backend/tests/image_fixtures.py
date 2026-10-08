"""Synthetic test images for the image-translation pipeline.

Every image is generated: real text drawn by MuPDF onto a generated
background, so the tests exercise real pixels and real glyph boxes without a
single customer or copyrighted image in the repository. `fake_ocr` reads the
regions back from the drawing itself — the boxes are exact — so no test ever
calls Vision.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import fitz
import numpy as np
from PIL import Image

from pagebirdy import fonts
from pagebirdy.image.ocr import group_lines
from pagebirdy.image.regions import TextRegion, Word
from pagebirdy.translate.engine import Engine

_FONT = fonts.resolve(["LiberationSans-Regular.ttf"])
_BOLD = fonts.resolve(["LiberationSans-Bold.ttf"])


@dataclass
class TextItem:
    lines: list[str]
    x: float
    y: float  # baseline of the first line
    size: float = 24
    color: tuple = (0, 0, 0)
    bold: bool = False
    confidence: float = 0.98
    language: str = "en"


@dataclass
class Scene:
    width: int = 480
    height: int = 260
    background: str = "solid"  # solid | gradient | photo
    color: tuple = (250, 246, 238)
    items: list[TextItem] = field(default_factory=list)
    graphic: bool = False  # a filled shape away from the text


def _background(scene: Scene) -> np.ndarray:
    h, w = scene.height, scene.width
    arr = np.empty((h, w, 3), dtype=np.float32)
    arr[:] = scene.color
    if scene.background == "gradient":
        ramp = np.linspace(0, 1, w, dtype=np.float32)[None, :, None]
        arr = arr * (1 - ramp) + np.array([40, 90, 180], dtype=np.float32) * ramp
    elif scene.background == "photo":
        rng = np.random.default_rng(7)
        arr = np.clip(arr + rng.normal(0, 40, arr.shape), 0, 255)
    return arr.astype(np.uint8)


def render_scene(scene: Scene) -> tuple[Image.Image, list[TextRegion]]:
    """The image, and the regions an ideal OCR would report for it."""
    doc = fitz.open()
    page = doc.new_page(width=scene.width, height=scene.height)
    regions: list[TextRegion] = []
    for item in scene.items:
        face = _BOLD if item.bold else _FONT
        font = fitz.Font(fontfile=face)
        words: list[Word] = []
        for i, line in enumerate(item.lines):
            base = item.y + i * item.size * 1.2
            page.insert_text((item.x, base), line, fontsize=item.size, fontfile=face,
                             fontname="B" if item.bold else "R",
                             color=tuple(c / 255 for c in item.color))
            x = item.x
            for token in line.split(" "):
                tw = font.text_length(token, fontsize=item.size)
                if token:
                    # Generous search band; tightened to the real ink below.
                    words.append(Word(text=token, bbox=(x, base - item.size * 0.9, x + tw,
                                                        base + item.size * 0.3),
                                      confidence=item.confidence))
                x += tw + font.text_length(" ", fontsize=item.size)
        regions.append(TextRegion(id=f"r{len(regions) + 1}", text=" ".join(item.lines),
                                  bbox=(0, 0, 0, 0), confidence=item.confidence,
                                  language=item.language, words=words))
    if scene.graphic:
        shape = page.new_shape()
        shape.draw_circle((scene.width - 60, scene.height - 60), 40)
        shape.finish(fill=(0.85, 0.2, 0.2), color=None)
        shape.commit()
    pix = page.get_pixmap(alpha=True, matrix=fitz.Identity)
    ink = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 4)
    doc.close()
    # Like a real OCR engine, report boxes that hug the ink: a word with no
    # descender gets no descender space.
    alpha = ink[..., 3] > 80
    for region in regions:
        for word in region.words:
            x0, y0, x1, y1 = (int(round(v)) for v in word.bbox)
            ys, xs = np.nonzero(alpha[max(0, y0):y1, max(0, x0):x1])
            if len(xs):
                word.bbox = (float(max(0, x0) + xs.min()), float(max(0, y0) + ys.min()),
                             float(max(0, x0) + xs.max() + 1), float(max(0, y0) + ys.max() + 1))
        region.lines = group_lines(region.words)
        region.bbox = (min(b[0] for b in region.lines), min(b[1] for b in region.lines),
                       max(b[2] for b in region.lines), max(b[3] for b in region.lines))
    bg = _background(scene).astype(np.float32)
    a = ink[..., 3:4].astype(np.float32) / 255.0
    # pixmap colour is premultiplied by alpha
    rgb = ink[..., :3].astype(np.float32)
    out = bg * (1 - a) + rgb
    return Image.fromarray(np.clip(np.rint(out), 0, 255).astype(np.uint8)), regions


def fake_ocr(regions: list[TextRegion]):
    """An OCR callable that reports `regions` (fresh copies) for any image."""
    import copy

    def read(_img):
        return copy.deepcopy(regions)
    return read


class DictEngine(Engine):
    """A deterministic engine: a lookup table over the *protected* source."""

    name = "dict"

    def __init__(self, table: dict[str, str]):
        self.table = table
        self.seen: list[str] = []

    def translate(self, texts: list[str]) -> list[str]:
        self.seen.extend(texts)
        return [self.table.get(t, t) for t in texts]


def make_psd(path, scene: Scene) -> list[TextRegion]:
    """A Photoshop document whose composite is `scene`; returns its regions."""
    from psd_tools import PSDImage

    img, regions = render_scene(scene)
    PSDImage.frompil(img).save(str(path))
    return regions


def make_ai(path, items, size=(400, 200), private_data=True, creator="Adobe Illustrator 28.0"):
    """A PDF-compatible Illustrator file: live text, a filled shape, and (by
    default) the `/PieceInfo` -> `AIPrivateData` stream real .ai files carry
    beside their PDF content. `items` is [(text, x, baseline_y, fontsize)]."""
    doc = fitz.open()
    page = doc.new_page(width=size[0], height=size[1])
    for text, x, y, fs in items:
        page.insert_text((x, y), text, fontsize=fs, fontfile=_FONT, fontname="F0")
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(size[0] - 70, size[1] - 70, size[0] - 20, size[1] - 20))
    shape.finish(fill=(0.2, 0.5, 0.9), color=None)
    shape.commit()
    if private_data:
        xref = doc.get_new_xref()
        doc.update_object(xref, "<<>>")
        doc.update_stream(xref, b"%AI24_ZStandard_Data native editing data")
        doc.xref_set_key(page.xref, "PieceInfo",
                         f"<</Illustrator <</Private <</AIPrivateData1 {xref} 0 R>>>>>>")
    doc.set_metadata({"creator": creator, "producer": "Adobe PDF library"})
    doc.save(str(path))
    doc.close()
