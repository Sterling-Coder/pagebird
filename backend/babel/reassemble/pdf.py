"""PDF reassembly: place translated target text back into the source layout.

Policy (this path is "draft + manual finish", safety over completeness):

  * REPLACE a segment only when it has no opaque math-font glyphs
    (`has_math_font` is False) and the engine produced a real translation.
    Numeric tokens like `⟦=3/4⟧` restore to plain digits that render fine in a
    normal font, so prose-with-numbers lines ARE replaceable.
  * A segment may cover several source lines (a merged paragraph). We redact all
    of them and set the Spanish back on those same baselines, shrinking the size
    until it occupies AT MOST the source's own line count — the target never
    grows past the footprint the English had, so it cannot collide with the
    segment below it.
  * Bold / italic are preserved by picking the matching font variant (gap E).
  * Anything with math-font glyphs is left untouched and flagged (gap: never
    corrupt a rendered equation).
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, replace
from dataclasses import replace as replace_dataclass  # for scopes that shadow `replace`
from difflib import SequenceMatcher
from functools import lru_cache

import fitz

from babel import fonts as babel_fonts
from babel import languages
from babel.models import BBox, Segment, Span
from babel.protect import mathguard

_MIN_SIZE = 5.0
# PyMuPDF line boxes are metric-derived, so the baseline sits this far down the
# box (ascender / (ascender - descender) for a normal text face).
_BASE_RATIO = 0.81
# A shared column size never drops below this fraction of the column's natural
# size — one runaway row must not shrink the whole table.
_COLUMN_FLOOR = 0.7
_PAGE_MARGIN = 18.0  # keep reflowed text clear of the page edge
_MATH_DPI = 400  # resolution for fractions lifted off the page as images

# Font candidates come from the language registry: Latin needs Arial-class faces,
# Chinese/Japanese/Korean/Devanagari need their own. The base-14 "helv" fallback
# is Latin-1 only and silently drops glyphs, so a language whose font is missing
# is a hard error rather than a page of blanks.


@dataclass
class LineOutcome:
    segment_id: str
    page: int
    action: str  # replaced | skipped_math | skipped_untranslated | overflow
    detail: str = ""


_FONT_DIRS = ("C:/Windows/Fonts", os.path.expanduser("~/Library/Fonts"),
              "/Library/Fonts", "/System/Library/Fonts", "/usr/share/fonts")


def _alias(path: str) -> str:
    """A distinct PDF font name per font FILE.

    PyMuPDF registers a fontfile against the name it is given and reuses that
    registration for every later call with the same name on that page. Sharing
    one alias therefore made whichever face was inserted first — usually the bold
    heading at the top of a page — swallow the regular text underneath it.
    """
    return "b" + hashlib.md5(path.encode("utf-8")).hexdigest()[:10]


def _norm(name: str) -> str:
    """Font identity for matching: drop the subset tag and any punctuation."""
    name = name.split("+")[-1]  # "ZZVIPY+Jubilat-Regular" -> "Jubilat-Regular"
    return "".join(c for c in name if c.isalnum()).lower()


@lru_cache(maxsize=1)
def _system_fonts() -> dict[str, str]:
    """Installed fonts indexed by normalised family+style name."""
    index: dict[str, str] = {}
    for directory in _FONT_DIRS:
        if not os.path.isdir(directory):
            continue
        for root, _, files in os.walk(directory):
            for f in files:
                if f.lower().endswith((".ttf", ".otf")):
                    index.setdefault(_norm(os.path.splitext(f)[0]), os.path.join(root, f))
    return index


def _source_font(seg: Segment, text: str) -> str | None:
    """The document's own typeface, when it is installed and can set `text`.

    Keeping the source face is what makes the translation look like the original
    rather than a retype. The embedded copy inside the PDF is no help: it is a
    subset containing only the glyphs the English needed, so it has no á, ñ or ¿.
    If the real family is installed we use it, after confirming it covers every
    character the target actually needs.
    """
    if not seg.font:
        return None
    path = _system_fonts().get(_norm(seg.font))
    if not path:
        return None
    try:
        font = _font(path)
    except Exception:
        return None
    return path if all(font.has_glyph(ord(c)) for c in set(text)) else None


_MATH_TOKEN = re.compile(r"(⟦m\d+⟧)")


def _embedded_faces(doc) -> dict[str, bytes]:
    """The document's own font programs, by normalised name.

    A math-font run has no recoverable character identity — this document's
    ToUnicode map claims the "=" glyph is the digit 2 — so the only faithful way
    to reproduce it is to draw the original character code in the original face.
    Re-embedding the face from the source PDF does exactly that.
    """
    faces: dict[str, bytes] = {}
    for pno in range(doc.page_count):
        for info in doc.load_page(pno).get_fonts(full=True):
            key = _norm(info[3])
            if key in faces:
                continue
            try:
                extracted = doc.extract_font(info[0])
            except Exception:
                continue
            buf = next((x for x in extracted if isinstance(x, (bytes, bytearray))), None)
            if buf:
                faces[key] = bytes(buf)
    return faces


def _math_drawable(seg: Segment, faces: dict[str, bytes]) -> bool:
    """Can every math run in this segment be redrawn in its original face?

    Each glyph needs its face available and its width known, and must stand as
    its own word. A token wedged inside a word would need the run split
    mid-word, which is not worth guessing at — those segments stay untouched.
    """
    tokens = set(_MATH_TOKEN.findall(seg.source))
    if not tokens:
        return False
    for token in tokens:
        by_face = _norm(seg.math_fonts.get(token, "")) in faces
        by_image = token in seg.math_boxes
        if not (by_face or by_image):
            return False
        if token not in seg.math_widths:
            return False
    return True


_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _split_bold(text: str) -> tuple[str, list[bool]]:
    """Strip `**bold**` markers, returning the plain (space-normalised) text
    alongside a per-word bold flag list of the same length as `text.split()`.

    Removing markers by cutting each word out of its `**...**` segment and
    rejoining with a space would insert a space that was never there — a
    marker sits flush against trailing punctuation ("**altura**.") with
    nothing between them. Instead strip the markers character-by-character,
    keeping every other character (including that attached ".") exactly
    where it was, and only tokenize on real whitespace afterward.
    """
    plain_chars: list[str] = []
    bold_mask: list[bool] = []
    pos = 0
    for m in _BOLD_RE.finditer(text):
        before = text[pos:m.start()]
        plain_chars.append(before)
        bold_mask.extend([False] * len(before))
        inner = m.group(1)
        plain_chars.append(inner)
        bold_mask.extend([True] * len(inner))
        pos = m.end()
    tail = text[pos:]
    plain_chars.append(tail)
    bold_mask.extend([False] * len(tail))
    plain = "".join(plain_chars)

    words: list[str] = []
    bold: list[bool] = []
    for tok in re.finditer(r"\S+", plain):
        words.append(tok.group())
        bold.append(any(bold_mask[tok.start():tok.end()]))
    return " ".join(words), bold


def _atoms(seg: Segment) -> list[tuple[str, bool]]:
    """The target as (word, is_math) atoms, value placeholders already restored."""
    raw = seg.target if seg.target is not None else seg.source
    for token, literal in seg.placeholders.items():
        if not _MATH_TOKEN.fullmatch(token):
            raw = raw.replace(token, literal)

    words: list[list[tuple[str, bool]]] = []
    current: list[tuple[str, bool]] = []
    for piece in _MATH_TOKEN.split(raw):
        if not piece:
            continue
        if _MATH_TOKEN.fullmatch(piece):
            current.append((piece, True))
            continue
        chunks = piece.split()
        if not chunks:  # whitespace only: ends the word in progress
            if current:
                words.append(current)
                current = []
            continue
        if piece[:1].isspace() and current:
            words.append(current)
            current = []
        for i, chunk in enumerate(chunks):
            if i:
                words.append(current)
                current = []
            current.append((chunk, False))
        if piece[-1:].isspace():
            words.append(current)
            current = []
    if current:
        words.append(current)
    return [w for w in words if w]


def _atom_width(word: list[tuple[str, bool]], seg: Segment,
                font: fitz.Font, size: float) -> float:
    total = 0.0
    for piece, is_math in word:
        total += seg.math_widths[piece] * size if is_math else font.text_length(piece, size)
    return total


def _wrap_atoms(atoms, seg, font, size, width) -> list[list[tuple[str, bool]]] | None:
    """Greedy wrap over mixed text/math atoms; None if one atom cannot fit."""
    space = font.text_length(" ", size)
    lines: list[list[tuple[str, bool]]] = []
    cur: list[tuple[str, bool]] = []
    used = 0.0
    for atom in atoms:
        w = _atom_width(atom, seg, font, size)
        if w > width:
            return None
        advance = w if not cur else w + space
        if cur and used + advance > width:
            lines.append(cur)
            cur, used = [atom], w
        else:
            cur.append(atom)
            used += advance
    if cur:
        lines.append(cur)
    return lines or [[]]


_MATH_TOUCH = 1.0  # pt² of overlap before a box counts as touching the math


def _overlapping_math(replace: list[Segment], page_segs: list[Segment]) -> set[str]:
    """Ids of segments whose box runs into a rendered equation on the same page.

    A stacked fraction is set as three overlapping lines — the numerator at the
    end of one line, the rule and the denominator at the start of the next — so
    a prose line beside one carries no math font itself yet its box still covers
    part of the fraction. Redacting it deletes the rule and the denominator, and
    the translation is then drawn on top of what is left. Such segments are left
    in the source language, exactly as a segment containing math already is:
    never corrupt a rendered equation.
    """
    redrawn = {s.id for s in replace}
    math_boxes = [fitz.Rect(s.bbox) for s in page_segs
                  if s.has_math_font and s.id not in redrawn]
    if not math_boxes:
        return set()
    hit: set[str] = set()
    for seg in replace:
        for bb in (seg.bboxes or [seg.bbox]):
            rect = fitz.Rect(bb)
            for box in math_boxes:
                ix = rect & box
                # Ignore thin sliver overlaps (e.g. line height leading overlap between adjacent rows)
                if ix.get_area() > _MATH_TOUCH and min(ix.width, ix.height) > 3.0:
                    hit.add(seg.id)
                    break
            if seg.id in hit:
                break
    return hit


def _collateral_casualties(replace: list[Segment], page_segs: list[Segment]) -> list[Segment]:
    """Untranslated segments whose box overlaps a redaction rect from `replace`.

    A big display digit ("1" in a lesson-number star) and its small caption
    ("LESSON") are separate lines whose boxes overlap by a few points — the
    digit's tall glyph rides up into the caption's row. `apply_redactions`
    erases any glyph run its rect touches, so once the caption is redacted
    for translation the digit vanishes with it, even though nothing skipped
    it directly. Redraw it too (with its own — unchanged — text) so it survives.
    """
    redrawn = {s.id for s in replace}
    rects = [fitz.Rect(bb) for s in replace for bb in (s.bboxes or [s.bbox])]
    casualties = []
    for seg in page_segs:
        if seg.id in redrawn or seg.has_math_font or seg.target is None:
            continue
        boxes = [fitz.Rect(bb) for bb in (seg.bboxes or [seg.bbox])]
        if any((r & b).get_area() > _MATH_TOUCH for r in rects for b in boxes):
            casualties.append(seg)
    return casualties


def _serif_faces(doc) -> set[str]:
    """Normalised names of the faces the document itself declares as serif.

    Every PDF font carries a /Flags integer in its FontDescriptor whose bit 2
    means serif. That is the document's own statement about its type, so a serif
    display face is substituted with a serif rather than flattened to the sans
    default. PyMuPDF's per-span `flags` cannot be used for this — it reports
    serif for Myriad Pro, which is a sans.
    """
    serif: set[str] = set()
    seen: set[str] = set()
    for pno in range(doc.page_count):
        for info in doc.load_page(pno).get_fonts(full=True):
            xref, base = info[0], info[3]
            key = _norm(base)
            if key in seen:
                continue
            seen.add(key)
            desc = doc.xref_get_key(xref, "FontDescriptor")
            if desc[0] != "xref":
                continue
            flags = doc.xref_get_key(int(desc[1].split()[0]), "Flags")
            if flags[0] == "int" and int(flags[1]) & 2:
                serif.add(key)
    return serif


# Typographic characters and the plain equivalents they degrade to. Every one is
# a variant of an ASCII character that a text face may simply not carry: Nirmala
# has no U+2011 non-breaking hyphen, Malgun Gothic no U+2212 minus sign. The
# extracted text still reads correctly, so nothing downstream notices -- the
# defect is only visible as an empty box on the printed page.
#
# Substitution happens per character and only when the chosen font cannot draw
# it, so a face that does carry the real dash keeps it.
_TYPOGRAPHIC_FALLBACK = {
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
    "―": "-", "−": "-", "­": "-",
    "‘": "'", "’": "'", "‚": ",", "‛": "'",
    "“": '"', "”": '"', "„": '"',
    "…": "...", "•": "*", "·": "*",
    " ": " ", " ": " ", " ": " ", " ": " ", " ": " ",
    "×": "x", "⁄": "/", "′": "'", "″": '"',
}


def _drawable(text: str, font) -> str:
    """`text` with any character this font cannot draw swapped for a plain one.

    A character the face lacks is drawn as an empty box while the text layer
    still says the right thing, so it survives every text-level check and only
    shows up on the page. Where a plain equivalent exists and *is* drawable, use
    it; anything else is left alone rather than silently deleted.
    """
    if font is None:
        return text
    out = []
    for ch in text:
        if font.has_glyph(ord(ch)):
            out.append(ch)
            continue
        fallback = _TYPOGRAPHIC_FALLBACK.get(ch)
        if fallback and all(font.has_glyph(ord(c)) for c in fallback):
            out.append(fallback)
        else:
            out.append(ch)
    return "".join(out)


def _font_for(seg: Segment, lang, text: str = "", serif: frozenset = frozenset()
              ) -> str | None:
    if text:
        original = _source_font(seg, text)
        if original:
            return original
    if seg.bold and seg.italic:
        order = ["bolditalic", "bold", "regular"]
    elif seg.bold:
        order = ["bold", "regular"]
    elif seg.italic:
        order = ["italic", "regular"]
    else:
        order = ["regular"]
    if _norm(seg.font or "") in serif:
        order = [f"serif{style}" for style in order] + order
    for style in order:
        found = babel_fonts.resolve(lang.fonts.get(style, ()))
        if found:
            return found
    return None  # fall back to built-in helv (Latin-1)


def _rgb(color: int) -> tuple[float, float, float]:
    return ((color >> 16 & 255) / 255, (color >> 8 & 255) / 255, (color & 255) / 255)


_CONTAINED = 0.9  # fraction of a line's own area that must sit inside another for it to count as nested
# Similarity above which two overlapping runs are the same content read twice.
# Real duplicates measure >= 0.93 even with an OCR typo; unrelated neighbours <= 0.27.
_SAME_CONTENT = 0.8


def _content_key(text: str) -> str:
    """Text reduced to what two readings of the same content should share."""
    return " ".join(text.split()).casefold()


def _hidden_duplicates(page_segs: list[Segment]) -> set[str]:
    """Ids of segments that sit almost entirely inside another segment's box.

    Some source PDFs carry an invisible duplicate text run under a styled
    headline — same white fill, a smaller/thinner font, fully eclipsed by the
    bold glyphs drawn on top of it in the same colour, so it never renders.
    Translating it independently reflows it at a different size and draws it
    back in, and nothing eclipses it anymore: the "hidden" copy surfaces as
    garbled overlapping text. A real, unrelated line practically never nests
    fully inside another line's box, so containment alone is a safe tell —
    leave the nested one untouched rather than risk unmasking it.
    """
    hidden: set[str] = set()
    for a in page_segs:
        rect_a = fitz.Rect(a.bbox)
        area_a = rect_a.get_area()
        if not area_a:
            continue
        for b in page_segs:
            if a.id == b.id:
                continue
            rect_b = fitz.Rect(b.bbox)
            if rect_b.get_area() <= area_a:
                continue
            if (rect_a & rect_b).get_area() >= _CONTAINED * area_a:
                hidden.add(a.id)
    return hidden


def _image_shadowed_duplicates(page_segs: list[Segment]) -> set[str]:
    """Ids of ordinary segments that duplicate an `in_image` one's content.

    A raster banner can sit on top of an ordinary PDF text run for the same
    word, drawn earlier in z-order — invisible in the source because the
    opaque image covers it, but still a real, translatable segment. Once
    OCR-based redaction blanks that image's pixels to remove the burned-in
    English, the previously-hidden text's own translated draw would surface
    and overlap the OCR-recovered one.

    An OCR-estimated box and a real text-metrics box for the same glyphs
    rarely align well (OCR clips ascenders/descenders, real text boxes are
    exact) — a geometric overlap fraction big enough to be a safe tell on
    its own turned out too strict in practice (a real case measured ~31%).
    Requiring the two segments' English text to actually match (like
    `_replaceable`'s no-op check, casefolded) alongside any overlap at all
    is the more reliable signal: it's tied to genuine duplicate content, not
    just how tightly two independently-measured boxes happen to align. The
    `in_image` segment is always the one kept: it carries the actually
    visible, OCR-recovered content.

    Matching has to tolerate OCR noise. Exact containment missed a real
    headline whose OCR read came back "Math on tha go" against the text run's
    "Math on the Go" — one wrong letter, so neither string contained the other
    and both were drawn, landing the two Arabic renderings on top of each
    other. Measured over the real pairs, true duplicates score 0.93 and above
    while unrelated neighbours score 0.27 and below, so `_SAME_CONTENT` sits in
    the empty middle of that gap rather than at either edge.    """
    hidden: set[str] = set()
    image_segs = [s for s in page_segs if s.in_image]
    if not image_segs:
        return hidden
    for other in page_segs:
        if other.in_image:
            continue
        other_text = _content_key(other.restored_source())
        if not other_text:
            continue
        rect_other = fitz.Rect(other.bbox)
        for img in image_segs:
            if (rect_other & fitz.Rect(img.bbox)).is_empty:
                continue
            img_text = _content_key(img.restored_source())
            if not img_text:
                continue
            if (other_text in img_text or img_text in other_text
                    or SequenceMatcher(None, other_text, img_text).ratio()
                    >= _SAME_CONTENT):
                hidden.add(other.id)
                break
    return hidden


def _replaceable(seg: Segment, faces: dict[str, bytes] | None = None) -> bool:
    # Compare against the RESTORED source: `seg.source` still carries ⟦…⟧ tokens,
    # so comparing to it never matches and passthrough (identity-engine) output
    # was being redacted and redrawn for no reason.
    #
    # casefold: a brand wordmark ("I-Ready Connect") sometimes comes back with
    # only its case flipped — not a real translation. Redacting it anyway is
    # actively harmful: the visible glyphs are vector art (a logo), which the
    # table-safe redaction (graphics=PDF_REDACT_LINE_ART_NONE, see below) never
    # strips, so the redrawn copy just doubles up on top of the untouched original.
    return (
        seg.status in ("translated", "tm_hit")
        and seg.target is not None
        and (not seg.has_math_font or _math_drawable(seg, faces or {}))
        and seg.restored_target().strip().casefold() != seg.restored_source().strip().casefold()
    )


# --- RTL page mirroring ------------------------------------------------------
#
# An RTL edition mirrors the page: what sat against the left margin belongs
# against the right one. Two pieces do the work — `mirror_bbox` moves the boxes
# we place text into, `mirror_page` flips everything already drawn on the page.


def mirror_bbox(bbox: BBox, page_width: float) -> BBox:
    """Reflect a box across the page's vertical centre line.

    Width and vertical position are untouched, so a mirrored box still fits the
    same text at the same size — only the side of the page changes.
    """
    x0, y0, x1, y1 = bbox
    return (page_width - x1, y0, page_width - x0, y1)


# How far across a numeral's own height the mark it is knocked out of may reach.
# The problem-number discs measure 16pt around a 12.6pt numeral — 1.3 — while
# anything else a numeral happens to sit on, a rule or a grid, runs off past any
# such bound.
_BADGE_SPAN = 2.5


def _badge_regions(page) -> list["fitz.Rect"]:
    """The numbered discs on the page: the numeral and the mark it sits in.

    `mathguard._is_badge` drops these from the text the pipeline translates —
    the "1" in the grey circle is artwork introducing a problem, not part of the
    sentence beside it. Reassembly therefore never sees them as segments, and
    nothing protected them from the page mirror: every problem number on an
    Arabic edition came out written backwards. They are found here by the same
    rule that drops them, so the two cannot drift apart.

    The disc travels with the numeral. Stamping the numeral alone would leave a
    neighbour's stamp free to paint over the disc it sits in, which is what cut
    the circles in half.
    """
    marks = [fitz.Rect(d["rect"]) for d in page.get_drawings() if d.get("fill")]
    out: list[fitz.Rect] = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                probe = Span(text=span["text"], font="", size=0,
                             color=span["color"], bbox=span["bbox"])
                if not span["text"].strip() or not mathguard._is_badge(probe):
                    continue
                rect = fitz.Rect(span["bbox"])
                reach = _BADGE_SPAN * rect.height
                for mark in marks:
                    if (mark.width <= reach and mark.height <= reach
                            and mark.intersects(rect)):
                        rect |= mark
                out.append(rect)
    return out


def _merged(rects: list["fitz.Rect"]) -> list["fitz.Rect"]:
    """Overlapping rects unioned together, until none of them overlap.

    Everything inside one stamp keeps its own left-to-right order, because the
    stamp is lifted and put back as a single picture. Anything split across
    several stamps does not: each lands at its own mirrored position, and their
    order reverses. A stacked fraction arrives as five overlapping fragments —
    numerator, bar, denominator, the parenthesis drawn around them and the
    exponent outside it — so mirroring them one at a time is what turned
    ⟦(6⁴/12⁴)²⟧ into ⟦²6⁴/12⁴)²⁴⟧ on the exponents pages.

    Overlap is the tell, and it is specific: separate lines of text sit beside
    one another, the pieces of one expression sit on top of one another.
    """
    out: list[fitz.Rect] = []
    for rect in rects:
        rect = fitz.Rect(rect)
        absorbing = True
        while absorbing:  # a union can reach rects neither part reached alone
            absorbing = False
            for other in list(out):
                if rect.intersects(other):
                    rect |= other
                    out.remove(other)
                    absorbing = True
        out.append(rect)
    return out


def _mirror_for_rtl(page, replace: list[Segment], page_segs: list[Segment],
                    artwork=()):
    """Turn a redacted LTR page into the RTL edition of itself.

    Runs after redaction and before any target text is drawn, which is what
    makes the whole transform safe: the mirror only ever sees artwork and text
    we are *not* replacing.

    Text we deliberately leave alone — math-font lines, runs no engine
    translated — would be mirrored into unreadable backwards glyphs. Those
    regions are lifted to pixmaps first and stamped back unflipped afterwards,
    so they read correctly even though the page around them has moved.

    `artwork` carries the same protection to marks drawn as vector art rather
    than text — a logo or wordmark, whose region redaction could not clear. A
    mirrored page is meant to move things, not to flip them: the layout is
    reflected, the content inside each protected region is not.

    The problem-number badges are protected too, though no segment carries them
    (see `_badge_regions`), and regions that overlap are stamped as one picture
    rather than one each (see `_merged`).

    Returns the page to carry on with and the segments re-expressed in mirrored
    coordinates.
    """
    width = page.rect.width
    keep = [s for s in page_segs if s not in replace]
    # Artwork last: its region contains the wordmark's own text box, so it must
    # be stamped over the top of it rather than under it.
    regions = _merged([fitz.Rect(s.bbox) for s in keep]
                      + _badge_regions(page)) + [fitz.Rect(r) for r in artwork]
    stamps = [(mirror_bbox(tuple(r), width),
               page.get_pixmap(clip=r, dpi=_MATH_DPI))
              for r in regions if r.get_area() > 0]

    page = mirror_page(page)
    for box, pix in stamps:
        page.insert_image(fitz.Rect(box), pixmap=pix)

    def flip(seg: Segment) -> Segment:
        return replace_dataclass(
            seg,
            bbox=mirror_bbox(seg.bbox, width),
            bboxes=[mirror_bbox(b, width) for b in seg.bboxes],
            math_boxes={t: mirror_bbox(b, width)
                        for t, b in seg.math_boxes.items()},
        )

    flipped = {s.id: flip(s) for s in page_segs}
    return page, [flipped[s.id] for s in replace], list(flipped.values())


def mirror_page(page):
    """Flip everything already drawn on `page` across its vertical centre.

    The whole content stream is wrapped in `q -1 0 0 1 W 0 cm … Q`, so the
    transform covers existing art and is closed again afterwards — anything
    drawn later (our translated text) is unaffected. That ordering is the
    safety property of the RTL path: the mirror only ever sees a page whose
    source text has already been redacted away.

    Wrapping the *whole* stream matters. Pages routinely open with their own
    `q … Q` pair, so slipping the matrix in behind the first `q` would mirror
    only that first group and silently leave the rest of the page alone.

    Returns the page to carry on with — the caller's handle is stale once the
    underlying stream has been rewritten.
    """
    doc = page.parent
    xrefs = page.get_contents()
    if not xrefs:  # nothing drawn yet; a mirror of nothing is nothing
        return page
    head = b"q\n-1 0 0 1 %g 0 cm\n" % page.rect.width
    doc.update_stream(xrefs[0], head + doc.xref_stream(xrefs[0]))
    doc.update_stream(xrefs[-1], doc.xref_stream(xrefs[-1]) + b"\nQ\n")
    return doc.reload_page(page)


_VECTOR_DENSE = 45  # drawings/page above this suggests a diagram, not just table borders


def figure_pages(doc) -> list[int]:
    """Pages carrying a figure, which a mirrored edition may have inverted.

    Broader than `detect_graphic_pages`, deliberately. That one looks for dense
    vector art to guess at diagrams; this one also counts any raster image,
    because mirroring flips artwork content as well as position and a flipped
    number line, coordinate grid or bar chart is not a cosmetic problem — it is
    wrong mathematics. Every page listed here goes to a human.
    """
    dense = {p["page"] for p in detect_graphic_pages(doc)}
    return sorted(
        pno for pno in range(doc.page_count)
        if pno in dense or doc.load_page(pno).get_images()
    )


def detect_graphic_pages(doc) -> list[dict]:
    """Flag pages that likely contain a DIAGRAM (coordinate grid, chart) whose
    labels are drawn as vectors/raster and therefore bypass text translation.

    Heuristic: table borders and a decorative page frame produce a moderate,
    uniform vector count on every page, so raw presence is not a signal. We flag
    pages whose vector-drawing count is an outlier (dense art). Text baked into a
    raster image can only be caught by OCR — noted as a later enhancement."""
    flagged = []
    for pno in range(doc.page_count):
        page = doc.load_page(pno)
        drawings = len(page.get_drawings())
        if drawings >= _VECTOR_DENSE:
            flagged.append({
                "page": pno,
                "vector_drawings": drawings,
                "reason": "dense vector art (likely diagram) — verify no untranslated graphic text",
            })
    return flagged


# --- artwork that redaction cannot remove ------------------------------------
#
# A brand wordmark is usually drawn as vector paths — one filled outline per
# glyph — with an invisible text run over it for search and accessibility. That
# run is a perfectly ordinary translatable segment, but the pixels a reader sees
# belong to the artwork, and the table-safe redaction below
# (PDF_REDACT_LINE_ART_NONE) deliberately leaves line art alone. Measured on a
# real page: redacting the "i-Ready Connect" run changed 0% of its pixels, while
# ordinary body text changed ~100%. Drawing the translation on top of that is
# strictly harmful — it doubles the wordmark — and on an RTL page the untouched
# original is then reflected into backwards glyphs.
#
# So the erase is verified rather than assumed: if redaction did not visibly
# change the region, the glyphs there are artwork and the segment is left alone.

_ERASE_DPI = 100
# Fraction of a box's pixels redaction must actually change for the erase to
# count. Glyphs cover ~10-40% of their own box, so anything at all above noise
# means the text really went; artwork measures a flat zero.
_ERASED = 0.01
_ERASE_DELTA = 16  # gray levels a pixel must move to count as changed
# A drawing covering more of the page than this is furniture — a background
# panel or page border — not part of the mark, and must not drag the whole page
# into the protected region.
_ARTWORK_SHARE = 0.25
# Gray levels a pixel must move for the erase to have taken a GLYPH away, as
# opposed to having resampled the edge of a drawing that happens to cross the
# box. Measured over a real banner: lifting white type off a magenta panel moves
# its pixels about 150 levels, while the arrow edge beside it never moves more
# than 26. `_ERASE_DELTA` sits below that noise on purpose — it only has to see
# that *something* happened — but a per-column reading has to tell the two
# apart.
_INK_DELTA = 48
# Share of a column's pixels that must move that far before the column counts as
# having carried visible source ink.
_INK_SHARE = 0.08
# Points a box has to lose before clipping it is worth doing. A line box carries
# a point or two of side bearing past its last glyph, and reshaping ordinary
# text for that would shrink the whole document.
_MIN_CLIP = 4.0
# A box clipped below this share of its width is not a headline with a covered
# tail, it is a measurement that went wrong; leave it as it was.
_MIN_VISIBLE = 0.35


def _page_gray(page):
    """One grayscale render of the whole page, shared by every segment on it.

    Clipping `get_pixmap` per segment re-runs the page's display list each time,
    which on a busy page is a few hundred renders to answer a question about a
    few thousand pixels. Rendering once and reading sub-rectangles out of it is
    the same measurement for a fraction of the work.
    """
    return page.get_pixmap(dpi=_ERASE_DPI, colorspace=fitz.csGRAY)


def _gray(pix, rect: "fitz.Rect", page_rect: "fitz.Rect") -> bytes:
    """The pixels of `rect`, read out of a full-page render."""
    if page_rect.width <= 0 or page_rect.height <= 0:
        return b""
    sx, sy = pix.width / page_rect.width, pix.height / page_rect.height
    x0, x1 = max(0, int(rect.x0 * sx)), min(pix.width, int(rect.x1 * sx) + 1)
    y0, y1 = max(0, int(rect.y0 * sy)), min(pix.height, int(rect.y1 * sy) + 1)
    if x1 <= x0 or y1 <= y0:
        return b""
    samples, stride = pix.samples, pix.stride
    return b"".join(samples[y * stride + x0:y * stride + x1]
                    for y in range(y0, y1))


def _erased_fraction(before: bytes, after: bytes) -> float:
    """How much of a region redaction actually changed."""
    if not before or len(before) != len(after):
        return 1.0  # unmeasurable: assume the erase worked, as before
    changed = sum(1 for a, b in zip(before, after) if abs(a - b) > _ERASE_DELTA)
    return changed / len(before)


def _artwork_rect(page, rect: "fitz.Rect") -> "fitz.Rect":
    """Grow a box to the extent of the artwork it belongs to.

    A wordmark is a run of separate filled paths — one per glyph — usually with
    an icon and a panel behind them. Protecting only the text's own box would
    leave the icon beside it reflected, so the box grows to cover every path it
    touches.
    """
    out = fitz.Rect(rect)
    budget = page.rect.get_area() * _ARTWORK_SHARE
    for drawing in page.get_drawings():
        r = fitz.Rect(drawing["rect"])
        if 0 < r.get_area() <= budget and r.intersects(rect):
            out |= r
    return out


def _ink_span(before, after, rect: "fitz.Rect", page_rect: "fitz.Rect"
              ) -> tuple[float, float] | None:
    """The x-range of `rect` where redaction actually took source ink away.

    Redaction lifts this segment's own glyphs and leaves everything else
    standing, so a column the erase changed is a column where the source text
    was *visible*. A column it left alone held nothing a reader ever saw —
    either blank paper, or glyphs that something drawn over them had already
    hidden. Which of the two it is, `_visible_box` decides from the geometry.

    None when the erase changed nothing at all, which the caller already treats
    as artwork rather than text.
    """
    if page_rect.width <= 0 or page_rect.height <= 0:
        return None
    sx, sy = before.width / page_rect.width, before.height / page_rect.height
    x0, x1 = max(0, int(rect.x0 * sx)), min(before.width, int(rect.x1 * sx) + 1)
    y0, y1 = max(0, int(rect.y0 * sy)), min(before.height, int(rect.y1 * sy) + 1)
    if x1 <= x0 or y1 <= y0:
        return None
    b, a, stride = before.samples, after.samples, before.stride
    floor = _INK_SHARE * (y1 - y0)
    inked = [x for x in range(x0, x1)
             if sum(1 for y in range(y0, y1)
                    if abs(b[y * stride + x] - a[y * stride + x]) > _INK_DELTA
                    ) > floor]
    if not inked:
        return None
    return inked[0] / sx, (inked[-1] + 1) / sx


def _obstacles(page) -> list["fitz.Rect"]:
    """Everything left on the page that a line of text can be hidden behind."""
    return ([fitz.Rect(d["rect"]) for d in page.get_drawings()]
            + [fitz.Rect(i["bbox"]) for i in page.get_image_info()])


def _visible_box(seg: Segment, before, after, page_rect, obstacles) -> BBox | None:
    """`seg`'s box narrowed to the part of it the source text was visible in.

    A banner headline is set as one text run — "Math on the Go" — and then a
    "GO!" arrow is painted over its tail, so the page only ever reads "Math on
    the". The run still measures the whole phrase, so the box handed to
    reassembly is a good half-inch wider than the space the design leaves for
    it. Filling that box edge to edge is what put the Arabic headline under the
    arrow on every activity page: English got away with it because the hidden
    part was hidden in the source too, and a translation has no such luck.

    The tell is that the segment's own ink stops before the artwork starts.
    Artwork the text is set *over* — a panel behind a heading, a rule under it —
    has ink running across it and is left alone, because there the whole box
    really is usable.

    A merged block needs one more reading. "Digital Math Tools" over an indented
    "Counters and Connecting Cubes" is one paragraph, and a counters icon stands
    in the indent — inside the union of the rows, though no row is set there. A
    measurement taken across the whole box finds the heading's ink on the icon's
    columns and calls the space usable, so the indent is read row by row
    instead. Only the leading edge: rows are free to end early, which is all
    ragged setting is, so a short row proves nothing about the space past it and
    only the box as a whole can speak for the trailing edge. Rows are not free
    to START late. One that does has been indented, and whatever it was
    indented around is not the translation's to occupy.

    Returns None when nothing covers the box, which is the ordinary case.
    """
    box = fitz.Rect(seg.bbox)
    over = [r for r in obstacles if r.intersects(box)]
    if not over:
        return None
    span = _ink_span(before, after, box, page_rect)
    if span is None:
        return None
    ink0, ink1 = span
    x0 = max([r.x1 for r in over if r.x1 <= ink0] + [box.x0])
    x1 = min([r.x0 for r in over if r.x0 >= ink1] + [box.x1])
    for row, _ in _rows(seg):
        # Artwork the row is indented past: on its line, and ending before its
        # own box begins. That box is where the row's ink starts, so no second
        # pixel reading is needed to know the row was set clear of it.
        x0 = max([r.x1 for r in over
                  if r.y0 < row.y1 and row.y0 < r.y1 and r.x1 <= row.x0] + [x0])
    width = x1 - x0
    if width > box.width - _MIN_CLIP or width < _MIN_VISIBLE * box.width:
        return None
    return (x0, box.y0, x1, box.y1)


def _border_average_color(page, rect: "fitz.Rect", dpi: int = 150) -> int:
    """Average color of a rect's border pixels.

    Used to paint an opaque patch over an `in_image` segment's original
    pixels: PyMuPDF's `apply_redactions()` image modes are not reliable on
    images that carry a soft mask (`has-mask`, common for rounded-corner /
    drop-shadow graphics) — the redaction call reports success but leaves
    the pixels untouched. Painting a same-color rectangle ourselves, before
    drawing the translation, guarantees the original burned-in text is
    covered regardless of whether the redaction actually reached the image.
    """
    pix = page.get_pixmap(clip=rect, dpi=dpi)
    w, h = pix.width, pix.height
    if w < 2 or h < 2 or pix.n < 3:
        return 0xFFFFFF
    stride, n = pix.stride, pix.n
    samples = pix.samples

    def px(x: int, y: int) -> tuple[int, int, int]:
        off = y * stride + x * n
        return samples[off], samples[off + 1], samples[off + 2]

    border = [px(x, 0) for x in range(w)] + [px(x, h - 1) for x in range(w)] \
        + [px(0, y) for y in range(h)] + [px(w - 1, y) for y in range(h)]
    r = int(sum(c[0] for c in border) / len(border))
    g = int(sum(c[1] for c in border) / len(border))
    b = int(sum(c[2] for c in border) / len(border))
    return (r << 16) | (g << 8) | b


def rebuild_pdf(src_pdf: str, segments: list[Segment], out_path: str,
                target_lang: str | None = None) -> list[LineOutcome]:
    lang = languages.get(target_lang)
    if not _font_for(Segment("probe", 0, (0, 0, 1, 1), "", 11, 0, "x"), lang):
        raise ValueError(
            f"no installed font can render {lang.name}; install one of "
            + ", ".join(lang.fonts.get("regular", []))
        )

    outcomes: list[LineOutcome] = []
    by_page: dict[int, list[Segment]] = {}
    for s in segments:
        by_page.setdefault(s.page, []).append(s)

    doc = fitz.open(src_pdf)
    try:
        serif = frozenset(_serif_faces(doc))
        faces = _embedded_faces(doc)
        for pno in range(doc.page_count):
            page = doc.load_page(pno)
            page_segs = by_page.get(pno, [])
            hidden = _hidden_duplicates(page_segs) | _image_shadowed_duplicates(page_segs)
            replace = [s for s in page_segs if s.id not in hidden and _replaceable(s, faces)]
            if lang.direction == "rtl":
                # A line mixing prose with math glyphs is laid out atom by atom,
                # each drawn at a computed x. That bypasses MuPDF's bidi, which
                # only orders a single appended run, and the math glyph has to
                # keep its original face regardless. Approximating the ordering
                # on a mathematics line is exactly the kind of silent corruption
                # this pipeline exists to prevent, so these lines stay in the
                # source language and are flagged for a reviewer instead.
                replace = [s for s in replace if not s.has_math_font]
            collides = _overlapping_math(replace, page_segs)
            replace = [s for s in replace if s.id not in collides]
            casualty_pool = [s for s in page_segs if s.id not in hidden]
            replace = replace + _collateral_casualties(replace, casualty_pool)
            # A fraction has to be lifted off the page before redaction clears it.
            snaps = {
                (x.id, tok): page.get_pixmap(clip=fitz.Rect(box), dpi=_MATH_DPI)
                for x in replace
                for tok, box in x.math_boxes.items()
                if _norm(x.math_fonts.get(tok, "")) not in faces
            }

            # Sampled before any redaction touches the page, so it reflects
            # the real original fill regardless of whether the redaction
            # below can actually reach these pixels (see cover step below).
            image_covers = {
                s.id: _border_average_color(page, fitz.Rect(s.bbox))
                for s in replace if s.in_image
            }

            # Sampled before redaction so the erase can be verified against it.
            # `in_image` segments are excluded: their originals are burned into
            # a raster and are masked by the explicit cover below, not by
            # redaction, so redaction leaving them alone proves nothing.
            probe = [s for s in replace if not s.in_image]
            before_pix = _page_gray(page) if probe else None
            before_erase = {s.id: _gray(before_pix, fitz.Rect(s.bbox), page.rect)
                            for s in probe}

            for s in replace:
                for bb in (s.bboxes or [s.bbox]):
                    # fill=None: erase the glyphs but paint nothing over the
                    # spot. A white fill blanked whatever the text sat on —
                    # shaded table headers came back as white boxes.
                    page.add_redact_annot(fitz.Rect(bb), fill=None)
                if s.bullet_bbox:
                    # Explicit, not incidental: whether the body redaction
                    # above happens to also wipe this glyph depends on MuPDF
                    # internals (see mathguard._is_bullet) — sometimes it
                    # survives untouched, which then double-draws once we add
                    # our own dot. Always erase it ourselves so there is
                    # exactly one bullet afterward, not zero or two.
                    page.add_redact_annot(fitz.Rect(s.bullet_bbox), fill=None)
            if replace:
                # graphics=PDF_REDACT_LINE_ART_NONE: the default deletes any line
                # art the redaction rect touches, which strips table rules and
                # cell borders out from under the text we are replacing.
                page.apply_redactions(graphics=fitz.PDF_REDACT_LINE_ART_NONE)

            # Whatever redaction could not remove is artwork, not text. Leave it
            # untouched and, on a mirrored page, protect the mark it belongs to
            # so the reflection does not run it backwards.
            after_pix = _page_gray(page) if probe else None
            artwork = {
                s.id: _artwork_rect(page, fitz.Rect(s.bbox))
                for s in replace
                if s.id in before_erase
                and _erased_fraction(
                    before_erase[s.id],
                    _gray(after_pix, fitz.Rect(s.bbox), page.rect)) < _ERASED
            }
            if artwork:
                replace = [s for s in replace if s.id not in artwork]
                outcomes.extend(
                    LineOutcome(sid, pno, "skipped_graphic",
                                "glyphs are artwork redaction cannot remove; "
                                "translate at source")
                    for sid in artwork
                )

            # Part of a box can be covered even when the rest of it erased
            # cleanly: the source hid the tail of a headline under a callout.
            # Clip those boxes back to the space the design actually leaves, so
            # fitting spends type size on the obstruction instead of setting the
            # translation underneath it. `in_image` runs keep their full box —
            # the cover patch below is cut to it — and turned type is not laid
            # out along x at all.
            obstacles = _obstacles(page) if before_pix else []
            clipped = {}
            for s in replace:
                if s.in_image or s.rotation or s.id not in before_erase:
                    continue
                box = _visible_box(s, before_pix, after_pix, page.rect, obstacles)
                if box:
                    # Only the union box moves. The source's own rows still say
                    # where each baseline sits and which edge the block was
                    # aligned on, and clipping them would rewrite both.
                    clipped[s.id] = replace_dataclass(s, bbox=box)
            if clipped:
                replace = [clipped.get(s.id, s) for s in replace]
                page_segs = [clipped.get(s.id, s) for s in page_segs]

            if lang.direction == "rtl":
                page, replace, page_segs = _mirror_for_rtl(
                    page, replace, page_segs, artwork.values())
            # Images carrying a soft mask (rounded corners, drop shadows —
            # common on decorative badges/banners) are not reliably cleared
            # by apply_redactions' image modes even though the call reports
            # success. `in_image` segments can't rely on redaction alone, so
            # cover the region ourselves with its own sampled background
            # color before the translation is drawn on top.
            for s in replace:
                if s.in_image:
                    page.draw_rect(fitz.Rect(s.bbox), color=None,
                                   fill=_rgb(image_covers[s.id]), overlay=True)

            room = {x.id: _room_below(x, page_segs, page.rect) for x in replace}
            shared = _fit_page(replace, lang, room, serif)
            shared = _relieve_overlaps(replace, page_segs, lang, room, serif, shared)
            for s in replace:
                outcomes.append(_place(page, s, lang, shared.get(s.id), room[s.id],
                                       serif, faces, snaps))

            for s in page_segs:
                if s in replace:
                    continue
                if s.id in collides:
                    outcomes.append(LineOutcome(s.id, pno, "skipped_math",
                                                "overlaps rendered math; manual finish"))
                elif s.has_math_font and s.is_translatable:
                    outcomes.append(LineOutcome(s.id, pno, "skipped_math",
                                                "contains math; manual finish"))
                elif s.status == "needs_human":
                    outcomes.append(LineOutcome(s.id, pno, "skipped_untranslated",
                                                "; ".join(s.notes)))

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        doc.save(out_path, garbage=4, deflate=True)
    finally:
        doc.close()
    return outcomes


def _adjust_box_for_whitespace(box: fitz.Rect, source: str, font: fitz.Font, size: float):
    """Shrink the box to preserve visual indentation from the source text."""
    leading = len(source) - len(source.lstrip(" "))
    if leading > 0:
        box.x0 = min(box.x0 + font.text_length(" " * leading, size), box.x1 - 10.0)
    trailing = len(source) - len(source.rstrip(" "))
    if trailing > 0:
        box.x1 = max(box.x1 - font.text_length(" " * trailing, size), box.x0 + 10.0)


def _fit_page(page_segs: list[Segment], lang, room: dict[str, float],
              serif: frozenset = frozenset()) -> dict[str, float]:
    """Choose one type size per table column, not per row.

    Fitting each row on its own makes a table look broken: a long translation
    drops to 7pt directly beneath an 11pt neighbour. Rows that share a column
    (same source size, same x-range) are therefore set at the smallest size any
    of them needs, so the column reads as one block.

    A single pathological row must not shrink its whole column, so the shared
    size is floored at `_COLUMN_FLOOR` of the column's natural size; anything
    needing less than that keeps its own smaller size and is reported.
    """
    fitted: dict[str, float] = {}
    groups: dict[tuple, list[str]] = {}

    for seg in page_segs:
        text = " ".join(seg.restored_target().split())
        if not text:
            continue
        font = _font(_font_for(seg, lang, text, serif))
        box = fitz.Rect(seg.bbox)
        rows = _rows(seg)
        limit_y = room.get(seg.id, box.y1)
        size, _, _ = _fit_lines(text, font, box.width, len(rows),
                                seg.size or 11.0, lang.wrapping,
                                _extra_lines(seg, font, limit_y),
                                vspace=limit_y - rows[0][0].y0)
        fitted[seg.id] = size
        key = (round(seg.size or 11.0, 1), round(box.x0 / 25), round(box.width / 25))
        groups.setdefault(key, []).append(seg.id)

    shared: dict[str, float] = {}
    for (natural, _, _), ids in groups.items():
        if len(ids) < 2:
            continue
        floor = natural * _COLUMN_FLOOR
        common = max(min(fitted[i] for i in ids), floor)
        for i in ids:
            shared[i] = min(common, fitted[i])
    return shared


# Points of type size a colliding block may give up before we stop trying. Two
# is enough to clear the interleaving cases and small enough that the block still
# reads as part of its column.
_OVERLAP_TRIM = 2


def _block_extent(seg: Segment, lang, size_hint, limit_y, serif):
    """Top and bottom of the ink this segment will actually put on the page.

    Sizes and lays the block out exactly as `_place` will, then reports the
    extent rather than drawing it.
    """
    text, _ = _split_bold(" ".join(seg.restored_target().split()))
    if not text:
        return None
    font = _font(_font_for(seg, lang, text, serif))
    box = fitz.Rect(seg.bbox)
    rows = _rows(seg)
    size, lines, _ = _fit_lines(text, font, box.width, len(rows),
                                size_hint or seg.size or 11.0, lang.wrapping,
                                _extra_lines(seg, font, limit_y),
                                vspace=limit_y - rows[0][0].y0)
    ys = _baselines(rows, box, len(lines), size, font, limit_y)
    return (ys[0] - size * font.ascender, ys[-1] - size * font.descender)


def _relieve_overlaps(replace: list[Segment], page_segs: list[Segment], lang,
                      room: dict[str, float], serif, shared: dict[str, float]
                      ) -> dict[str, float]:
    """Give back type size where two blocks would still land on each other.

    `_room_below` only counts a segment as "below" this one if it starts past
    this one's bottom. A bullet and its run-on line routinely overlap by a point
    or two in the source, so each reports no ceiling at all and both get set at
    full size — which Latin absorbs and Arabic, needing half again the height,
    does not. Rather than redefine what "below" means, the blocks that actually
    collide are measured after fitting and handed back a point of size until they
    clear, at most `_OVERLAP_TRIM`.

    Text burned into an image is never shrunk: its size belongs to the artwork it
    sits on, and shrinking it would leave the translation adrift inside a cover
    patch cut for the original. A colliding neighbour gives way instead.
    """
    sizes = dict(shared)
    movable = {s.id for s in replace
               if not s.in_image and not s.rotation and not s.has_math_font}
    if not movable:
        return sizes
    # Segments we are not replacing keep their original ink exactly where it is.
    fixed = {s.id: (s.bbox[1], s.bbox[3]) for s in page_segs if s not in replace}

    for _ in range(_OVERLAP_TRIM):
        extents = dict(fixed)
        for s in replace:
            extent = _block_extent(s, lang, sizes.get(s.id), room[s.id], serif)
            if extent:
                extents[s.id] = extent
        boxes = {s.id: s.bbox for s in page_segs}

        clashing: set[str] = set()
        for a in page_segs:
            for b in page_segs:
                if a.id >= b.id or a.id not in extents or b.id not in extents:
                    continue
                if boxes[a.id][2] <= boxes[b.id][0] or boxes[b.id][2] <= boxes[a.id][0]:
                    continue  # a different column
                (top_a, bot_a), (top_b, bot_b) = extents[a.id], extents[b.id]
                if bot_a <= top_b or bot_b <= top_a:
                    continue  # clear of one another
                clashing.update((a.id, b.id))

        trim = clashing & movable
        if not trim:
            break
        for sid in trim:
            seg = next(s for s in replace if s.id == sid)
            natural = sizes.get(sid) or seg.size or 11.0
            sizes[sid] = max(_MIN_SIZE, natural - 1.0)
    return sizes


def _place(page, seg: Segment, lang, size_hint: float | None = None,
           limit_y: float | None = None, serif: frozenset = frozenset(),
           faces: dict[str, bytes] | None = None, snaps: dict | None = None
           ) -> LineOutcome:
    """Set the target on the source's own baselines, in the source's line count.

    Editorial contract: English that occupied N visual lines comes back as N
    lines. We wrap with real font metrics and shrink the size until that holds,
    then draw line i on the baseline of source row i — so the block keeps the
    exact footprint it had and can never run into the block below it.

    `size_hint` is the shared size agreed for this segment's table column.
    """
    if seg.rotation:
        return _place_rotated(page, seg, lang, size_hint, serif)
    if seg.has_math_font and _math_drawable(seg, faces or {}):
        return _place_with_math(page, seg, lang, size_hint, limit_y, serif,
                                faces or {}, snaps or {})

    raw_text = " ".join(seg.restored_target().split())
    if not raw_text:
        return LineOutcome(seg.id, seg.page, "replaced", "empty")
    text, bold_words = _split_bold(raw_text)
    if not text:
        return LineOutcome(seg.id, seg.page, "replaced", "empty")

    font_path = _font_for(seg, lang, text, serif)
    font = _font(font_path)
    # Done here, not earlier: whether a character is drawable is a property of
    # the face that was just chosen, not of the text.
    text = _drawable(text, font)
    bold_font_path, bold_font = font_path, font
    if any(bold_words):
        # Skip the source-font lookup for the bold face: `seg.font` names the
        # segment's own (regular-weight) family, and matching it by name would
        # just hand back the same regular font for both weights.
        bp = _font_for(replace(seg, bold=True), lang, "", serif)
        if bp:
            bold_font_path, bold_font = bp, _font(bp)

    box = fitz.Rect(seg.bbox)
    _adjust_box_for_whitespace(box, seg.source, font, size_hint or seg.size or 11.0)
    
    rows = _rows(seg)
    max_lines = len(rows)

    if limit_y is None:
        limit_y = box.y1
    size, lines, overflow = _fit_lines(text, font, box.width, max_lines,
                                       size_hint or seg.size or 11.0, lang.wrapping,
                                       _extra_lines(seg, font, limit_y),
                                       vspace=limit_y - rows[0][0].y0)
    baselines = _baselines(rows, box, len(lines), size, font, limit_y)

    kwargs = dict(fontsize=size, color=_rgb(seg.color))
    if font_path:
        kwargs.update(fontname=_alias(font_path), fontfile=font_path)
    else:
        kwargs.update(fontname="helv")

    bold_kwargs = dict(kwargs)
    if bold_font_path:
        bold_kwargs.update(fontname=_alias(bold_font_path), fontfile=bold_font_path)
    if seg.accent_color is not None:
        bold_kwargs["color"] = _rgb(seg.accent_color)

    align = _alignment(rows)
    rtl = lang.direction == "rtl"
    if rtl:
        # A block set against the left margin in English is set against the
        # right one in Arabic: the aligned edge is the margin, not the side.
        align = {"left": "right", "right": "left"}.get(align, align)

    word_i = 0
    for i, (line, y) in enumerate(zip(lines, baselines)):
        if rtl:
            # One append per line, never per word: MuPDF resolves bidi ordering
            # across the whole run, so splitting it would strand digits and
            # punctuation on the wrong side of the words they belong to. The
            # cost is that inline bold applies to the whole line — see
            # _draw_rtl.
            n = len(line.split())
            face = bold_font_path if any(bold_words[word_i:word_i + n]) else font_path
            _draw_rtl(page, line, _align_x(line, font, size, box, align), y,
                      face, size, _rgb(seg.color))
            word_i += n
            continue
        parts = _leader_parts(line, font, size, box) if i == len(lines) - 1 else None
        if parts and len(parts) > 1:  # a dot leader owns this line's geometry
            for x, part in parts:
                page.insert_text(fitz.Point(x, y), part, **kwargs)
            continue
        words = line.split()
        line_bold = bold_words[word_i:word_i + len(words)]
        if not any(line_bold):
            page.insert_text(fitz.Point(_align_x(line, font, size, box, align), y), **kwargs,
                             text=line)
        else:
            x = _align_x(line, font, size, box, align)
            space_w = font.text_length(" ", size)
            accent_size = size * seg.accent_size_ratio if seg.accent_size_ratio else size
            for word, is_bold in zip(words, line_bold):
                wfont = bold_font if is_bold else font
                word_size = accent_size if is_bold else size
                wkwargs = dict(bold_kwargs if is_bold else kwargs, fontsize=word_size)
                page.insert_text(fitz.Point(x, y), word, **wkwargs)
                x += wfont.text_length(word, word_size) + space_w
        word_i += len(words)

    if seg.bullet_color is not None and not rtl:
        # Drawn explicitly rather than left untouched on the page: MuPDF's
        # apply_redactions can erase this glyph as a side effect of redacting
        # a nearby segment sharing the same content-stream text object, even
        # though the bullet's own bbox was excluded from every redaction rect
        # (mathguard._is_bullet) — the bullet's own bbox is force-erased above
        # for exactly this reason, so there is always exactly one to draw.
        #
        # A design commonly sets its bullet glyph at a much larger point size
        # than the body text purely to get a normal-looking dot out of a font
        # whose "•" has tiny ink relative to its em box (30pt bullet next to
        # 12pt body measured at only ~6.3pt actual ink diameter — the point
        # size ratio wildly overstates the visible mark). Scaling the radius
        # by that raw ratio overshoots badly, so this uses a fraction of the
        # render size instead, calibrated against a measured source bullet.
        radius = size * 0.26
        cx = box.x0 - size * 0.35 - radius
        cy = baselines[0] - size * 0.32
        color = _rgb(seg.bullet_color)
        page.draw_circle(fitz.Point(cx, cy), radius, color=color, fill=color)

    if overflow:
        return LineOutcome(
            seg.id, seg.page, "overflow",
            f"needs {len(lines)} lines vs {max_lines} at min size {_MIN_SIZE}; compressed",
        )
    return LineOutcome(seg.id, seg.page, "replaced",
                       f"size={size:.2f} lines={len(lines)}/{max_lines}")


def _draw_rtl(page, text: str, x: float, y: float, font_path: str | None,
              size: float, color: tuple[float, float, float],
              rotate: int = 0) -> None:
    """Draw one right-to-left line, starting at `x` on baseline `y`.

    `page.insert_text` cannot set this text. It applies no bidi reordering, so
    an embedded number run comes out on the wrong side of its sentence, and it
    performs no glyph fallback — digits set in Noto Sans Hebrew, which carries
    none, are written as NUL. `TextWriter` does both: MuPDF runs the bidi
    algorithm over the whole appended run and falls back to another face for
    any glyph the chosen one lacks.

    `x` is still the left edge; `right_to_left` reorders the glyphs within the
    run rather than changing where it starts, so the existing alignment maths
    needs no special case.
    """
    writer = fitz.TextWriter(page.rect)
    writer.append(fitz.Point(x, y), text, font=_font(font_path),
                  fontsize=size, right_to_left=1)
    # TextWriter has no `rotate`; turned type is written flat and then spun
    # about its own start point, which is where insert_text's rotate pivots too.
    morph = (fitz.Point(x, y), fitz.Matrix(rotate)) if rotate else None
    writer.write_text(page, color=color, morph=morph)


def _alignment(rows) -> str:
    """Infer the block's alignment from how its source lines line up.

    A ragged display phrase is set flush right or centred; redrawing it flush
    left keeps the words but loses the shape. Which edge is the deliberate one
    is decided by comparing how much each edge varies: the aligned edge is the
    steady one. A single line carries no such evidence, so it stays as it was.
    """
    if len(rows) < 2:
        return "left"
    lefts = [r.x0 for r, _ in rows]
    rights = [r.x1 for r, _ in rows]
    centres = [(r.x0 + r.x1) / 2 for r, _ in rows]
    width = max(rights) - min(lefts)
    left_spread = max(lefts) - min(lefts)
    right_spread = max(rights) - min(rights)
    centre_spread = max(centres) - min(centres)
    steady = 0.1 * width

    if right_spread < steady and right_spread * 2 < left_spread:
        return "right"
    if centre_spread < steady and centre_spread * 2 < min(left_spread, right_spread):
        return "center"
    return "left"


def _align_x(line: str, font: fitz.Font, size: float, box: fitz.Rect, align: str) -> float:
    if align == "right":
        return box.x1 - font.text_length(line, size)
    if align == "center":
        return box.x0 + (box.width - font.text_length(line, size)) / 2
    return box.x0


_LEADER = re.compile(r"^(.*?[^.\s])[.…]{2,}\s*(\d[\d\-–]*)?\s*$")


def _leader_parts(line: str, font: fitz.Font, size: float, box: fitz.Rect
                  ) -> list[tuple[float, str]]:
    """Split a table-of-contents line into (x, text) runs to draw.

    A row like "7 Multiplicar … científica......... 10" is a left-aligned title,
    a right-aligned page number, and dots bridging the two. Flowing it as one
    string leaves the number stranded mid-column and the leader at whatever
    length the translation happened to produce, so the number is set against the
    column's right edge and the dots are regenerated to reach it. When the page
    number is its own table cell the leader still gets rebuilt to fill the cell,
    which is what keeps the dotted column straight. Lines without that shape are
    drawn unchanged.
    """
    m = _LEADER.match(line)
    if not m:
        return [(box.x0, line)]

    head, number = m.group(1), m.group(2) or ""
    head_w = font.text_length(head + " ", size)
    num_w = font.text_length(" " + number, size) if number else 0.0
    gap = box.width - head_w - num_w
    dot_w = font.text_length(".", size)
    if gap < dot_w * 2:  # no room for a leader — keep it as one flowed line
        return [(box.x0, line)]

    parts = [(box.x0, head + " " + "." * int(gap / dot_w))]
    if number:
        parts.append((box.x1 - font.text_length(number, size), number))
    return parts


def _place_rotated(page, seg: Segment, lang, size_hint, serif) -> LineOutcome:
    """Set a vertical run — a graph's axis label — along its own axis.

    The source sets these turned 90°, so the text runs down the tall side of a
    narrow box. Setting them horizontally leaves only a few characters of room
    per line and breaks the label into stacked fragments; the length available
    is the box's HEIGHT, and the type is drawn turned to match.
    """
    text = " ".join(seg.restored_target().split())
    if not text:
        return LineOutcome(seg.id, seg.page, "replaced", "empty")

    font_path = _font_for(seg, lang, text, serif)
    font = _font(font_path)
    text = _drawable(text, font)
    box = fitz.Rect(seg.bbox)
    
    # We do not adjust whitespace for rotated text since trailing/leading spaces
    # usually pad the height, not width, and spacing is less rigid.
    
    size, lines, overflow = _fit_lines(text, font, box.height, len(_rows(seg)),
                                       size_hint or seg.size or 11.0, lang.wrapping)

    kwargs = dict(fontsize=size, color=_rgb(seg.color), rotate=seg.rotation)
    if font_path:
        kwargs.update(fontname=_alias(font_path), fontfile=font_path)
    else:
        kwargs.update(fontname="helv")

    # The baseline of turned type runs parallel to the long side of the box; its
    # offset is measured across the short side, exactly as for upright text.
    pitch = size * (font.ascender - font.descender)
    for i, line in enumerate(lines):
        offset = box.width * _BASE_RATIO + i * pitch
        if seg.rotation == 90:
            start = fitz.Point(box.x0 + offset, box.y1)
        else:
            start = fitz.Point(box.x1 - offset, box.y0)
        if lang.direction == "rtl":
            _draw_rtl(page, line, start.x, start.y, font_path, size,
                      _rgb(seg.color), rotate=seg.rotation)
        else:
            page.insert_text(start, line, **kwargs)

    if overflow:
        return LineOutcome(seg.id, seg.page, "overflow",
                           f"rotated label did not fit at min size {_MIN_SIZE}")
    return LineOutcome(seg.id, seg.page, "replaced",
                       f"size={size:.2f} rotated={seg.rotation}")


def _place_with_math(page, seg: Segment, lang, size_hint, limit_y, serif,
                     faces: dict[str, bytes], snaps: dict) -> LineOutcome:
    """Set a line that mixes prose with math glyphs.

    The prose is translated and drawn in the target font; each math glyph is
    drawn as its ORIGINAL character code in the document's ORIGINAL face, which
    is the only faithful way to reproduce a symbol whose character identity the
    PDF does not record. That lets these lines be translated instead of being
    left in the source language to protect the equation.
    """
    atoms = _atoms(seg)
    if not atoms:
        return LineOutcome(seg.id, seg.page, "replaced", "empty")

    prose = " ".join(p for word in atoms for p, is_math in word if not is_math)
    font_path = _font_for(seg, lang, prose, serif)
    font = _font(font_path)
    box = fitz.Rect(seg.bbox)
    _adjust_box_for_whitespace(box, seg.source, font, size_hint or seg.size or 11.0)
    
    rows = _rows(seg)
    max_lines = len(rows)

    size = max(float(size_hint or seg.size or 11.0), _MIN_SIZE)
    lines = None
    while size > _MIN_SIZE:
        wrapped = _wrap_atoms(atoms, seg, font, size, box.width)
        if wrapped is not None and len(wrapped) <= max_lines:
            lines = wrapped
            break
        size -= 0.25
    overflow = lines is None
    if lines is None:
        size = _MIN_SIZE
        lines = _wrap_atoms(atoms, seg, font, size, box.width) or [atoms]

    if limit_y is None:
        limit_y = box.y1
    baselines = _baselines(rows, box, len(lines), size, font, limit_y)

    text_kw = dict(fontsize=size, color=_rgb(seg.color))
    if font_path:
        text_kw.update(fontname=_alias(font_path), fontfile=font_path)
    else:
        text_kw.update(fontname="helv")
    space = font.text_length(" ", size)

    for line, y in zip(lines, baselines):
        x = box.x0
        for i, word in enumerate(line):
            if i:
                x += space
            for piece, is_math in word:
                if is_math and (seg.id, piece) in snaps:
                    # A stacked fraction: replayed as the pixels it was, scaled
                    # to the size the surrounding prose ended up at.
                    pix = snaps[(seg.id, piece)]
                    w = seg.math_widths[piece] * size
                    h = w * pix.height / pix.width if pix.width else size
                    page.insert_image(fitz.Rect(x, y - h * 0.74, x + w, y + h * 0.26),
                                      pixmap=pix)
                elif is_math:
                    buf = faces[_norm(seg.math_fonts[piece])]
                    name = "m" + hashlib.md5(buf).hexdigest()[:10]
                    page.insert_font(fontname=name, fontbuffer=buf)
                    page.insert_text(fitz.Point(x, y), seg.placeholders[piece],
                                     fontname=name, fontsize=size, color=_rgb(seg.color))
                    w = seg.math_widths[piece] * size
                else:
                    page.insert_text(fitz.Point(x, y), piece, **text_kw)
                    w = font.text_length(piece, size)
                x += w

    if overflow:
        return LineOutcome(seg.id, seg.page, "overflow",
                           f"math line did not fit at min size {_MIN_SIZE}")
    return LineOutcome(seg.id, seg.page, "replaced",
                       f"size={size:.2f} lines={len(lines)}/{max_lines} +math")


def _room_below(seg: Segment, page_segs: list[Segment], page_rect) -> float:
    """First y below the segment that is already occupied — its reflow ceiling."""
    bottom = fitz.Rect(seg.bbox).y1
    limit = page_rect.y1 - _PAGE_MARGIN
    for other in page_segs:
        if other is seg:
            continue
        r = fitz.Rect(other.bbox)
        if r.y0 < bottom - 0.5:  # not below us
            continue
        if r.x1 <= seg.bbox[0] or r.x0 >= seg.bbox[2]:  # a different column
            continue
        limit = min(limit, r.y0 - 1.0)
    return max(limit, bottom)


def _extra_lines(seg: Segment, font: fitz.Font, limit_y: float) -> int:
    """How many further lines fit in the empty space under this block."""
    rows = _rows(seg)
    pitch = (seg.size or 11.0) * (font.ascender - font.descender)
    if pitch <= 0:
        return 0
    return int(max(0.0, limit_y - rows[-1][0].y1) // pitch)


def _rows(seg: Segment) -> list[tuple[fitz.Rect, float]]:
    """The segment's VISUAL lines as (rect, baseline y), top to bottom.

    `seg.bboxes` is a fragment list, not a line list: PyMuPDF splits a
    tab-separated row (a table cell, a TOC entry "12 | Understanding … | 18")
    into several "lines" that sit side by side on the same baseline. Counting
    those as lines stacks the text on top of itself.

    Fragments are grouped by BASELINE (box bottom) rather than by box overlap: a
    vertically centred cell next to a two-line title overlaps both of its lines,
    so overlap-chaining merges rows that are visually distinct. That same centred
    cell also sits higher than its row, so the row's baseline is taken from its
    WIDEST fragment — the one actually carrying the text — rather than from the
    merged rect, which the centred cell would drag upwards.

    The baseline itself is the one the source recorded, where there is one.
    Deriving it from the box instead put a bulleted line several points too low:
    its "•" is set at twice the type size, so the box is half as tall again as
    the text sitting in it. Fragments with no recorded baseline — OCR reports a
    box and nothing else — still fall back to `_BASE_RATIO`.
    """
    boxes = list(seg.bboxes or [seg.bbox])
    known = seg.baselines if len(seg.baselines) == len(boxes) else []
    pairs = sorted(
        ((fitz.Rect(b), known[i] if known else None) for i, b in enumerate(boxes)),
        key=lambda p: (p[0].y1, p[0].x0),
    )
    tol = 0.6 * min((r.height for r, _ in pairs), default=1.0)
    groups: list[list[tuple[fitz.Rect, float | None]]] = []
    anchor = None
    for pair in pairs:
        if anchor is not None and pair[0].y1 - anchor <= tol:
            groups[-1].append(pair)
        else:
            groups.append([pair])
            anchor = pair[0].y1
    if not groups:
        groups = [[(fitz.Rect(seg.bbox), None)]]

    rows = []
    for members in groups:
        rect = fitz.Rect(members[0][0])
        for m, _ in members[1:]:
            rect |= m
        main, baseline = max(members, key=lambda m: m[0].width)
        if baseline is None:
            baseline = main.y0 + main.height * _BASE_RATIO
        rows.append((rect, baseline))
    return rows


@lru_cache(maxsize=8)
def _font(path: str | None) -> fitz.Font:
    """Metrics for the face we actually draw with, so wrapping matches output."""
    return fitz.Font(fontfile=path) if path else fitz.Font("helv")


def _wrap(text: str, font: fitz.Font, size: float, width: float,
          hard: bool = False, wrapping: str = "space") -> list[str]:
    """Greedy wrap at `width`.

    A word wider than the column is left whole (the caller shrinks the size until
    it fits) unless `hard`, the last-resort pass, which breaks mid-word. Breaking
    "Estudiantes" into "Estudia/ntes" is worse than a point of extra shrink.

    Chinese and Japanese have no word spaces — `wrapping="char"` breaks between
    characters instead, which is how those scripts actually line-break.
    """
    if wrapping == "char":
        return _wrap_chars(text, font, size, width)

    lines: list[str] = []
    cur = ""
    for word in text.split():
        trial = f"{cur} {word}" if cur else word
        if cur and font.text_length(trial, size) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
        while hard and len(cur) > 1 and font.text_length(cur, size) > width:
            cut = len(cur)
            while cut > 1 and font.text_length(cur[:cut], size) > width:
                cut -= 1
            lines.append(cur[:cut])
            cur = cur[cut:]
    if cur:
        lines.append(cur)
    return lines or [""]


_NO_LINE_START = "。、，．！？：；）」』】》%"  # never begin a line with these


def _wrap_chars(text: str, font: fitz.Font, size: float, width: float) -> list[str]:
    """Character-level wrap for CJK, keeping closing punctuation off line starts."""
    lines: list[str] = []
    cur = ""
    for ch in text:
        if cur and font.text_length(cur + ch, size) > width and ch not in _NO_LINE_START:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines or [""]


def _fit_lines(text, font, width, max_lines, start, wrapping="space", extra=0,
               vspace: float | None = None) -> tuple[float, list[str], bool]:
    """Set the text in the source's own line count, at the largest size that fits.

    The line count is the hard constraint: text set on three lines in the source
    comes back on three lines, never five. Type size is what gives way when the
    translation runs longer, since a block that grows extra lines changes the
    shape of the page — and, worse, risks colliding with whatever sits below it.
    (`extra`/`_room_below` looked like a safe way to spend real whitespace
    instead of shrinking, but on a page with several short stacked segments —
    a bulleted list — the "room" one segment sees below it is frequently
    space another segment is about to grow into too, or space a segment with
    a narrower box was wrongly skipped past as "different column". The result
    was overlapping, unreadable text — worse than the small font it was meant
    to avoid. `extra` is accepted for call compatibility and ignored.)

    A line is only accepted if every word fits the column at that size, so an
    over-long word shrinks the block instead of being split mid-word.

    `vspace` is the vertical room the block may occupy — from the top of its
    first source row down to the first thing below it (`_room_below`). Fitting
    on width alone was safe only while every target face had roughly the source
    face's proportions: Noto Naskh occupies 1.70 em per line against Arial's
    1.12, so Arabic set at the source's own size overran the line beneath it by
    about half a line every time. Height is a real constraint, not a free one,
    so it is spent the same way width is.
    """
    start = max(float(start), _MIN_SIZE)
    line_height = font.ascender - font.descender

    def attempt(size: float, budget: int) -> list[str] | None:
        lines = _wrap(text, font, size, width, wrapping=wrapping)
        if len(lines) > budget:
            return None
        if any(font.text_length(ln, size) > width for ln in lines):
            return None  # an unbreakable word still overhangs the column
        if vspace is not None and len(lines) * size * line_height > vspace:
            return None  # the block is taller than the room under it
        return lines

    lines = attempt(start, max_lines)
    if lines:
        return start, lines, False

    size = start - 0.25
    while size > _MIN_SIZE:
        lines = attempt(size, max_lines)
        if lines:
            return size, lines, False
        size -= 0.25

    lines = _wrap(text, font, _MIN_SIZE, width, hard=True, wrapping=wrapping)
    return _MIN_SIZE, lines, len(lines) > max_lines


def _baselines(rows, box, count, size, font, limit_y) -> list[float]:
    """Baseline y for each output line, never crossing `limit_y`.

    Reusing the source rows' own baselines puts the translation exactly where the
    English sat. Lines beyond the source's own rows continue at natural leading
    into the empty space below, and are compressed into the block's own box only
    if even that space is too tight — so a block can never reach its neighbour.
    """
    ys = [baseline for _, baseline in rows[:count]]
    pitch = size * (font.ascender - font.descender)
    while len(ys) < count:
        ys.append(ys[-1] + pitch)

    # The source's leading was chosen for the source's face. A target face that
    # needs more room than that would be set on baselines too close together and
    # collide with itself, so a block whose source rows are tighter than the
    # target's own leading is re-led from its first baseline instead. `_fit_lines`
    # has already sized the block to fit the room below, and the compression
    # fallback underneath still applies, so this can never reach the next block.
    gaps = [b - a for a, b in zip(ys, ys[1:])]
    if gaps and min(gaps) < pitch:
        ys = [ys[0] + pitch * i for i in range(count)]

    if ys[-1] - size * font.descender > limit_y:
        step = max((limit_y - box.y0) / count, size)
        ys = [box.y0 + step * i + step * _BASE_RATIO for i in range(count)]
    return ys
