"""Everything about a right-to-left target, and nothing about a left-to-right one.

Shaping is not done here: MuPDF shapes Arabic and Hebrew itself when the text
is set (the same engine the PDF path draws RTL text with), so letters join and
nothing is ever reversed by hand. What this layer owns is the two decisions the
shaper cannot make:

* **Reading order of protected runs.** Under the Unicode bidi algorithm an
  equation inside Arabic is split at its neutral characters — `3 + 4 = 7`
  comes back drawn as `7 = 4 + 3`. Each protected literal (a number, an
  expression, a URL) is wrapped in a left-to-right embedding (LRE … PDF) so it
  keeps its own order as one unit. Measured on MuPDF 1.26: the embedding holds
  `3 + 4 = 7`; the newer isolates (LRI … PDI) detach the run from its sentence
  and an HTML `dir` attribute is ignored.
* **Alignment.** Text the source set against its start edge is set against
  the target's start edge, which for RTL is the right. Centred stays centred.

An LTR target goes through `restore_target` and `alignment` unchanged.
"""

from __future__ import annotations

import dataclasses

from pagebirdy.models import Segment

LRE = "‪"
PDF = "‬"


def is_rtl(lang) -> bool:
    return getattr(lang, "direction", "ltr") == "rtl"


def direction(lang) -> str:
    return "rtl" if is_rtl(lang) else "ltr"


def restore_target(seg: Segment, lang) -> str:
    """The text to draw: the segment's target with its placeholders restored,
    each protected literal held left-to-right when the target is RTL."""
    if not is_rtl(lang):
        return seg.restored_target()
    held = {tok: f"{LRE}{lit}{PDF}" for tok, lit in seg.placeholders.items()}
    return dataclasses.replace(seg, placeholders=held).restored_target()


def alignment(source_align: str, lang) -> str:
    if not is_rtl(lang) or source_align == "center":
        return source_align
    return {"left": "right", "right": "left"}.get(source_align, source_align)
