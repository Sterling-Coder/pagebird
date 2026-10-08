"""The contract every office/plain-text adapter fulfils.

Adapters extract `Segment`s and write text back. They never protect,
translate or score: that is `office.pipeline`, shared by every format.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

from pagebirdy.languages import Language
from pagebirdy.models import Segment

# A segment's target reaches the file only in these states; anything else
# (needs_human, pending, protected) keeps the source text, as on the IDML path.
WRITABLE = frozenset({"translated", "tm_hit", "approved", "edited"})


@dataclass
class Issue:
    level: str      # "warning" | "error"
    code: str       # "overflow", "tags", "structure", "formula", ...
    where: str      # human locator: "slide 12", "Sheet1!B4", "line 7"
    detail: str

    def as_dict(self) -> dict:
        return asdict(self)


class Adapter(Protocol):
    def extract(self, src: str) -> list[Segment]: ...
    def rebuild(self, src: str, segments: list[Segment], out: str, lang: Language) -> list[Issue]: ...
    def validate(self, src: str, out: str) -> list[Issue]: ...
    def units(self, src: str) -> dict: ...


def blank_segment(seg_id: str, text: str, page: int = 0) -> Segment:
    """A segment with no geometry: office formats are addressed by `id`."""
    return Segment(id=seg_id, page=page, bbox=(0.0, 0.0, 0.0, 0.0), font="", size=0.0,
                   color=0, source=text)


def writable(seg: Segment | None) -> bool:
    return seg is not None and seg.status in WRITABLE and seg.target is not None


def reject_tags(seg: Segment, where: str) -> Issue:
    """The engine's tags came back in an order the gate's multiset cannot see
    (closed before opened, nested). The paragraph keeps its source text and a
    person decides."""
    seg.status = "needs_human"
    seg.notes.append("formatting tags came back malformed; source text kept")
    return Issue("warning", "tags", where, "formatting tags came back malformed; source kept")
