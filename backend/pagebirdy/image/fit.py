"""Fit a translation into the box its source occupied.

The same order of preference `idml/textfit.py` follows, without its IDML
machinery: reducing type is the last resort, not the first.

1. the source's own size, on as many lines as the box has room for;
2. the same size with tighter line spacing, if wrapping needs it;
3. the size reduced in small steps, down to a floor;
4. only then, MuPDF's own scale-to-fit — the text still never leaves the box,
   and the region is flagged, because type that small may not read.

The box is never enlarged and nothing around it moves: one long translation is
never a reason to change the rest of the image.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from pagebirdy.image.render import Style, layout

_LINE_HEIGHTS = (1.2, 1.1, 1.0)


def min_font_px() -> float:
    return float(os.getenv("BABEL_IMAGE_MIN_FONT_PX", "8"))


@dataclass
class Fit:
    font_px: float
    line_height: float
    natural_px: float
    shrunk: bool  # set smaller than the source
    forced: bool  # nothing fitted; MuPDF scaled it into the box

    def to_dict(self) -> dict:
        return {"font_px": round(self.font_px, 2), "line_height": self.line_height,
                "natural_px": round(self.natural_px, 2), "shrunk": self.shrunk,
                "forced": self.forced}


def fit_text(text: str, w: float, h: float, style: Style, natural_px: float) -> Fit:
    # Never below the configured floor, and never below half the source size,
    # unless the box itself is smaller than the floor.
    floor = min(max(min_font_px(), natural_px * 0.5), natural_px)
    step = max(0.5, natural_px * 0.04)
    px = natural_px
    while px >= floor - 1e-6:
        for lh in _LINE_HEIGHTS:
            if layout(text, w, h, style, px, lh).fits:
                return Fit(px, lh, natural_px, shrunk=px < natural_px - 1e-6, forced=False)
        px -= step
    return Fit(floor, _LINE_HEIGHTS[-1], natural_px, shrunk=True, forced=True)
