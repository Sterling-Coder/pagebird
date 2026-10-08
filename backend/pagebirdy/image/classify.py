"""Which OCR regions to translate and which to leave exactly as drawn.

An ordered table of rules; the first one that claims a region decides it. A new
content type is one more function in `RULES`, nothing else. Protected regions
keep their original pixels — nothing is masked or redrawn — so a URL, a price
or a serial number can never come back altered.

Low confidence is a protection, not a translation with a warning attached: a
misread source cannot be translated into anything trustworthy, so the region is
left as it was and surfaced for a person to inspect.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from pagebirdy import script
from pagebirdy.image.regions import TextRegion
from pagebirdy.protect.mathguard import load_never_translate

URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s]+|\b[\w-]+(?:\.[\w-]+)*\.(?:com|org|net|edu|gov|io|co|uk|de|fr|es|info|biz)(?:/[^\s]*)?\b",
    re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
# A token mixing letters and digits with no spaces — "SKU-4471B", "A1B2C3",
# "X-200". Ordinary words never mix the two; ordinals ("1st") are excluded.
_CODE_TOKEN = re.compile(r"^(?=[A-Za-z0-9#/_.-]*\d)(?=[A-Za-z0-9#/_.-]*[A-Za-z])[A-Za-z0-9#/_.-]{4,}$")
_ORDINAL = re.compile(r"^\d+(st|nd|rd|th)$", re.IGNORECASE)
# Prices and quantities that are nothing but a value: "$19.99", "50%", "€5", "x2".
_VALUE = re.compile(r"^[\s$€£¥₹+\-−–(]*\d[\d\s.,:/%×x*+\-−–=)]*[$€£¥₹%]?\s*$", re.IGNORECASE)
# Rotations OCR reports within this many degrees of horizontal still count as
# horizontal — a slightly skewed photo of a sign.
_MAX_SKEW = 8.0
# Below this many pixels a line cannot be redrawn legibly in any script.
_MIN_LINE_PX = 7.0


def min_confidence() -> float:
    return float(os.getenv("BABEL_IMAGE_MIN_CONFIDENCE", "0.80"))


@dataclass
class Context:
    min_confidence: float
    protected_terms: tuple[str, ...]
    median_line_px: float


@dataclass
class Decision:
    content_type: str
    action: str  # translate | protect
    reason: str = ""
    warnings: list[str] = field(default_factory=list)


Rule = Callable[[TextRegion, Context], Optional[Decision]]


def _low_confidence(r: TextRegion, ctx: Context) -> Optional[Decision]:
    if r.confidence < ctx.min_confidence:
        return Decision("low_confidence", "protect",
                        f"OCR confidence {r.confidence:.0%} is below {ctx.min_confidence:.0%}",
                        [f"Low OCR confidence ({r.confidence:.0%}); left untranslated for review"])
    return None


def _rotated(r: TextRegion, ctx: Context) -> Optional[Decision]:
    skew = abs(((r.angle + 180) % 360) - 180)
    if skew > _MAX_SKEW:
        return Decision("rotated", "protect", f"text runs at {r.angle:.0f}°",
                        ["Rotated text is not redrawn yet; left as in the source"])
    return None


def _too_small(r: TextRegion, ctx: Context) -> Optional[Decision]:
    if r.line_height < _MIN_LINE_PX:
        return Decision("too_small", "protect", f"line height {r.line_height:.0f}px",
                        ["Text too small to redraw legibly; left as in the source"])
    return None


def _email(r: TextRegion, ctx: Context) -> Optional[Decision]:
    m = EMAIL_RE.search(r.text)
    if m and m.group(0).strip() == r.text.strip():
        return Decision("email", "protect", "email address")
    return None


def _url(r: TextRegion, ctx: Context) -> Optional[Decision]:
    m = URL_RE.search(r.text)
    if m and m.group(0).strip(" .") == r.text.strip(" ."):
        return Decision("url", "protect", "URL")
    return None


def _number_or_math(r: TextRegion, ctx: Context) -> Optional[Decision]:
    text = r.text.strip()
    if script.is_math_expression(text) and script.contains_math_operator(text):
        return Decision("math", "protect", "mathematical expression")
    if _VALUE.match(text):
        return Decision("number", "protect", "number or value")
    if script.is_math_expression(text):
        # A lone variable or label letter: "x", "A", "(b)".
        return Decision("symbol", "protect", "single letter or symbol")
    return None


def _code(r: TextRegion, ctx: Context) -> Optional[Decision]:
    tokens = r.text.split()
    if tokens and all(_CODE_TOKEN.match(t) and not _ORDINAL.match(t) for t in tokens):
        return Decision("code", "protect", "code or serial number")
    return None


def _brand(r: TextRegion, ctx: Context) -> Optional[Decision]:
    if r.text.strip() in ctx.protected_terms:
        return Decision("brand", "protect", "protected name")
    return None


def _prose(r: TextRegion, ctx: Context) -> Decision:
    words = len(r.text.split())
    if ctx.median_line_px and r.line_height >= 1.5 * ctx.median_line_px:
        return Decision("heading", "translate")
    if words <= 3:
        return Decision("label", "translate")
    return Decision("text", "translate")


RULES: list[Rule] = [
    _low_confidence, _rotated, _too_small,
    _email, _url, _code, _number_or_math, _brand,
]


def protected_terms() -> tuple[str, ...]:
    """The shared never-translate list plus any image-only extras."""
    extra = tuple(t.strip() for t in os.getenv("BABEL_IMAGE_PROTECTED_TERMS", "").split(",")
                  if t.strip())
    return load_never_translate() + extra


def classify(regions: list[TextRegion], min_conf: float | None = None,
             terms: tuple[str, ...] | None = None) -> list[TextRegion]:
    heights = sorted(r.line_height for r in regions) or [0.0]
    ctx = Context(
        min_confidence=min_confidence() if min_conf is None else min_conf,
        protected_terms=protected_terms() if terms is None else terms,
        median_line_px=heights[len(heights) // 2],
    )
    for r in regions:
        decision = next((d for rule in RULES if (d := rule(r, ctx))), None) or _prose(r, ctx)
        r.content_type, r.action, r.reason = decision.content_type, decision.action, decision.reason
        r.warnings.extend(decision.warnings)
        if decision.action == "protect":
            r.status = "needs_human" if decision.content_type == "low_confidence" else "protected"
    return regions
