"""Core data types shared across pipeline stages.

A source document is decomposed into `Line`s (one visual line of text, made of
`Span`s). A `Line` becomes one translation unit (`Segment`) after math is
protected. The `Segment` carries everything reassembly needs to place the
translated text back in the same spot.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# A rectangle as (x0, y0, x1, y1) in PDF points, origin top-left.
BBox = tuple[float, float, float, float]

# C0/C1 control chars minus tab/newline/CR, which XML (and IDML) forbids outright.
_CONTROL_CHARS_RE = re.compile(
    "[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]"
)


def _strip_control_chars(text: str) -> str:
    """Drop XML-illegal control chars an OCR pass or LLM occasionally emits."""
    return _CONTROL_CHARS_RE.sub("", text)


@dataclass
class Span:
    """One run of text with uniform styling, straight from PyMuPDF."""

    text: str
    font: str
    size: float
    color: int  # sRGB packed int
    bbox: BBox
    flags: int = 0  # PyMuPDF span flags (bit 1<<4 = bold, 1<<1 = italic, etc.)
    # Set for a run that must be reproduced from the page image rather than
    # re-encoded as text — a stacked fraction, whose three pieces are not a
    # character sequence at all (see mathguard._merge_fractions).
    atomic: bool = False
    # The run's own baseline (PyMuPDF `origin.y`). Reassembly needs the real
    # baseline, not one estimated from the box: a bulleted line sets its "•" at
    # twice the type size, so the line box is half as tall again as the text in
    # it and any estimate derived from that box lands the translation several
    # points too low — into the block underneath. 0.0 means "not recorded"
    # (OCR-recovered runs have no origin), and the estimate is used instead.
    origin: float = 0.0

    @property
    def is_math_font(self) -> bool:
        # Source packets carry math glyphs in dedicated faces; never translate these.
        name = self.font.lower()
        return any(k in name for k in ("math", "pi lt", "pilt", "mathematicalpi"))

    @property
    def is_bold(self) -> bool:
        """Bold by PyMuPDF's flag OR by the face's own name.

        The flag is set from the embedded font descriptor and is often wrong:
        `MuseoSans-700` is a bold weight but reports False, so headings set in it
        came back regular. The face name carries the weight reliably, either as a
        word or as a numeric weight, which is the standard naming convention
        rather than anything specific to one document.
        """
        if self.flags & (1 << 4):
            return True
        name = self.font.lower()
        if any(k in name for k in ("bold", "black", "heavy")):
            return True
        weight = re.search(r"(?<!\d)([1-9])00(?!\d)", name)
        return bool(weight and int(weight.group(1)) >= 6)

    @property
    def is_italic(self) -> bool:
        if self.flags & (1 << 1):
            return True
        name = self.font.lower()
        return bool(re.search(r"(italic|oblique|it)$", name))


@dataclass
class Line:
    """A visual line: its bbox and the spans composing it, in reading order."""

    page: int
    bbox: BBox
    spans: list[Span]
    block: int = 0  # PyMuPDF block index, used to group lines into paragraphs
    direction: tuple[float, float] = (1.0, 0.0)  # PyMuPDF line["dir"]
    # --- OCR provenance (see ingest/ocr.py) ---
    from_ocr: bool = False  # recovered by OCR, not present as PDF text
    ocr_confidence: float = 1.0
    in_image: bool = False  # burned into a raster image; original must be masked
    latex: Optional[str] = None  # set when the equation layer recognises this line

    @property
    def rotation(self) -> int:
        """Reading direction in degrees counter-clockwise (0, 90, 180 or 270).

        Axis labels on a graph are set vertically. Ignoring that draws them
        across a tall, narrow box, which forces a break after every few letters.
        """
        dx, dy = self.direction
        if abs(dx) >= abs(dy):
            return 0 if dx >= 0 else 180
        return 90 if dy < 0 else 270

    @property
    def dominant(self) -> Span:
        """The span that best represents this line's styling (widest one)."""
        return max(self.spans, key=lambda s: s.bbox[2] - s.bbox[0])

    @property
    def baseline(self) -> float:
        """The line's own baseline, taken from the run that carries its text.

        Falls back to a position estimated from the box for lines that have no
        recorded origin — anything OCR produced, which reports a box only.
        """
        origin = self.dominant.origin
        if origin:
            return origin
        y0, y1 = self.bbox[1], self.bbox[3]
        return y0 + (y1 - y0) * 0.81

    @property
    def raw_text(self) -> str:
        return "".join(s.text for s in self.spans)

    @property
    def has_math_font(self) -> bool:
        return any(s.is_math_font for s in self.spans)

    @property
    def is_bold(self) -> bool:
        return self.dominant.is_bold

    @property
    def is_italic(self) -> bool:
        return self.dominant.is_italic


@dataclass
class Segment:
    """A translation unit: protected source, plus reassembly context.

    A segment may span several visual lines (a merged prose paragraph), so it
    carries both the union `bbox` and the per-line `bboxes` it was built from.
    """

    id: str
    page: int
    bbox: BBox  # union of bboxes
    font: str
    size: float
    color: int
    source: str  # protected text, math replaced by placeholders
    placeholders: dict[str, str] = field(default_factory=dict)  # token -> literal
    # Math placeholders keep the face they were set in and their width relative
    # to the type size, so reassembly can redraw the real glyph rather than the
    # meaningless character code the PDF exposes for it.
    math_fonts: dict[str, str] = field(default_factory=dict)  # token -> font name
    math_widths: dict[str, float] = field(default_factory=dict)  # token -> width/size
    math_boxes: dict[str, BBox] = field(default_factory=dict)  # token -> source bbox
    rotation: int = 0  # degrees counter-clockwise; 90 for a vertical axis label
    bboxes: list[BBox] = field(default_factory=list)  # original line boxes covered
    baselines: list[float] = field(default_factory=list)  # each line's own baseline
    has_math_font: bool = False  # any opaque math-font placeholder present
    bold: bool = False
    italic: bool = False
    # Color of an inline emphasised run (the "**bold**"-marked words) when it
    # differs from `color` — e.g. a purple highlighted word inside black body
    # text. None means the emphasis is same-color, just a different weight.
    accent_color: Optional[int] = None
    # Point-size of that same emphasised run relative to the body text's size
    # (e.g. 14pt "SAY" inside 12pt prose -> 1.1667). None means the emphasis
    # is the body's own size, just bolded/recolored. Applied as a multiplier
    # on the fitted size at reassembly, so it scales down with the rest of the
    # line if the block has to shrink to fit.
    accent_size_ratio: Optional[float] = None
    # A leading list-bullet glyph, stripped from the translated text (it needs
    # no translation) and redrawn explicitly as a dot at reassembly: relying on
    # it to survive untouched on the page is not safe, since redacting a
    # nearby segment can erase it as a side effect (see mathguard._is_bullet).
    bullet_color: Optional[int] = None
    bullet_bbox: Optional[BBox] = None
    target: Optional[str] = None  # protected ES text (placeholders intact)
    status: str = "pending"  # pending | translated | needs_human | tm_hit | empty
    engine: Optional[str] = None
    disagreement: bool = False  # primary vs secondary engine differed
    notes: list[str] = field(default_factory=list)
    # --- provenance, set when the segment came from OCR or the equation layer ---
    from_ocr: bool = False
    in_image: bool = False  # text burned into an image; mask the original on output
    latex: Optional[str] = None  # recognised equation, source of truth over `source`

    @property
    def source_line_count(self) -> int:
        """Lines the source occupied — the editorial contract for the target."""
        return len(self.bboxes) or 1

    @property
    def is_translatable(self) -> bool:
        # Nothing to translate if, after protection, only whitespace remains.
        return bool(self.source.strip())

    def restored_target(self) -> str:
        """Target text with math placeholders swapped back to their literals."""
        out = self.target if self.target is not None else self.source
        for token, literal in self.placeholders.items():
            out = out.replace(token, literal)
        # Clean up any hallucinated numeric placeholders that the LLM added
        # (e.g. converting the word "Five" to "⟦=5⟧").
        out = re.sub(r"⟦=([^⟧]*)⟧", r"\1", out)
        return _strip_control_chars(out)

    def restored_source(self) -> str:
        """Source text with placeholders swapped back (human-readable EN)."""
        out = self.source
        for token, literal in self.placeholders.items():
            out = out.replace(token, literal)
        out = re.sub(r"⟦=([^⟧]*)⟧", r"\1", out)
        return _strip_control_chars(out)
