"""The unit every image stage passes along: one text region the OCR found.

Coordinates are image pixels, origin top-left, as (x0, y0, x1, y1) — the same
tuple shape `models.BBox` uses for PDF points, so a region can be handed to the
shared `Segment` without conversion.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

from pagebirdy.models import BBox


@dataclass
class Word:
    text: str
    bbox: BBox
    confidence: float = 1.0


@dataclass
class TextRegion:
    id: str
    text: str
    bbox: BBox
    confidence: float
    language: Optional[str] = None
    words: list[Word] = field(default_factory=list)
    # One box per visual line, top to bottom — what font-size estimation and
    # wrapping are measured against.
    lines: list[BBox] = field(default_factory=list)
    block: int = 0
    paragraph: int = 0
    # Reading direction of the text in degrees, from the OCR's own vertex
    # order: 0 for horizontal text, ±90 for a vertical axis label.
    angle: float = 0.0

    # --- classification (classify.py) ---
    content_type: str = "text"
    action: str = "translate"  # translate | protect
    reason: str = ""

    # --- translation (translate.py) ---
    target: Optional[str] = None
    # pending | translated | protected | needs_human | failed
    status: str = "pending"
    engine: Optional[str] = None
    notes: list[str] = field(default_factory=list)

    # --- reconstruction (render.py): font size, colour, fit, background ---
    render: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def width(self) -> float:
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> float:
        return self.bbox[3] - self.bbox[1]

    @property
    def line_height(self) -> float:
        """Median height of one visual line — the closest thing OCR gives to a
        type size."""
        heights = sorted(b[3] - b[1] for b in self.lines) or [self.height]
        return heights[len(heights) // 2]

    def to_dict(self) -> dict:
        """JSON-safe: every number a plain float, whatever produced it (OCR
        coordinates can arrive as numpy scalars)."""
        def num(v, places=1):
            return round(float(v), places)

        d = asdict(self)
        d["bbox"] = {"x": num(self.bbox[0]), "y": num(self.bbox[1]),
                     "width": num(self.width), "height": num(self.height)}
        d["confidence"] = num(self.confidence, 4)
        d["angle"] = num(self.angle)
        d["words"] = [{"text": w.text, "confidence": num(w.confidence, 4),
                       "bbox": [num(v) for v in w.bbox]} for w in self.words]
        d["lines"] = [[num(v) for v in b] for b in self.lines]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TextRegion":
        """The inverse of `to_dict` (coordinates to one decimal, as stored)."""
        b = d["bbox"]
        fields = {k: v for k, v in d.items() if k not in ("bbox", "words", "lines")}
        return cls(**fields,
                   bbox=(b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"]),
                   words=[Word(w["text"], tuple(w["bbox"]), w["confidence"]) for w in d["words"]],
                   lines=[tuple(line) for line in d["lines"]])
