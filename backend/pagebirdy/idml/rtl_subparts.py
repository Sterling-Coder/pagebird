"""One shared starting edge for a list of lettered or numbered sub-parts --
``a.``, ``b.``, ``c.`` or ``1.``, ``2.``, ``3.`` -- after
:func:`rtl.set_text_direction` has already run.

**The defect this corrects.** In the sample books a lettered sub-part is very
often its own small text frame (one paragraph, sometimes one frame per
letter), not a shared list inside one box. Every such frame in a group shares
one left edge in the English source -- that is what makes the list read as
aligned -- but each frame is only as *wide* as its own line needed, so their
right edges differ, often by tens of points. Mirrored to right-aligned Arabic
text (:func:`rtl.set_text_direction` swaps ``LeftIndent``/``RightIndent`` and
flips ``Justification``, but never touches a frame's own geometry -- see that
module's docstring for why), each label now hugs *its own* frame's right
edge, and a group that read as one flush list in English comes out staggered
in Arabic by however much its members' widths happened to differ.

**The fix stays inside the "text only" contract.** `rtl.py` never
repositions or resizes a *text-bearing* object -- every rule in `idml.
rtl_rules` that matches `content_kind == "text"` keeps its position, which is
exactly what every object this module touches is. This module honours that
same boundary independently: it never touches a
frame's ``ItemTransform`` or ``PathGeometry``. The only thing it writes is
each paragraph's own ``RightIndent`` -- already a text property `set_text_
direction` swaps for exactly this reason (a hanging indent has to move with
the text) -- nudged by however much its own frame's right edge sits past the
group's shared anchor.

**Choosing the anchor.** The anchor is the *smallest* of the group's right
edges (frame's own bounds, minus its own right inset, minus its already-
resolved ``RightIndent``) -- the one member that needed the least extra
margin to begin with. Every other member gets exactly enough additional
``RightIndent`` to pull its own text in to that same point. This is the only
direction that never asks a frame to hold more text in less width than it
already advertised: the anchor member is left untouched, and every other
member only gains a right margin it already had room for (its frame was
wider than the anchor's to begin with). Anchoring at the *largest* edge
instead would require pushing some member's text out past its own frame --
past what InDesign will actually draw. A member's word-wrap may need a line
or two more once its own width narrows to the anchor; that is the same
translation-growth risk every frame in an RTL book already carries (see
`textfit.py`), not a new one this module invents, and is deliberately left
for that pass rather than second-guessed here.

**Detecting a group.** A paragraph is a candidate sub-part label when the
very first text on its first line -- before any explicit line break --
matches a single letter or a run of digits, a period, and then either
whitespace or the end of that leading text (``a.``, ``b.\\t...``,
``1. ...``, ``12.\\t...``). A letter run and a digit run never continue one
another (`a` cannot be followed by `1`), so a page mixing a lettered list and
a numbered one nearby splits into separate groups on marker kind alone, the
same way two lists sharing a left margin already split on letter sequence
(below). Candidates in the same
spread are bucketed by their own frame's right edge (rounded to the nearest
point -- float noise from repeated transform arithmetic, not a real
difference), because that is exactly the signal the post-repositioning RTL
design uses to say "these belong to one list": every member of one group sat flush
on one shared right edge after repositioning. Within a
bucket, candidates are read in top-to-bottom document order and folded into
maximal runs of *consecutive* markers (``a,b,c`` or ``1,2,3`` continues; a repeated or
out-of-sequence marker starts a new run) -- so two lists that happen
to share a left margin (two questions stacked in one column) split back into
two groups on their own, without this module ever having to know they were
two different questions. A run of fewer than two members is not a group:
there is nothing to make consistent.

Multi-line sub-parts need no special handling: ``RightIndent`` is a whole-
paragraph property, so every wrapped line of a sub-part follows the same
adjustment its first line does, automatically. The label's own hang past
that margin (``FirstLineIndent``) is untouched by this module, exactly as
`set_text_direction` leaves it -- only the shared margin every line in the
paragraph measures from moves, never the label's own offset from it.
"""

from __future__ import annotations

import re

from pagebirdy.idml import rtl
from pagebirdy.idml.styles import StyleIndex

# A run of consecutive letters shorter than this has nothing to make
# consistent with -- one label alone was never staggered against a sibling.
_MIN_GROUP_SIZE = 2

# Sub-point float noise from repeated transform composition, not a real gap
# between two frames that were genuinely meant to share an edge.
_EDGE_EPSILON = 0.05

_LABEL_RE = re.compile(r"^\s*([A-Za-z]|\d+)\.(?=\s|$)")


def _flt(value, default: float = 0.0) -> float:
    try:
        return float(value) if value else default
    except (TypeError, ValueError):
        return default


def _leading_text(psr) -> str:
    """The text of a paragraph's own first line, up to its first `<Br/>`.

    A label can only ever be the very first thing on the first line, so
    nothing past the first break is relevant -- and stopping there keeps this
    cheap on a paragraph holding several sentences.
    """
    text = ""
    for csr in psr.findall("./{*}CharacterStyleRange"):
        for child in csr:
            name = rtl._localname(child)
            if name == "Content":
                text += child.text or ""
            elif name == "Br":
                return text
    return text


def _label_marker(psr) -> str | None:
    match = _LABEL_RE.match(_leading_text(psr))
    if match is None:
        return None
    text = match.group(1)
    return text.lower() if text.isalpha() else text


def _is_successor(marker: str, prev: str) -> bool:
    """True when `marker` continues the sequence `prev` started.

    Letters advance one Unicode codepoint (`a` -> `b`); digit runs advance as
    integers (`9` -> `10`, not `9` -> `:`), so a list running into double
    digits still reads as one continuing run. The two marker kinds never
    chain into each other.
    """
    if marker.isdigit() and prev.isdigit():
        return int(marker) == int(prev) + 1
    if marker.isalpha() and prev.isalpha():
        return ord(marker) == ord(prev) + 1
    return False


def _right_inset(frame_el) -> float:
    pref = frame_el.find("./{*}TextFramePreference")
    if pref is None:
        return 0.0
    spacing = pref.find("./{*}Properties/{*}InsetSpacing")
    if spacing is None:
        return 0.0
    items = [i.text for i in spacing.iter("{*}ListItem")]
    try:
        _top, _left, _bottom, right = items[:4]
        return float(right)
    except (ValueError, IndexError):
        return 0.0


def _usable_frame(frame_el) -> bool:
    """Same scope guard `textfit.py` uses: a frame this module can reason
    about the right edge of at all.

    Threaded (`PreviousTextFrame`/`NextTextFrame` not `"n"`), rotated, or
    vertically flipped frames have no single well-defined "own right edge" to
    anchor against, so they are left alone -- the safe default.
    """
    if (frame_el.get("PreviousTextFrame") not in (None, "n")
            or frame_el.get("NextTextFrame") not in (None, "n")):
        return False
    a, b, c, d = rtl.parse_transform(frame_el.get("ItemTransform"))[:4]
    return b == 0.0 and c == 0.0 and d > 0.0


def _candidates(spread, story_els: dict) -> list[dict]:
    items = [el for el in spread.iter() if rtl._is_page_item(el)]
    frames = [el for el in items if rtl._is(el, "TextFrame")]

    found: list[dict] = []
    for frame_el in frames:
        story_el = story_els.get(frame_el.get("ParentStory"))
        if story_el is None or not _usable_frame(frame_el):
            continue
        bounds = rtl.item_bounds(frame_el)
        if bounds is None:
            continue
        frame_right = bounds[2] - _right_inset(frame_el)
        for order, psr in enumerate(story_el.findall(".//{*}ParagraphStyleRange")):
            marker = _label_marker(psr)
            if marker is None:
                continue
            found.append({
                "marker": marker, "psr": psr,
                "top": bounds[1], "order": order,
                "frame_right": frame_right,
                "bucket_left": round(bounds[0]),
                "bucket_right": round(bounds[2]),
            })
    return found


def _runs(candidates: list[dict]) -> list[list[dict]]:
    """Maximal runs of consecutive letters, within one left-edge or right-edge bucket,
    in top-to-bottom document order."""
    runs: list[list[dict]] = []
    for bucket_key in ("bucket_left", "bucket_right"):
        by_bucket: dict[int, list[dict]] = {}
        for c in candidates:
            by_bucket.setdefault(c[bucket_key], []).append(c)

        for members in by_bucket.values():
            members.sort(key=lambda c: (c["top"], c["order"]))
            current: list[dict] = []
            for c in members:
                if current and _is_successor(c["marker"], current[-1]["marker"]):
                    current.append(c)
                else:
                    if len(current) >= _MIN_GROUP_SIZE:
                        runs.append(current)
                    current = [c]
            if len(current) >= _MIN_GROUP_SIZE:
                runs.append(current)

    unique_runs = []
    seen_keys = set()
    for run in runs:
        key = tuple(id(c["psr"]) for c in run)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_runs.append(run)
    return unique_runs


def normalize_subpart_indentation(documents: dict) -> dict:
    """Give every sibling in a detected sub-part list the same start edge.

    Must run after :func:`rtl.set_text_direction`: it reads each paragraph's
    *already-swapped* `RightIndent` (inline or inherited through its style)
    and only ever adds to it, so a paragraph that had a legitimate indent of
    its own for some other reason keeps it, on top of whatever this module
    adds to line its edge up with its siblings'.
    """
    report = {"rtl_subpart_groups_aligned": 0, "rtl_subpart_paragraphs_indented": 0}

    story_els: dict[str, object] = {}
    for name, tree in documents.items():
        if not name.startswith("Stories/"):
            continue
        for el in tree.iter():
            if rtl._is(el, "Story"):
                story_els[el.get("Self")] = el
    if not story_els:
        return report

    styles = documents.get("Resources/Styles.xml")
    preferences = documents.get("Resources/Preferences.xml")
    text_default = None
    if preferences is not None:
        for el in preferences.iter():
            if rtl._localname(el) == "TextDefault":
                text_default = el
                break
    index = StyleIndex(styles, text_default)

    for name, tree in documents.items():
        if not name.startswith("Spreads/"):
            continue
        for spread in tree.iter("Spread"):
            candidates = _candidates(spread, story_els)
            for group in _runs(candidates):
                edges = [c["frame_right"] - _flt(index.effective(c["psr"], None, "RightIndent"))
                         for c in group]
                anchor = min(edges)
                touched = False
                for c, edge in zip(group, edges):
                    delta = edge - anchor
                    if delta <= _EDGE_EPSILON:
                        continue
                    current = _flt(index.effective(c["psr"], None, "RightIndent"))
                    c["psr"].set("RightIndent", rtl._num(round(current + delta, 2)))
                    report["rtl_subpart_paragraphs_indented"] += 1
                    touched = True
                if touched:
                    report["rtl_subpart_groups_aligned"] += 1

    return report
