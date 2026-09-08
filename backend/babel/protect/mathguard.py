"""Math protection + paragraph segmentation.

Two placeholder styles, by trust and by what the translator needs to see:

* **Math-font spans** (rendered in `MathematicalPiLTStd`, etc.) are opaque —
  `⟦m0⟧`. Their glyphs are custom-encoded; the LLM must never see or touch them,
  and reassembly must never re-render them in a normal font.
* **Numeric tokens** in prose (`3/4`, `1–6`, `(-3, -2)`) are *value-visible* —
  `⟦=3/4⟧`. The LLM sees the number so it can inflect surrounding words for
  agreement ("5 manzanas" vs "1 manzana", gap C), but the token is still
  verified intact by the integrity gate and restored verbatim.

Segmentation (gap A): consecutive prose lines inside one PyMuPDF block are merged
into a single translation unit so the MT engine sees whole sentences, not visual
line fragments. Lines carrying a math-font span become their own segment.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import replace

from babel.models import BBox, Line, Segment

_DASHES = "–—−\\-"  # en-dash, em-dash, unicode minus, hyphen
_COORD = rf"\(\s*[{_DASHES}+]?\d[\d.,\s{_DASHES}+]*\)"
_NUM = (
    rf"[{_DASHES}+]?\d+(?:[.,]\d+)?"
    rf"(?:\s*[/×✕⋅·÷*+=<>≤≥{_DASHES}]\s*[{_DASHES}+]?\d+(?:[.,]\d+)?)*%?"
)
_BLANK = r"[_—–-]{2,}"
_TOKEN_RE = re.compile(f"(?:{_COORD})|(?:{_NUM})|(?:{_BLANK})")


class Allocator:
    """Hands out placeholder tokens for one segment and records their literals."""

    def __init__(self) -> None:
        self.map: dict[str, str] = {}
        self.fonts: dict[str, str] = {}
        self.widths: dict[str, float] = {}
        self.boxes: dict[str, BBox] = {}
        self.has_math_font = False
        self._n = 0

    def take_math(self, span) -> str:
        """Protect a math run. `span` may be a Span (PDF path, carries geometry)
        or a bare string (IDML path, where the layout engine handles setting)."""
        token = f"⟦m{self._n}⟧"
        self._n += 1
        self.has_math_font = True
        if isinstance(span, str):
            self.map[token] = span
            return token
        self.map[token] = span.text
        size = span.size or 1.0
        self.widths[token] = (span.bbox[2] - span.bbox[0]) / size
        self.boxes[token] = tuple(span.bbox)
        if not getattr(span, "atomic", False):
            # A simple glyph run can be redrawn from its own face; an atomic run
            # (a stacked fraction) has no character sequence and must be lifted
            # off the page as an image instead.
            self.fonts[token] = span.font
        return token

    def take_value(self, literal: str) -> str:
        # Value-derived: identical numbers collapse to one token (fine — same restore).
        token = f"⟦={literal}⟧"
        self.map[token] = literal
        return token

    def take_break(self, literal: str) -> str:
        """Protect a forced line/paragraph separator (U+2028/U+2029) — an
        InDesign soft-return embedded mid-run. Sent to an LLM raw, at least
        one model reliably corrupts it into unrelated control bytes (backspace,
        vertical tab) in its JSON reply, which then fails IDML's XML writer.
        Fixed token, not numbered: every occurrence restores to the same
        literal, so collapsing repeats onto one key is safe (unlike take_math,
        this never needs a distinct token per occurrence)."""
        token = "⟦br⟧"
        self.map[token] = literal
        return token


def _is_badge(span) -> bool:
    """A short numeral knocked out in white — the "1" inside the grey circle that
    starts each problem. It is artwork, not part of the sentence: translating it
    redacts the badge and re-draws the numeral in body colour on top of it."""
    r, g, b = (span.color >> 16) & 255, (span.color >> 8) & 255, span.color & 255
    return min(r, g, b) >= 240 and len(span.text.strip()) <= 3


_BULLET_CHARS = {"•", "◦", "‣", "▪", "●"}


def _is_bullet(span) -> bool:
    """A standalone leading list-marker glyph — decorative, not prose. Excluded
    from the translated body text so it isn't merged into the paragraph and
    redrawn in the paragraph's body color, losing e.g. a purple bullet set
    against black body text. Its own color/position is captured separately
    (see `_leading_bullet`) and redrawn explicitly as a dot: leaving it as
    untouched page content is not reliable, since PyMuPDF's `apply_redactions`
    can erase a bullet's glyph run as a side effect of redacting a nearby
    segment sharing the same content-stream text object, even when the
    bullet's own bbox was never included in the redaction rect."""
    return span.text.strip() in _BULLET_CHARS


def _leading_bullet(line: Line):
    """The line's leading bullet span, if any (after skipping a badge), for
    capturing its color/position before it is stripped from body text."""
    spans = list(line.spans)
    while spans and _is_badge(spans[0]):
        spans.pop(0)
    if spans and _is_bullet(spans[0]):
        return spans[0]
    return None


def _body_spans(line: Line) -> list:
    """The line's spans with any leading badge numerals or bullet marks dropped."""
    spans = list(line.spans)
    while spans and (_is_badge(spans[0]) or _is_bullet(spans[0])):
        spans.pop(0)
    return spans or list(line.spans)


def _body_bbox(line: Line) -> BBox:
    """The line's bbox narrowed to the spans we actually translate, so redaction
    never reaches the badge sitting to their left."""
    spans = _body_spans(line)
    return (min(s.bbox[0] for s in spans), line.bbox[1],
            max(s.bbox[2] for s in spans), line.bbox[3])


def _protect_line(line: Line, alloc: Allocator) -> str:
    spans = _body_spans(line)
    # Segment.bold is one flag for the whole (possibly multi-line) segment, so
    # a line that mixes bold and plain runs ("by length and by **height**")
    # needs its own markers or the emphasis is silently dropped. Only mark
    # when the line actually mixes styles — a uniformly bold/plain line is
    # already covered by the segment-level flag, and markers the LLM has to
    # carry through translation for nothing are just risk of it losing them.
    mixed = len({s.is_bold for s in spans if not s.is_math_font}) > 1
    parts: list[str] = []
    for span in spans:
        if span.is_math_font:
            parts.append(alloc.take_math(span))
            continue
        text = _TOKEN_RE.sub(lambda m: alloc.take_value(m.group(0)), span.text)
        if mixed and span.is_bold and text.strip():
            lead = text[: len(text) - len(text.lstrip())]
            trail = text[len(text.rstrip()):]
            parts.append(f"{lead}**{text.strip()}**{trail}")
        else:
            parts.append(text)
    return "".join(parts)


def _accent_color(lines: list[Line], body_color: int) -> int | None:
    """Color of a bold inline-emphasis run when it differs from the paragraph's
    body color — e.g. a purple "SAY" or "BONUS:" set against black prose.
    Only the emphasised (bold) run gets re-marked in this color at reassembly;
    picking one shared accent per segment matches every case seen so far,
    where a paragraph highlights a single term or label, not several colors."""
    for ln in lines:
        for span in _body_spans(ln):
            if span.is_bold and not span.is_math_font and span.color != body_color:
                return span.color
    return None


def _accent_size_ratio(lines: list[Line], body_size: float) -> float | None:
    """Point-size of a bold inline-emphasis run relative to the paragraph's
    body size, when it differs — e.g. "SAY" set two points larger than the
    prose around it. Reassembly only distinguishes per-word style for bold
    runs (see `_place`'s `bold_words`), so this reuses that same gate rather
    than introducing a second, unrelated notion of "emphasis".

    A ratio close to 1.0 is not worth carrying: reassembly already fits body
    text to a shrunk size when the translation runs long, and a 2-3% size
    difference surviving that fit is noise, not a callout the source cared
    about — the note it would leave in the review UI would never match what a
    person actually sees.
    """
    if not body_size:
        return None
    for ln in lines:
        for span in _body_spans(ln):
            if span.is_bold and not span.is_math_font and abs(span.size - body_size) > 0.1 * body_size:
                return span.size / body_size
    return None


def _union(bboxes: list[BBox]) -> BBox:
    x0 = min(b[0] for b in bboxes)
    y0 = min(b[1] for b in bboxes)
    x1 = max(b[2] for b in bboxes)
    y1 = max(b[3] for b in bboxes)
    return (x0, y0, x1, y1)


def _make_segment(lines: list[Line], sid: str) -> Segment:
    alloc = Allocator()
    texts = [_protect_line(ln, alloc) for ln in lines]
    source = " ".join(t.strip() for t in texts).strip() if len(lines) > 1 else texts[0]
    dom = max((ln.dominant for ln in lines), key=lambda s: s.bbox[2] - s.bbox[0])
    bboxes = [_body_bbox(ln) for ln in lines]
    baselines = [ln.baseline for ln in lines]
    bullet = _leading_bullet(lines[0])
    return Segment(
        id=sid,
        page=lines[0].page,
        bbox=_union(bboxes),
        font=dom.font,
        size=dom.size,
        color=dom.color,
        source=source,
        placeholders=alloc.map,
        math_fonts=alloc.fonts,
        math_widths=alloc.widths,
        math_boxes=alloc.boxes,
        bboxes=bboxes,
        baselines=baselines,
        has_math_font=alloc.has_math_font,
        rotation=lines[0].rotation,
        bold=lines[0].is_bold,
        italic=lines[0].is_italic,
        accent_color=_accent_color(lines, dom.color),
        accent_size_ratio=_accent_size_ratio(lines, dom.size),
        bullet_color=bullet.color if bullet else None,
        bullet_bbox=tuple(bullet.bbox) if bullet else None,
        from_ocr=lines[0].from_ocr,
        in_image=lines[0].in_image,
    )


def build_segment(line: Line, index: int) -> Segment:
    """Single-line segment (kept for tests / simple callers)."""
    return _make_segment([line], f"p{line.page}-l{index}")


def _same_row(a: Line, b: Line) -> bool:
    """Do these two lines sit side by side on one visual row?"""
    overlap = min(a.bbox[3], b.bbox[3]) - max(a.bbox[1], b.bbox[1])
    shortest = min(a.bbox[3] - a.bbox[1], b.bbox[3] - b.bbox[1])
    return overlap > 0.5 * shortest


def _columns_align(a: Line, b: Line) -> bool:
    """Do these two stacked lines occupy the same column?

    Overlap alone, measured against only the narrower box, passes for free
    whenever a small floating annotation (a single counting-arrow digit, a
    badge number) happens to sit anywhere under a much wider paragraph line —
    a 9pt-wide box needs only 4.5pt of overlap with a 270pt-wide one to clear
    "50% of the narrower side". That merged a standalone "1" label into the
    prose line above it, corrupting both the sentence and the reassembly of
    the annotation itself. Requiring the overlap to also be a meaningful slice
    of the *wider* box demands the two actually run the same span, not just
    touch — genuine wrapped-paragraph lines and same-width list entries still
    clear this easily since they share nearly their whole width.
    """
    overlap = min(a.bbox[2], b.bbox[2]) - max(a.bbox[0], b.bbox[0])
    width_a, width_b = a.bbox[2] - a.bbox[0], b.bbox[2] - b.bbox[0]
    narrowest, widest = min(width_a, width_b), max(width_a, width_b)
    return overlap > 0.5 * narrowest and overlap > 0.2 * widest


def _touching(prev: Line, ln: Line) -> bool:
    """Are these lines set solid, i.e. one on the very next baseline?

    PyMuPDF splits a ragged display phrase like "See the Grade 8 Math / concepts
    covered in / this packet!" into a separate block per line. Translating each
    line alone produces three disconnected fragments, so blocks that follow each
    other with no leading gap are rejoined. The threshold is deliberately tight:
    a real paragraph break leaves far more space than this.
    """
    gap = ln.bbox[1] - prev.bbox[3]
    return gap <= 0.25 * (prev.bbox[3] - prev.bbox[1])


def _continues_geometry(prev: Line, ln: Line) -> bool:
    """Would `ln` merge into `prev`'s segment on layout/typography grounds alone
    — same block-or-touching, different row, matching size? Shared by
    `_continues` and `_short_list_run_lines`, which both need this gate before
    layering their own content-based exception on top of it.
    """
    if prev.page != ln.page or prev.rotation != ln.rotation:
        return False
    if prev.block != ln.block and not _touching(prev, ln):
        return False
    if _same_row(prev, ln):
        return False
    # A heading and the subtitle under it share a block and a column, but they
    # are not one sentence: merging them translates both as a single string and
    # re-sets them at one size, destroying the type hierarchy. Different type
    # size means different piece of text.
    a, b = prev.dominant.size, ln.dominant.size
    if max(a, b) and abs(a - b) > 0.15 * max(a, b):
        return False
    # Same reasoning for weight: a bold section header ("Multilingual
    # Glossary") sitting right above its plain-weight entries ("count on",
    # "count back") can be well within the size tolerance above and still be
    # two different pieces of text — the header names the list, it does not
    # continue into it. Merging them forces one segment through one fit-to-box
    # pass, which then has to compromise between the header's short line and
    # the entries' longer translated text (wrong size for both).
    return prev.is_bold == ln.is_bold


def _continues(prev: Line, ln: Line, list_lines: frozenset[int] = frozenset()) -> bool:
    """Is `ln` the next line of the same paragraph — or the next table cell?

    PyMuPDF reports every cell of a table row as a separate "line" inside one
    block, so merging a whole block flattens `Concept | Practice | Fluency` into
    a single string that is then translated and re-drawn as one run of prose,
    losing the columns. Two rules keep cells apart without hardcoding any
    layout: lines that share a row are different cells, and stacked lines only
    continue a cell when their columns actually line up.
    """
    if not _continues_geometry(prev, ln):
        return False
    # A line starting a new bullet is a new list item, not a continuation of
    # the previous one — merging both into one string loses the bullet
    # boundary and the translated text comes back as one run-on paragraph
    # with the "•" stranded mid-sentence.
    if ln.raw_text.lstrip().startswith("•"):
        return False
    # An unbulleted list (a vocabulary column: "above" / "across" / "around",
    # one term per line) looks like prose to every check above — same block,
    # same column, same size, short line. `list_lines` flags only lines that
    # are part of a run of 3+ such short lines in a row (see
    # `_short_list_run_lines`): a single short line, or two, is an ordinary
    # wrapped title ending short, not a list — splitting those loses the MT
    # context that ties them into one phrase.
    if id(prev) in list_lines and id(ln) in list_lines:
        return False
    return _columns_align(prev, ln)


def _short_list_item(line: Line) -> bool:
    """At most three words — one entry of an unbulleted vertical list.

    Covers both a bare vocabulary term ("above") and a number-pair entry
    ("1 and 9" — three words once "and" is counted): both are one self-
    contained list line, not prose that continues onto the next line."""
    words = line.raw_text.split()
    return 0 < len(words) <= 3


def _short_list_run_lines(lines: list[Line]) -> frozenset[int]:
    """`id()`s of lines belonging to a run of 4+ consecutive short lines that
    would otherwise merge (same block/column/size) — a vocabulary column, not
    a title that merely wraps short across two or three lines. A 2-3 line
    title ending short ("Understanding / Expressions and / Exponents") is
    common enough that a lower bar mistook it for a list too often; a real
    vocabulary column runs longer than any title does."""
    marked: list[int] = []
    run: list[Line] = []

    def flush():
        if len(run) >= 4:
            marked.extend(id(ln) for ln in run)
        run.clear()

    for ln in lines:
        chains = bool(run) and _continues_geometry(run[-1], ln) and _columns_align(run[-1], ln)
        if chains and _short_list_item(ln):
            run.append(ln)
        else:
            flush()
            run = [ln] if _short_list_item(ln) else []
    flush()
    return frozenset(marked)


_FRACTION_PAD = 2.0  # x slack when matching a numerator/denominator to its rule


def _merge_fractions(lines: list[Line]) -> list[Line]:
    """Fold each stacked fraction's three pieces into one atomic span.

    A fraction is set as a rule on its own line, the numerator riding at the END
    of the line above and the denominator at the START of the line below, all
    sharing one narrow x window. None of those pieces is a character sequence:
    read as text they are just loose digits, and translating the surrounding
    prose moves them away from the rule. Folding all three into a single opaque
    run lets the sentence be translated while the fraction travels with it as
    one unit, reproduced later from the page image.
    """
    rules = [
        i for i, ln in enumerate(lines)
        if ln.spans and ln.raw_text.strip() and (
            all(s.is_math_font for s in ln.spans)
            or re.fullmatch(r"[_—–-]{1,}", ln.raw_text.strip())
        )
    ]
    drop: set[int] = set()
    for i in rules:
        rule = lines[i]
        above = next((j for j in range(i - 1, -1, -1)
                      if j not in drop and lines[j].page == rule.page), None)
        below = next((j for j in range(i + 1, len(lines))
                      if lines[j].page == rule.page), None)
        if above is None or below is None:
            continue
        num, den = lines[above], lines[below]
        # Ignore the whitespace-only spans that pad either side of the digits.
        top_at = next((k for k in range(len(num.spans) - 1, -1, -1)
                       if num.spans[k].text.strip()), None)
        bottom_at = next((k for k, sp in enumerate(den.spans) if sp.text.strip()), None)
        if top_at is None or bottom_at is None:
            continue
        top, bottom = num.spans[top_at], den.spans[bottom_at]
        
        # If the PDF reading order is inverted (denominator read before numerator),
        # their physical positions will be swapped relative to the reading order.
        if top.bbox[3] > bottom.bbox[1] + _FRACTION_PAD:
            top, bottom = bottom, top
            num, den = den, num

        # The rule's own box is inflated by the math face's metrics, so it is no
        # use as a vertical reference; the two digits must simply not overlap.
        if top.bbox[3] > bottom.bbox[1] + _FRACTION_PAD:
            continue
        window = (rule.bbox[0] - _FRACTION_PAD, rule.bbox[2] + _FRACTION_PAD)
        if not (window[0] <= top.bbox[0] and top.bbox[2] <= window[1]):
            continue
        if not (window[0] <= bottom.bbox[0] and bottom.bbox[2] <= window[1]):
            continue

        fraction = replace(
            top,
            text=f"{top.text.strip()}/{bottom.text.strip()}",
            font="MathematicalPi",  # forces is_math_font True so it's redrawn as an image
            bbox=(min(top.bbox[0], rule.bbox[0], bottom.bbox[0]), num.bbox[1],
                  max(top.bbox[2], rule.bbox[2], bottom.bbox[2]), den.bbox[3]),
            atomic=True,
        )
        # The text after the denominator continues the same sentence on the same
        # visual row, so numerator line, rule and denominator line collapse into
        # one line. Left as two, they overlap vertically and are read as separate
        # table cells — translated apart and drawn on top of each other.
        lines[above] = replace(
            num,
            spans=num.spans[:top_at] + [fraction] + den.spans[bottom_at + 1:],
            bbox=(min(num.bbox[0], den.bbox[0]), min(num.bbox[1], den.bbox[1]),
                  max(num.bbox[2], den.bbox[2]), max(num.bbox[3], den.bbox[3])),
        )
        drop.add(i)
        drop.add(below)
    return [ln for i, ln in enumerate(lines) if i not in drop]


_COL_TOL = 2.0  # points; two edges this close are the same column
_MIN_COL_HITS = 3  # an edge must recur this often before it counts as a column


def _column_starts(lines: list[Line]) -> dict[int, list[float]]:
    """Left edges that recur often enough on a page to be real table columns."""
    per_page: dict[int, Counter] = {}
    for ln in lines:
        per_page.setdefault(ln.page, Counter())[round(ln.bbox[0] / _COL_TOL)] += 1
    return {
        page: sorted(k * _COL_TOL for k, hits in counter.items() if hits >= _MIN_COL_HITS)
        for page, counter in per_page.items()
    }


def _split_at_columns(line: Line, columns: list[float]) -> list[Line]:
    """Cut a line where it crosses into a later column of the same table.

    A row whose title runs long enough to leave no dot leader comes back from
    PyMuPDF as ONE line holding both the title and the page number, while every
    other row reports them as separate cells. Left alone it translates as
    "…notación científica 8" with the page number embedded in the sentence.
    The cut points are the column edges the page itself demonstrates, so nothing
    about this table's geometry is assumed.
    """
    if len(line.spans) < 2 or not columns:
        return [line]

    cuts = []
    _MIN_COL_GAP = 10.0
    for i, span in enumerate(line.spans[1:], start=1):
        if not span.text.strip():
            continue
        starts_column = any(
            abs(span.bbox[0] - c) <= _COL_TOL for c in columns if c > line.bbox[0] + _COL_TOL
        )
        # A table column break is marked by a significant visual gap.
        # A simple space character mid-sentence must never split a sentence in two,
        # even if it happens to align with a column edge.
        last_visible = next((s for s in reversed(line.spans[:i]) if s.text.strip()), None)
        gap = span.bbox[0] - last_visible.bbox[2] if last_visible else 0
        after_gap = gap >= _MIN_COL_GAP

        if starts_column and after_gap:
            cuts.append(i)
            
    if not cuts:
        return [line]

    pieces: list[Line] = []
    for start, end in zip([0] + cuts, cuts + [len(line.spans)]):
        chunk = [s for s in line.spans[start:end] if s.text.strip()]
        if not chunk:
            continue
        bbox = (min(s.bbox[0] for s in chunk), line.bbox[1],
                max(s.bbox[2] for s in chunk), line.bbox[3])
        pieces.append(replace(line, spans=chunk, bbox=bbox))
    return pieces or [line]


def build_segments(lines: list[Line]) -> list[Segment]:
    """Group consecutive prose lines of one cell into paragraph segments;
    table cells and math-font lines stay standalone."""
    lines = _merge_fractions(list(lines))
    columns = _column_starts(lines)
    lines = [
        piece
        for ln in lines
        for piece in _split_at_columns(ln, columns.get(ln.page, []))
    ]
    list_lines = _short_list_run_lines(lines)

    segments: list[Segment] = []
    buf: list[Line] = []
    counter = 0

    def flush() -> None:
        nonlocal counter, buf
        if buf:
            segments.append(_make_segment(buf, f"p{buf[0].page}-s{counter}"))
            counter += 1
            buf = []

    for ln in lines:
        if ln.has_math_font:
            flush()
            segments.append(_make_segment([ln], f"p{ln.page}-s{counter}"))
            counter += 1
            continue
        if buf and not _continues(buf[-1], ln, list_lines):
            flush()
        buf.append(ln)
    flush()
    return segments
