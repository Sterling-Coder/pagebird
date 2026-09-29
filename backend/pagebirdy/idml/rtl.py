"""RTL layout for the IDML path: text direction, and selectively adapted geometry.

:func:`apply_rtl` is the one call the pipeline makes for an RTL target. Reading
direction changes for every story and paragraph via :func:`set_text_direction`
(flipping the typographic properties that travel with reading direction --
alignment, indents, a paragraph's shading/border box, table column order, and a
directional bullet glyph -- an arrow or pointer -- substituted for its mirror
image so it still points into the text once that text reads the other way) and
:func:`preserve_ltr_content` (pinning runs that must keep reading left-to-right
-- an equation, a URL, a file name -- inside a paragraph that otherwise flows
right to left). Object geometry then goes through the rule table in
`idml.rtl_plan`/`idml.rtl_rules` (:func:`apply_plan`, below), the same for
every RTL target: the page template -- master items, the lesson badge, the
vertical lesson title, bleed art on a master -- stays where it is, and every
piece of the page's content mirrors within its page. See `idml.rtl_rules`'s
own module docstring for the rule list.

Two narrower passes follow those two. :func:`mirror_anchored_object_settings`
flips an inline badge's own text-relative anchor (``AnchorXoffset``,
``HorizontalAlignment``, ``AnchorPoint``) so a callout number pinned to the
corner where its sentence opened still sits at the corner where the same
sentence opens once it reads the other way -- otherwise the badge is left
introducing the end of its line rather than the start. `idml.rtl_subparts`
follows: a group of sibling sub-part labels (``a.``, ``b.``, ``c.``, ...)
shares one left edge in the English source but, once mirrored to right-aligned
text, each hugs its own frame's own right edge instead, which is rarely the
same point twice. It gives the group back one shared start edge the same way
-- a paragraph's own ``RightIndent``, never a frame's position or size. Once
the frames themselves mirror, labels that shared a left edge share a right
edge and there is usually nothing left for it to correct.

**The geometry engine mirrors content, not the page.** `idml.rtl_plan`,
`idml.rtl_components` and `idml.rtl_rules` classify every object and
:func:`apply_plan` carries the classification out. Mirroring only some content
is what breaks a page -- a picture reflected onto a paragraph that stayed where
English left it -- so everything that is not template furniture is reflected
about one axis per page, which keeps every distance between those pieces and
cannot make them overlap. That axis is the page's centre unless fixed furniture
runs down one side (the blue strip carrying the badge and vertical title); then
content mirrors within the area the strip leaves (:func:`content_axes`). A
group's own children mirror with it, a styled equation crosses the page as one
rigid unit, and nothing nested inside a moving item moves on its own account.
Checked against the human Arabic references in `backend/Reference/`. The
whole-page mirror in `idml.rtl_legacy` still exists, unused, kept only for
calibration reference.

**One kind of content is turned round on purpose.** The human-translated Arabic
references mirror a *photograph* with the page -- the sprinters on the Lesson 12
family letter run leftwards in Arabic and rightwards in English -- and never
mirror the vector art beside it, because a coordinate plane's x-axis and a
badge's glyph mean what they mean only one way round. :func:`reflect_graphic`
takes that line where IDML already draws it, between a raster ``<Image>`` and
placed ``<PDF>``/``<EPS>``/``<WMF>`` art, and turns the picture round *inside*
its frame -- reflecting the frame's outline, its wrap contour and its children's
transforms about the frame's own centre, so the frame's own ``a b c d`` still go
untouched and its bounds still land where the ``tx`` mirror computed. Leaving a
clipped photograph alone is not neutral: its wrap contour was cut round a
subject facing the other way, so it takes the wrong bite out of every line of
type beside it.

**Content stays on its own page.** A band drawn past its page's outer trim --
bleed, or a frame dragged long -- carries that overhang with it when its box is
reflected, and on a facing-page spread the other side of the page is the
spine. The target keeps the source's left-to-right binding
(`set_text_direction` never touches `PageBinding`, and `idml.validate` rejects
a change to it), so the spine stays the spine and the overhang would print on
the facing page: the Understand question bar on RCM07 L03 page 49 did exactly
that. Every move is therefore held by :func:`keep_on_page` to its owning page
on each side where another page sits -- a shift, never a trim, so the item
keeps its size and shows the width of its old bleed on the page instead. An
outer trim has no page beyond it and still takes the overhang; a single-page
spread holds nothing back. A component is held as one piece.

**Position is not the only thing that names a side.** Moving a frame's ``tx``
leaves untouched every property whose *meaning* is an edge rather than a
coordinate, and a page with those still pointing the old way reads as half
mirrored. :func:`mirror_item_properties` flips the ones that travel with the
geometry -- a wrap contour biased to one side (``TextWrapSide``), a wrap or
frame inset wider on one edge (``TextWrapOffset``, a four-part
``InsetSpacing``), and an inline object offset sideways from its anchor
(``AnchorXoffset``, ``HorizontalAlignment``, ``AnchorPoint``). It reads
``Resources/`` as well as the stories and spreads, because an object style is
where most frames get all three from. :func:`set_text_direction` flips the
typographic ones -- a bullet's hanging indent (``LeftIndent`` /
``RightIndent``), the shading and border box drawn around a paragraph, and a
table's column order (``TableDirection``, on the table *and* on the table style
every unstyled table inherits it from).

**An Arabic page is not wholly Arabic.** It carries equations, URLs, file names
and page numbers, and each has to keep the order it was written in.
:func:`preserve_ltr_content` pins the runs that hold nothing but
left-to-right content -- and only those -- so the neutral ``+`` and ``=``
between the numbers of ``10x + 15y = 150`` resolve inside the expression
instead of against the paragraph around it. A run with so much as one Arabic
letter is left to bidi, which is what mixed prose needs.

Three kinds of value are deliberately left alone, for the same reason
throughout: they are not absolute. ``BothSides``, ``FullyJustified`` and a
scalar ``InsetSpacing`` are symmetric and name no side at all.
``SideTowardsSpine``, ``AwayFromBindingSide`` and ``ToBindingSide`` are
binding-relative, so InDesign re-resolves them the moment ``PageBinding``
flips; mirroring them here would mirror them twice. And ``FirstLineIndent`` is
measured from the paragraph's *leading* edge, which ``ParagraphDirection`` has
already moved -- negating it as well turns a hanging indent back into a
first-line indent.

**Two declarations the source cannot supply.** Arabic, Hebrew, Persian and Urdu
compose correctly only under Adobe's World-Ready composer, so every paragraph
is moved onto it -- including the paragraphs that named no composer, since
those inherit the Latin one rather than nothing. And the target face is
registered in ``Resources/Fonts.xml``: naming a family in ``AppliedFont`` that
the package never declares opens the document with a missing-font warning and a
substituted face, which for an Arabic run means glyphs drawn from something
that has none of them.

"""

from __future__ import annotations

import logging

from lxml import etree

logger = logging.getLogger(__name__)

IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

# Absolute alignments swap under a mirror. `AwayFromBindingSide` and
# `ToBindingSide` are already binding-relative -- InDesign re-resolves them when
# PageBinding flips, so touching them would mirror those paragraphs twice.
# `CenterAlign`, `FullyJustified`, `CenterJustified` and `DefaultJustification`
# name no side and are left exactly as authored.
#
# `LeftJustified`/`RightJustified` are justified-with-last-line-aligned. The
# side they name is as absolute as `LeftAlign`'s, so they mirror the same way;
# leaving them out stranded every justified paragraph's last line.
_ALIGN_FLIP = {
    "LeftAlign": "RightAlign",
    "RightAlign": "LeftAlign",
    "LeftJustified": "RightJustified",
    "RightJustified": "LeftJustified",
}

# The wrap contour's side is absolute in the same way. `BothSides` is
# symmetric, and `SideTowardsSpine`/`SideAwayFromSpine` are binding-relative --
# both are re-resolved or unaffected when `PageBinding` flips, so neither is
# touched here.
_WRAP_SIDE_FLIP = {"LeftSide": "RightSide", "RightSide": "LeftSide"}

# The corner *of the object* pinned to its anchor. `HorizontalAlignment` says
# where the anchor sits; this says which part of the object is put there, so
# flipping one without the other slides the object sideways by its own width.
# The three centre-column points sit on the mirror axis and map to themselves.
_ANCHOR_POINT_FLIP = {
    "TopLeftAnchor": "TopRightAnchor",
    "TopRightAnchor": "TopLeftAnchor",
    "LeftCenterAnchor": "RightCenterAnchor",
    "RightCenterAnchor": "LeftCenterAnchor",
    "BottomLeftAnchor": "BottomRightAnchor",
    "BottomRightAnchor": "BottomLeftAnchor",
}

# Arabic, Hebrew, Persian and Urdu are laid out correctly only by Adobe's
# World-Ready composer ("Optyca" is its internal name). Under the Latin
# composer InDesign sets the run in logical order and applies no bidi
# reordering, which is what prints shaped-but-backwards Arabic.
_COMPOSER_WORLD_READY = {
    "HL Composer": "HL Composer Optyca",
    "HL Single": "HL Single Optyca",
}
_DEFAULT_COMPOSER = "HL Composer Optyca"

# Both human-authored Arabic references set Western digits throughout and never
# an Arabic-Indic one. Writing the attribute rather than inheriting it is what
# stops the arithmetic changing numeral set on someone else's machine.
_DIGITS = "DefaultDigits"

_RTL = "RightToLeftDirection"

# A bullet that points somewhere has to point *into* the text. RTL moves the
# bullet to the other side of the line but cannot turn the glyph round, so a
# direction line set with a rightwards arrowhead ends up pointing away from the
# sentence it introduces.
#
# These pairs are true Unicode mirrors sitting in the same block as each other,
# so a face that carries one carries the other and the bullet font is left
# alone.
_BULLET_MIRROR = {
    0x2190: 0x2192, 0x2192: 0x2190,      # ← →
    0x21D0: 0x21D2, 0x21D2: 0x21D0,      # ⇐ ⇒
    0x25B6: 0x25C0, 0x25C0: 0x25B6,      # ▶ ◀
    0x25B8: 0x25C2, 0x25C2: 0x25B8,      # ▸ ◂
    0x25BA: 0x25C4, 0x25C4: 0x25BA,      # ► ◄
    0x25BB: 0x25C5, 0x25C5: 0x25BB,      # ▻ ◅
    0x27A1: 0x2B05, 0x2B05: 0x27A1,      # ➡ ⬅
}

# The Dingbats arrows are the case `_BULLET_MIRROR` cannot serve: every arrow
# in ITC Zapf Dingbats points right and the family has no leftward twin at any
# codepoint, so remapping one inside its own face prints a missing-glyph box.
# Left as authored, though, the arrowhead introducing each direction line sits
# at the right of an Arabic sentence pointing away from it. The human-
# translated reference books do not leave it: they flip the arrow, drawing it
# as artwork because the face has no glyph for it.
#
# So a substitution names both the codepoint and the face to draw it from: the
# plain left pointer for an arrowhead, the plain leftwards arrow for an arrow
# with a shaft. Both are WGL4, so Arial carries them on every machine that can
# open the document, and every book in the corpus already declares Arial --
# nothing new has to be installed for the bullet to render. A curved or
# diagonal dingbat is left alone: a plain left pointer is not the mirror of
# one, only a different glyph.
#
# Consulted before `_BULLET_MIRROR`, which is for a mirror the bullet's own
# face can be trusted to have.
_BULLET_FALLBACK = ("Arial", "Regular")
_BULLET_SUBSTITUTE = {
    # arrowheads and pointers -- U+25C4
    **{cp: 0x25C4 for cp in (0x27A2, 0x27A3, 0x27A4)},
    # straight rightwards arrows with a shaft -- U+2190
    **{cp: 0x2190 for cp in (0x2794, 0x2799, 0x279B, 0x279C, 0x279D, 0x279E,
                             0x279F, 0x27A0, 0x27A1, 0x27A7, 0x27A8, 0x27A9,
                             0x27AA, 0x27AB, 0x27AC, 0x27AD, 0x27AE, 0x27AF,
                             0x27B1, 0x27B2, 0x27B3)},
}

# Minimum overlap, in points, for an item to count as sitting on a page. Well
# under a printer's dot and far above the float noise the transform arithmetic
# leaves on a frame aligned to the spine.
_OVERLAP_EPS = 0.01

# How much of *itself* an item has to put on a page before that page counts as
# one it spans, as a fraction of the item's own width.
#
# Items lap over the spine for reasons that have nothing to do with belonging
# to the facing page. A full-bleed backdrop is drawn a little larger than its
# page in every direction. A text frame is drawn as wide as the designer felt
# like dragging it, and its empty tail can run well past the gutter. Measured
# against `_OVERLAP_EPS` alone, 0.62pt of backdrop overhang reads as a genuine
# two-page overlap, the backdrop is taken for a gutter-spanning banner, and
# reflecting a banner about the *spread* centre carries the whole thing onto
# the facing page -- which is how a left-page backdrop ended up printing on the
# right page of a real spread.
#
# The share is measured against the item because that is the question being
# asked: does this item live on both pages, or does a piece of it merely stick
# out? Against the *page* instead, the floor is a fixed 12pt whatever the item,
# so a 623pt-wide answer-line frame overhanging the spine by 47.5pt -- 7.6% of
# itself, and no more part of the facing page than 0.62pt of bleed is -- was
# called a banner and mirrored onto page 13, taking problem 4 of page 12 with
# it. Against the item, 15% separates the two cleanly: every overhang in the
# sample books is under 8% of its item, and nothing at all falls between there
# and the half-and-half of a real spanner. It also keeps a small item astride
# the spine -- a 10pt icon, 5pt each side -- correctly spread-spanning rather
# than assigned to whichever page it leans towards.
_PAGE_SHARE = 0.15


def _localname(el) -> str:
    if not isinstance(el.tag, str):  # comments / PIs
        return ""
    return etree.QName(el).localname


def _is(el, name: str) -> bool:
    """True for an unnamespaced IDML element of this name.

    Every `Spreads/*.xml` is rooted in `<idPkg:Spread>`, a packaging wrapper
    whose local name collides with the real `<Spread>` inside it. Matching on
    local name alone treats that wrapper as a spread and the real spread as one
    of its page items — which would mirror every item a second time by way of
    its own container. Document content is unnamespaced; the wrapper is not.
    """
    return el.tag == name


# ---- matrix helpers --------------------------------------------------------


def parse_transform(value: str | None) -> tuple[float, ...]:
    """`"a b c d tx ty"` -> 6-tuple. Anything unparseable is the identity."""
    if not value:
        return IDENTITY
    parts = value.split()
    if len(parts) != 6:
        return IDENTITY
    try:
        return tuple(float(p) for p in parts)
    except ValueError:
        return IDENTITY


def _num(v: float) -> str:
    # Keep whole numbers integral so an untouched matrix round-trips as it was
    # written ("1 0 0 1 ...", not "1.0 0.0 ...").
    if v == int(v):
        return str(int(v))
    return repr(v)


def format_transform(t: tuple[float, ...]) -> str:
    return " ".join(_num(v) for v in t)


def apply_transform(t: tuple[float, ...], x: float, y: float) -> tuple[float, float]:
    a, b, c, d, tx, ty = t
    return (a * x + c * y + tx, b * x + d * y + ty)


def compose(outer: tuple[float, ...], inner: tuple[float, ...]) -> tuple[float, ...]:
    """`outer` composed with `inner` -- apply `inner` first, then `outer`."""
    a1, b1, c1, d1, tx1, ty1 = outer
    a2, b2, c2, d2, tx2, ty2 = inner
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * tx2 + c1 * ty2 + tx1,
        b1 * tx2 + d1 * ty2 + ty1,
    )


# ---- bounds ----------------------------------------------------------------


def _is_page_item(el) -> bool:
    """A page item is any spread child carrying its own transform.

    Matching on `ItemTransform` rather than an allowlist of tag names means
    every frame type IDML defines -- `Rectangle`, `Oval`, `Polygon`,
    `GraphicLine`, `TextFrame`, `TextBox`, `Group`, buttons, media, imported
    pages -- is handled without the list going stale. `Page` carries a transform
    too and is the one child that must never move.
    """
    return (
        el.get("ItemTransform") is not None
        and isinstance(el.tag, str)
        and not _is(el, "Page")
        and etree.QName(el).namespace is None
    )


def item_bounds(el, parent: tuple[float, ...] = IDENTITY):
    """Axis-aligned bounds of a page item in its parent's coordinate space.

    Prefers the item's own `PathGeometry` -- the visible frame. An image placed
    inside a frame is a child with its own, usually larger, geometry; measuring
    that instead would place the mirror off by the amount the frame crops.

    Failing that, `PathBoundingBox`: form controls (`CheckBox`, `RadioButton`,
    `Button`) declare no path, because their appearance lives in `<State>`
    children. Reading only `PathGeometry` left every checkbox on a worksheet
    behind on the old binding edge.

    Only a container with neither (a `Group`) is measured from its children.
    """
    t = compose(parent, parse_transform(el.get("ItemTransform")))
    xs: list[float] = []
    ys: list[float] = []

    geom = el.find("./{*}Properties/{*}PathGeometry")
    box = el.find("./{*}Properties/{*}PathBoundingBox")
    if geom is None and box is not None:
        try:
            left, top = float(box.get("Left")), float(box.get("Top"))
            right, bottom = float(box.get("Right")), float(box.get("Bottom"))
        except (TypeError, ValueError):
            return None
        for corner in ((left, top), (right, top), (left, bottom), (right, bottom)):
            x, y = apply_transform(t, *corner)
            xs.append(x)
            ys.append(y)
    elif geom is not None:
        for point in geom.iter("{*}PathPointType"):
            anchor = point.get("Anchor")
            if not anchor:
                continue
            coords = anchor.split()
            if len(coords) != 2:
                continue
            try:
                px, py = float(coords[0]), float(coords[1])
            except ValueError:
                continue
            x, y = apply_transform(t, px, py)
            xs.append(x)
            ys.append(y)
    else:
        for child in el:
            if not _is_page_item(child):
                continue
            box = item_bounds(child, t)
            if box is None:
                continue
            xs.extend((box[0], box[2]))
            ys.extend((box[1], box[3]))

    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def page_extents(spread) -> list[tuple[float, float]]:
    """Each page's horizontal extent in spread coordinates, in document order.

    `GeometricBounds` is `"y0 x0 y1 x1"` in page space; each page's
    `ItemTransform` places it in the spread.
    """
    extents: list[tuple[float, float]] = []
    for page in spread:
        if not _is(page, "Page"):
            continue
        bounds = (page.get("GeometricBounds") or "").split()
        if len(bounds) != 4:
            continue
        try:
            y0, x0, y1, x1 = (float(v) for v in bounds)
        except ValueError:
            continue
        t = parse_transform(page.get("ItemTransform"))
        xs = [apply_transform(t, cx, cy)[0]
              for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
        extents.append((min(xs), max(xs)))
    return extents


def spread_axis(spread) -> float | None:
    """The centre of the whole spread — the axis for an item spanning pages."""
    extents = page_extents(spread)
    if not extents:
        return None
    return (min(x0 for x0, _ in extents) + max(x1 for _, x1 in extents)) / 2.0


def pages_of(box, extents) -> list[int]:
    """Indices of the pages an item sits on, in document order.

    Empty means the pasteboard; one index means the item belongs to that page;
    two or more means it genuinely spans the gutter. The three cases are what
    :func:`mirror_axis_for` decides an item's mirror axis from, and what
    `idml.validate` asks to tell an object that legitimately crossed the gutter
    from one that was dropped on the wrong page.

    An item with no width is decided by containment rather than by overlap: a
    vertical rule covers no area, so an area test puts it on no page at all and
    the mirror walks straight past it. A rule sitting exactly on the spine
    touches both pages.

    Overlap is measured against a floor rather than zero, for failures at very
    different scales. A frame set flush to the spine comes out of the transform
    arithmetic at `-0.0` or `-1e-13`, which counts as a real overlap against a
    bare `> 0`. A full-bleed backdrop laps a fraction of a point over the spine
    because it is drawn larger than its page. A text frame runs tens of points
    past it because that is where the designer stopped dragging. All of them
    read as a second page and turn a single-page item into a spread-spanning
    one, which mirrors it across the gutter; the floor is a share of the item's
    own width, see `_PAGE_SHARE`.

    An item that clears the floor on no page at all but still touches one is
    the pasteboard's near miss: it belongs to the page it covers most, so that
    a frame parked half off the sheet still mirrors with the page it shows on.
    """
    x0, x1 = box[0], box[2]
    if x1 - x0 <= _OVERLAP_EPS:
        return [i for i, (px0, px1) in enumerate(extents)
                if px0 - _OVERLAP_EPS <= x0 <= px1 + _OVERLAP_EPS]

    overlaps = [min(x1, px1) - max(x0, px0) for px0, px1 in extents]
    floor = max(_OVERLAP_EPS, _PAGE_SHARE * (x1 - x0))
    hit = [i for i, ov in enumerate(overlaps) if ov > floor]
    if hit:
        return hit
    # Nothing cleared the floor, but something is on a page: an item parked
    # mostly on the pasteboard with a corner showing still prints, and still
    # has to mirror with the page that shows it. It belongs to the page it
    # covers most.
    best = max(range(len(overlaps)), key=overlaps.__getitem__, default=None)
    return [best] if best is not None and overlaps[best] > _OVERLAP_EPS else []


def dominant_page(box, extents) -> int | None:
    """The page an item covers most of, or None when it covers none.

    The page an item *is on*, in the sense a reader means: a bleed lapping a
    few points over the gutter has not moved house. `idml.validate` asks this
    of an item before and after the mirror, because an item changing the page
    it mostly covers is how content lands on the facing page -- problem 4 of
    page 12 printing on page 13.
    """
    x0, x1 = box[0], box[2]
    best, covered = None, _OVERLAP_EPS
    for i, (px0, px1) in enumerate(extents):
        overlap = min(x1, px1) - max(x0, px0)
        if x1 - x0 <= _OVERLAP_EPS:  # a rule has no area; containment decides
            overlap = 0.0 if not (px0 - _OVERLAP_EPS <= x0 <= px1 + _OVERLAP_EPS)                 else px1 - px0
        if overlap > covered:
            best, covered = i, overlap
    return best


# Tolerance for "this item reaches the page edge", in points.
_EDGE_TOL = 1.0
# A fixed item only narrows a page's content area when it runs down most of the
# page's height -- a side strip, not a corner badge or a running head.
_SIDE_BAND_HEIGHT_SHARE = 0.5


def page_boxes(spread) -> list[tuple[float, float, float, float]]:
    """Each page's `(x0, y0, x1, y1)` in spread coordinates, in document order."""
    boxes: list = []
    for page in spread:
        if not _is(page, "Page"):
            continue
        bounds = (page.get("GeometricBounds") or "").split()
        if len(bounds) != 4:
            continue
        try:
            y0, x0, y1, x1 = (float(v) for v in bounds)
        except ValueError:
            continue
        t = parse_transform(page.get("ItemTransform"))
        pts = [apply_transform(t, cx, cy)
               for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
        boxes.append((min(p[0] for p in pts), min(p[1] for p in pts),
                      max(p[0] for p in pts), max(p[1] for p in pts)))
    return boxes


def content_axes(pages, furniture) -> list[float]:
    """The axis each page's content mirrors about.

    The page's own centre, unless fixed furniture runs down one side of it --
    the blue strip carrying a lesson's badge and vertical title. Content then
    mirrors within the area that strip leaves: a paragraph set 61pt clear of
    the strip in English lands 61pt clear of the opposite edge, instead of
    being thrown into the strip by a reflection about the physical centre.
    Measured from the furniture actually on the page, so a book with a wider
    strip, a strip on the other side, or none at all needs nothing changed.
    """
    axes: list = []
    for px0, py0, px1, py1 in pages:
        left, right = px0, px1
        mid = (px0 + px1) / 2.0
        height = py1 - py0
        for fx0, fy0, fx1, fy1 in furniture:
            covered = min(fy1, py1) - max(fy0, py0)
            if height <= 0 or covered < _SIDE_BAND_HEIGHT_SHARE * height:
                continue
            if min(fx1, px1) - max(fx0, px0) <= 0:
                continue
            if fx0 <= px0 + _EDGE_TOL and fx1 < mid:
                left = max(left, fx1)
            elif fx1 >= px1 - _EDGE_TOL and fx0 > mid:
                right = min(right, fx0)
        axes.append((left + right) / 2.0)
    return axes


def mirror_axis_for(box, extents, spread_centre, axes=None) -> float | None:
    """The axis a single item reflects about.

    An item mirrors **within its own page**. Reflecting a facing-page spread
    about its centre instead would carry every item across the gutter and swap
    the two pages — page 17 printing where page 16 belongs. Page order is a
    property of the document, not of the layout, and RTL binding is expressed
    by `PageBinding`, not by moving content between pages.

    Three cases, decided by which pages the item actually overlaps:

    * exactly one page — reflect about that page's centre;
    * two or more — a spread-spanning banner or full-bleed backdrop, which has
      no single page to belong to, so it reflects about the spread centre and
      keeps covering what it covered;
    * none — the item sits on the pasteboard and never prints, so it is left
      exactly where the designer parked it.

    Which pages an item sits on is :func:`pages_of`, including how a zero-width
    rule and a bleed's sub-point overhang are judged; this only turns that
    answer into an axis.

    `axes`, when given, is :func:`content_axes` for the same pages: a single-
    page item mirrors about its page's content axis instead of the page's
    physical centre. An item spanning the whole page width (a background)
    still uses the physical centre, so it keeps covering both edges.
    """
    hit = pages_of(box, extents)
    if not hit:
        return None
    if len(hit) == 1:
        px0, px1 = extents[hit[0]]
        spans_page = box[0] <= px0 + _EDGE_TOL and box[2] >= px1 - _EDGE_TOL
        if axes is not None and hit[0] < len(axes) and not spans_page:
            return axes[hit[0]]
        return (px0 + px1) / 2.0
    return spread_centre


def keep_on_page(box, dx, extents) -> float:
    """`dx`, corrected so `box` moved by it enters no page beside its own.

    The reflection that mirrors an item within its page carries whatever of it
    lay off the page across with it: a band bleeding off a right-hand page's
    outer trim comes back with that bleed over the spine, printing on the
    facing page. The target keeps the source's binding, so the spine is still
    the spine. On each side of its page where another page sits, the item is
    therefore stopped at the page edge; an outer trim, with no page beyond it,
    still takes the overhang. Only the position changes -- never the size --
    and a component passes its union box so its members shift as one piece.

    An item on no single page (a gutter-spanning banner, the pasteboard) has
    no page to be held to and keeps `dx`; so does one wider than the room
    between two neighbouring pages, which cannot fit whatever is done.
    Neighbours are found from the page geometry, not from document order.
    """
    hit = pages_of(box, extents)
    if len(hit) != 1:
        return dx
    px0, px1 = extents[hit[0]]
    others = [e for i, e in enumerate(extents) if i != hit[0]]
    lo = px0 if any(ox1 <= px0 + _EDGE_TOL for _, ox1 in others) else None
    hi = px1 if any(ox0 >= px1 - _EDGE_TOL for ox0, _ in others) else None
    x0, x1 = box[0] + dx, box[2] + dx
    if lo is not None and hi is not None and x1 - x0 > hi - lo + _OVERLAP_EPS:
        return dx
    if lo is not None and x0 < lo - _OVERLAP_EPS:
        return dx + (lo - x0)
    if hi is not None and x1 > hi + _OVERLAP_EPS:
        return dx - (x1 - hi)
    return dx



# ---- mirroring -------------------------------------------------------------


# Content that makes an item more than a decorative shape. Any of these inside
# a frame means reflecting its path would reflect something that must never be
# reflected -- the `scaleX(-1)` trap, one level down.
_CONTENTFUL = ("Link", "Image", "PDF", "EPS", "WMF", "Content",
               "CharacterStyleRange", "ParagraphStyleRange")

# How IDML names the two kinds of placed graphic. A raster arrives as `Image`;
# art placed from `.ai`, `.pdf` or `.eps` arrives as `PDF`, `EPS` or `WMF`.
# The distinction decides whether the mirror may turn the picture round; see
# :func:`is_placed_photograph`.
_RASTER = ("Image",)
_VECTOR = ("PDF", "EPS", "WMF")


def is_decorative_path(el) -> bool:
    """True for an item whose whole appearance is its own outline.

    A dotted swoosh, a rule, a bracket, an arrow: nothing inside it has an
    orientation of its own, so reflecting the outline reflects the item and
    nothing else. A frame holding text or a placed graphic is excluded --
    that content has its own reading direction and mirroring it produces
    backwards type and reversed photographs.

    `Group` is excluded because groups already mirror as one unit and their
    children are reached on their own terms; reflecting the group's path would
    mirror it a second time.
    """
    if not _is_page_item(el) or _is(el, "Group"):
        return False
    if el.get("ParentStory") is not None:
        return False
    if el.find("./{*}Properties/{*}PathGeometry") is None:
        return False
    for child in el.iter():
        if child is el:
            continue
        if _localname(child) in _CONTENTFUL:
            return False
    # Reflecting local x is a true mirror only while the item's own axes are
    # still parallel to the page's. Under rotation or shear they are not, and
    # reflecting anyway would distort the artwork rather than mirror it.
    a, b, c, d = parse_transform(el.get("ItemTransform"))[:4]
    return b == 0.0 and c == 0.0 and a != 0.0 and d != 0.0


def reflect_path(el) -> bool:
    """Reflect a decorative item's own outline about its centre.

    The mirror moves an item's position by its `tx` alone, deliberately never
    negating the matrix, so an item's *content* is never flipped. That is right
    for a photograph and essential for text -- but an asymmetric decorative
    curve is all content and no text, and moving it without reflecting it
    leaves it curving the way it always did on the wrong side of the page. The
    dotted swoosh pointing at the `SAY` callout ends up pointing away from it.

    Reflecting the path points in the item's own space achieves the mirror
    without touching `a b c d`: the outline flips, while width, height,
    rotation, scale and every other item keep the guarantees the matrix rule
    exists to give. The axis is the centre of the anchors' own x-range, so the
    item's bounds are unchanged and the `tx` mirror still places it correctly.

    **Only the item's own outline.** A frame can hold a child frame, and each
    carries a `PathGeometry` of its own; the child's is written in the parent's
    space and is that child's business, reached when the child is walked. Swept
    up here it does two kinds of damage at once: it drags the axis off the
    item's own centre, which moves the outline instead of reflecting it in
    place -- two rectangles of a graphic organiser travelled clear across the
    gutter that way -- and it rewrites the child's path without touching the
    transform that places it. So the points come from `Properties/PathGeometry`
    alone, the same geometry :func:`item_bounds` measures, which is what makes
    "the item's bounds are unchanged" true rather than nearly true.

    Returns True when the item was reflected.
    """
    if not is_decorative_path(el):
        return False
    axis = _path_axis(el)
    if axis is None:
        return False
    _reflect_geometry(el.find("./{*}Properties/{*}PathGeometry"), axis)
    _reflect_wrap_contour(el, axis)
    return True


def _path_axis(el) -> float | None:
    """The centre of an item's own outline, in the item's own space.

    Reflecting about this axis and no other is what makes "the item's bounds
    are unchanged" true: it is the same geometry :func:`item_bounds` measures,
    so the `tx` mirror still places the item exactly where it computed.
    """
    geom = el.find("./{*}Properties/{*}PathGeometry")
    if geom is None:
        return None
    xs: list[float] = []
    for point in geom.iter("{*}PathPointType"):
        anchor = (point.get("Anchor") or "").split()
        if len(anchor) == 2:
            try:
                xs.append(float(anchor[0]))
            except ValueError:
                pass
    if not xs:
        return None
    return (min(xs) + max(xs)) / 2.0


def _reflect_geometry(geom, axis: float) -> int:
    """Reflect every point of one path about `axis`. Returns points moved."""
    if geom is None:
        return 0
    moved = 0
    for point in geom.iter("{*}PathPointType"):
        # Map the anchor and both control points, and leave each handle in its
        # own role. `LeftDirection`/`RightDirection` name a point's incoming and
        # outgoing tangent -- path order, not screen position -- so a
        # reflection, which maps control points and nothing else, does not
        # exchange them. Exchanging them is what *reversing* a path does; here
        # it swaps every point's lead-in and lead-out tangent lengths, kinking
        # each one, and a smooth spiral comes out an arbitrary shape.
        for attr in ("Anchor", "LeftDirection", "RightDirection"):
            value = _reflect_pair(point.get(attr), axis)
            if value is not None:
                point.set(attr, value)
                moved += 1
    return moved


def _reflect_wrap_contour(el, axis: float) -> int:
    """Reflect a frame's wrap contour along with the outline it hugs.

    `TextWrapMode="Contour"` wraps text around a path drawn by hand round the
    subject, written in the frame's own space beside the frame's own geometry.
    Reflecting the frame and not the contour leaves the two disagreeing, and
    the disagreement is not cosmetic: the measure available to the text on each
    line comes from the contour, so a silhouette cut for a right-facing figure
    and moved to the left of the page carves the wrong bite out of every line.
    With `TextWrapSide="BothSides"` it opens a gap in the middle of the column
    that was never there, and the composer fills the sliver on the far side of
    the picture -- which is how the tail of an Arabic heading ended up printing
    on the *left* of its own first line.
    """
    return _reflect_geometry(
        el.find("./{*}TextWrapPreference/{*}Properties/{*}PathGeometry"), axis)


def placed_content(el) -> set:
    """Which kinds of placed graphic a frame holds: `Image`, `PDF`, `EPS`, `WMF`."""
    return {_localname(child) for child in el.iter()
            if child is not el and _localname(child) in _RASTER + _VECTOR}


def is_placed_photograph(el, keep_upright=()) -> bool:
    """True for a frame whose whole content is a placed raster picture.

    The human-translated Arabic references *do* turn a photograph round: the
    sprinters on the Lesson 12 family letter run rightwards in the English
    edition and leftwards in the Arabic one. They never turn the vector art
    beside it round -- a coordinate plane keeps x running rightwards, a "?"
    badge keeps its glyph the right way about -- because a diagram's
    orientation carries meaning and its labels are type. Mirroring everything
    is the `scaleX(-1)` trap; mirroring nothing leaves a photograph facing off
    the page and, where it wraps text, cutting the wrong side out of every line.

    IDML draws the line for us. A raster is `<Image>`; every technical figure,
    icon and logo in the corpus is placed vector art (`<PDF>`, `<EPS>`,
    `<WMF>`), and a frame holding a mix of the two is left alone rather than
    guessed at. A frame setting text of its own is excluded for the reason
    :func:`is_decorative_path` excludes one, and a rotated or sheared frame for
    the reason it excludes those: reflecting local x is a true mirror only
    while the item's own axes are parallel to the page's.

    `keep_upright` names link URIs whose artwork the translation stage has
    already rewritten. Those carry target-language type burned into the pixels,
    so turning them round would print the translation backwards -- the one
    thing mirroring a picture is supposed to avoid.
    """
    if not _is_page_item(el) or _is(el, "Group"):
        return False
    if _carries_text(el):
        return False
    if el.find("./{*}Properties/{*}PathGeometry") is None:
        return False
    if placed_content(el) != set(_RASTER):
        return False
    if keep_upright and _link_uris(el) & set(keep_upright):
        return False
    a, b, c, d = parse_transform(el.get("ItemTransform"))[:4]
    return b == 0.0 and c == 0.0 and a != 0.0 and d != 0.0


def _link_uris(el) -> set:
    """Every asset URI a frame's placed content points at."""
    return {child.get("LinkResourceURI") or ""
            for child in el.iter() if _is(child, "Link")}


def reflect_graphic(el, keep_upright=()) -> bool:
    """Turn a placed photograph round inside its own frame.

    Three things move together or the picture comes apart. The frame's
    **outline** is often a silhouette cut round the subject, so it reflects
    like any decorative path. Its **wrap contour** reflects with it, for the
    reasons in :func:`_reflect_wrap_contour`. And the **picture** reflects too,
    by composing a mirror onto each child's transform rather than by editing
    the frame's own `a b c d` -- so the frame keeps every guarantee the matrix
    rule gives it (width, height, rotation, scale, position) and only what it
    contains is turned round.

    One axis for all three, the centre of the frame's own outline, which is why
    the frame's bounds are unchanged and the `tx` mirror still lands it in the
    right place. Composing onto the *children* also means a picture nested one
    frame deeper -- the usual `Polygon > Rectangle > Image` a clipped photo
    arrives as -- is carried round by its parent rather than reflected about an
    axis of its own, which would slide it out from under the silhouette.

    Returns True when the picture was turned round.
    """
    if not is_placed_photograph(el, keep_upright):
        return False
    axis = _path_axis(el)
    if axis is None:
        return False

    _reflect_geometry(el.find("./{*}Properties/{*}PathGeometry"), axis)
    _reflect_wrap_contour(el, axis)

    mirror = (-1.0, 0.0, 0.0, 1.0, 2.0 * axis, 0.0)
    for child in el:
        if child.get("ItemTransform") is None:
            continue
        child.set("ItemTransform", format_transform(
            compose(mirror, parse_transform(child.get("ItemTransform")))))

    # The crop records how much of the picture each edge of the frame hides.
    # The picture has just swapped ends, so the two horizontal figures have too;
    # left as they were they re-crop the other side the moment auto-fit runs.
    fitting = el.find("./{*}FrameFittingOption")
    if fitting is not None:
        _swap_attrs(fitting, "LeftCrop", "RightCrop")
    return True


def _reflect_pair(value: str | None, axis: float) -> str | None:
    """`"x y"` reflected about `axis`; None when it is not a coordinate pair."""
    if not value:
        return None
    parts = value.split()
    if len(parts) != 2:
        return None
    try:
        x, y = float(parts[0]), float(parts[1])
    except ValueError:
        return None
    return f"{_num(2.0 * axis - x)} {_num(y)}"


def _carries_text(el) -> bool:
    """True for an item that sets type of its own."""
    if el.get("ParentStory") is not None:
        return True
    return any(_localname(d) in ("CharacterStyleRange", "ParagraphStyleRange")
               for d in el.iter())


def _resolve_members(members, index):
    """`(Decision, element, bounds)` for every member `index` can find.

    A member with no matching element (should not happen, but a package with
    a `Self` the plan never saw is not this function's business to raise
    over) or no measurable bounds is dropped rather than crashing the whole
    component's move over one bad entry.
    """
    resolved = []
    for d in members:
        el = index.get(d.object)
        if el is None:
            continue
        box = item_bounds(el, _parent_transform(el))
        if box is None:
            continue
        resolved.append((d, el, box))
    return resolved


def _page_item_ancestors(el) -> list:
    """`el`'s enclosing page items, outermost first, the spread excluded."""
    return [a for a in reversed(list(el.iterancestors()))
            if _is_page_item(a) and not _is(a, "Spread")
            and not _is(a, "MasterSpread")]


def _parent_transform(el) -> tuple[float, ...]:
    """What places `el`'s own `ItemTransform` in its spread's coordinates.

    A component can join a spread child to an item drawn inside another
    group -- a form field and the backdrop behind it, say. That item's path is
    written in its group's space, and measured there it can seem to sit on the
    other page entirely, which is enough to make a component look as if it
    straddles the gutter and mirror it about the spread centre.
    """
    t = IDENTITY
    for a in _page_item_ancestors(el):
        t = compose(t, parse_transform(a.get("ItemTransform")))
    return t


def _is_nested(el) -> bool:
    """True for an item carried by an enclosing page item's own move."""
    return bool(_page_item_ancestors(el))


def _axes_along_the_page(el) -> bool:
    """Is `el`'s coordinate space still aligned with the page's?

    Reflecting positions inside a group about a vertical line in the group's
    own space is a page mirror only while that space is not rotated or
    sheared on the page -- composed through every ancestor, since a turned
    parent turns everything inside it.
    """
    chain = [el] + [a for a in el.iterancestors() if _is_page_item(a)]
    t = IDENTITY
    for node in reversed(chain):
        t = compose(t, parse_transform(node.get("ItemTransform")))
    return abs(t[1]) <= _AXIS_EPS and abs(t[2]) <= _AXIS_EPS


def _mirror_arrangement(group, rigid: frozenset = frozenset(),
                        blocks: dict | None = None) -> int:
    """Reflect where each child of `group` sits, about the group's own centre.

    Together with moving the group itself across its page, this puts every
    child exactly where reflecting that child about the page axis would put
    it: a callout bar's icon ends up at its leading edge, not still at the
    left end of a bar that has crossed the page. Each child's own drawing is
    untouched -- only its `tx` changes, plus :func:`reflect_path` for a purely
    decorative outline, the same as any other mirrored item.

    Recurses into child groups. A child listed in `rigid` (a styled equation,
    say) is moved as a whole but its own inside is left as drawn. Children
    are measured in the group's own space, which is where their transforms
    are written, so the arithmetic needs no conversion -- provided that space
    is not rotated on the page; when it is, nothing inside is rearranged.

    **`blocks` names children that reflect as one unit**, mapping each child's
    `Self` to the id of the equation block it belongs to
    (`rtl_components`'s `"equation"` components, passed down by
    :func:`apply_plan`). Their union is reflected once and every one of them
    moves by that single delta, so their relative offsets -- which are the
    mathematics, not a reading order -- survive intact; without it a group
    holding a heading and the five frames spelling `3 · 4 = 12` would
    rearrange the equation into `12 = 4 · 3` while correctly moving the
    heading. Their own outlines are not reflected either, for the same
    reason: inside the block, nothing turns round.

    Returns how many children moved.
    """
    if not _axes_along_the_page(group):
        return 0
    blocks = blocks or {}
    children = [(child, item_bounds(child)) for child in group
                if _is_page_item(child)]
    children = [(child, box) for child, box in children if box is not None]
    if len(children) < 2:
        return 0
    axis = (min(b[0] for _, b in children) + max(b[2] for _, b in children)) / 2.0
    # One unit per equation block, and one per child that is in none.
    units: dict = {}
    for child, box in children:
        units.setdefault(blocks.get(child.get("Self"), child), []).append(
            (child, box))
    moved = 0
    for key, unit in units.items():
        in_block = isinstance(key, str)
        x0 = min(box[0] for _, box in unit)
        x1 = max(box[2] for _, box in unit)
        dx = 2.0 * axis - (x0 + x1)
        for child, box in unit:
            t = parse_transform(child.get("ItemTransform"))
            child.set("ItemTransform",
                      format_transform(t[:4] + (t[4] + dx, t[5])))
            if not in_block:
                reflect_path(child)
            moved += 1
            if (_is(child, "Group") and not in_block
                    and child.get("Self") not in rigid):
                moved += _mirror_arrangement(child, rigid, blocks)
    return moved


def _move_component(anchor, members, index, extents, centre,
                    rigid: frozenset = frozenset(), axes=None,
                    blocks: dict | None = None) -> bool:
    """Carry out one component's decision across every member, exactly once.

    A component's non-anchor members carry `KEEP_POSITION`/`component.bound`
    (Task 5) precisely so the executor moves the component once instead of
    moving it and then moving each member again -- but "once" means something
    different for the two shapes `rtl_components.detect` produces, and for the
    two actions that reach here.

    **A group anchor is the `<Group>` element itself.** Its children's own
    `ItemTransform` is written in the *group's* coordinate space, so moving
    the anchor's own `tx` already carries every child with it -- nothing else
    needs to move, and moving a child as well would move it twice.
    `RTL_REPOSITION` on a group anchor therefore touches only the anchor.
    `RTL_RESTRUCTURE` is the opposite: the group's own outline -- what the
    page mirror already computed for it -- must stay exactly where it is
    (the anchor's own `tx` is left alone), and only the children, excluded
    from `members` by `d.object != anchor.object`, are reflected about the
    union of their own bounds.

    **A cluster anchor is just one sibling among several independent spread
    children** -- an arrow beside the sentence it introduces -- with no
    shared transform to piggyback on. `RTL_REPOSITION` has to move every
    member individually, by one delta shared across all of them (computed
    once, from the union of their bounds, reflected about the page axis) so
    their relative arrangement survives the trip unchanged. `RTL_RESTRUCTURE`
    still has to move every member, the anchor included: an arrow that is
    itself one of the things being rearranged has to end up on the other side
    of its own sentence, so unlike a group it takes part in the same
    union-centre reflection as its siblings rather than sitting it out.

    Both `RTL_RESTRUCTURE` branches reflect about the *members'* own union
    centre, never the page axis -- the component rearranges internally and
    does not, as a whole, change which side of the page it is on. Both
    `RTL_REPOSITION` branches reflect about the page axis, via
    :func:`mirror_axis_for`, exactly as a lone object would, and are then held
    to that page by :func:`keep_on_page` measured on the component's union, so
    every member shares the one correction. Members are measured in spread
    coordinates, and a member drawn inside another page item is left to that
    item's own move.

    `a b c d` are never touched on any member; every move is `tx` alone. Every
    element whose `tx` changes here also gets :func:`reflect_path`, exactly as
    the standalone per-object path does -- an asymmetric decorative outline
    (the arrowhead itself, on a direction line) has to turn round as well as
    move, or it crosses to the far side of its sentence still pointing the
    way it pointed on the English page, which is worse than not moving at
    all.

    Returns whether anything moved, so the caller only counts a decision as
    carried out when it was.
    """
    from dataclasses import replace as _replace

    from pagebirdy.idml.rtl_plan import RTL_MIRROR, RTL_RESTRUCTURE

    equation = anchor.component_kind == "equation"
    if anchor.component_kind in ("containment", "equation"):
        # A form field and the backdrop drawn around it are separate spread
        # siblings, not one group's children: the same shape as a cluster.
        # So are the frames spelling out one equation -- each is placed on
        # the spread in its own right, with no shared transform to
        # piggyback on -- which is why an equation block takes the cluster
        # arithmetic: one delta, from the union, applied to every member.
        # What it does not take is `reflect_path`; see below.
        anchor = _replace(anchor, component_kind="cluster")

    if anchor.component_kind not in ("group", "cluster"):
        # `build_plan` always sets `component_kind` alongside `component` --
        # the same `component_context` supplies both -- so a decision that
        # has one without the other did not come from the real classifier.
        # The group/cluster branches below need to know which shape they are
        # moving; guessing (the `else` in each pair used to fall through to
        # "cluster" silently) would move an actual group's children by the
        # cluster's page-axis arithmetic instead of leaving the anchor's own
        # outline alone, which is a wrong move dressed up as a normal one.
        # Left untouched instead, loudly, which is this module's rule for
        # every case it cannot act on with confidence.
        logger.error(
            "rtl: component %r (anchor %r) has component_kind=%r, expected "
            "'group' or 'cluster' -- leaving every member untouched rather "
            "than guessing which arithmetic applies",
            anchor.component, anchor.object, anchor.component_kind)
        return False

    resolved = _resolve_members(members, index)
    if not resolved:
        return False

    if anchor.action == RTL_RESTRUCTURE:
        # Rearranged among themselves, about their own union: measured in the
        # space their transforms are written in, and never leaving that union,
        # so there is no page edge to hold them to.
        if anchor.component_kind == "group":
            movers = [(el, item_bounds(el)) for d, el, _ in resolved
                     if d.object != anchor.object]
        else:
            movers = [(el, item_bounds(el)) for _, el, _ in resolved]
        movers = [(el, box) for el, box in movers if box is not None]
        if not movers:
            return False
        axis = (min(b[0] for _, b in movers)
               + max(b[2] for _, b in movers)) / 2.0
        for el, box in movers:
            dx = 2.0 * axis - (box[0] + box[2])
            t = parse_transform(el.get("ItemTransform"))
            el.set("ItemTransform", format_transform(t[:4] + (t[4] + dx, t[5])))
            reflect_path(el)
        return True

    # RTL_REPOSITION / RTL_MIRROR.
    if anchor.component_kind == "group":
        anchor_entry = next(((el, box) for d, el, box in resolved
                             if d.object == anchor.object), None)
        if anchor_entry is None:
            return False
        el, box = anchor_entry
        axis = mirror_axis_for(box, extents, centre, axes)
        if axis is None:
            return False
        dx = keep_on_page(box, 2.0 * axis - (box[0] + box[2]), extents)
        t = parse_transform(el.get("ItemTransform"))
        el.set("ItemTransform", format_transform(t[:4] + (t[4] + dx, t[5])))
        reflect_path(el)
        if anchor.action == RTL_MIRROR:
            _mirror_arrangement(el, rigid, blocks)
        return True

    # A member drawn inside another page item -- a backdrop inside some other
    # group -- is carried by that item's own move; moving it here as well
    # would move it twice.
    resolved = [(d, el, box) for d, el, box in resolved if not _is_nested(el)]
    if not resolved:
        return False

    if anchor.action == RTL_MIRROR:
        # Every member reflected about the one page axis on its own: an arrow
        # lands on the far side of its sentence and the pair crosses the page,
        # in one step. The axis comes from the members' union, so members that
        # share a page share an axis, and the union is held to its page by one
        # shift shared by every member, so the arrangement survives.
        x0 = min(box[0] for _, _, box in resolved)
        x1 = max(box[2] for _, _, box in resolved)
        axis = mirror_axis_for((x0, 0.0, x1, 0.0), extents, centre, axes)
        if axis is None:
            return False
        reflected = 2.0 * axis - (x0 + x1)
        shift = keep_on_page((x0, 0.0, x1, 0.0), reflected, extents) - reflected
        for d, el, box in resolved:
            dx = 2.0 * axis - (box[0] + box[2]) + shift
            t = parse_transform(el.get("ItemTransform"))
            el.set("ItemTransform", format_transform(t[:4] + (t[4] + dx, t[5])))
            reflect_path(el)
            if _is(el, "Group") and d.object not in rigid:
                _mirror_arrangement(el, rigid, blocks)
        return True

    # Cluster: one shared delta from the union box, applied to every member.
    x0 = min(box[0] for _, _, box in resolved)
    x1 = max(box[2] for _, _, box in resolved)
    axis = mirror_axis_for((x0, 0.0, x1, 0.0), extents, centre, axes)
    if axis is None:
        return False
    dx = keep_on_page((x0, 0.0, x1, 0.0), 2.0 * axis - (x0 + x1), extents)
    for _, el, _ in resolved:
        t = parse_transform(el.get("ItemTransform"))
        el.set("ItemTransform", format_transform(t[:4] + (t[4] + dx, t[5])))
        # An equation block is the one composition whose pieces keep their
        # own drawing exactly as it is. A direction arrow has to turn round
        # when it crosses to the far side of its sentence; a long-division
        # bracket, a fraction bar or a "greater than" drawn as artwork means
        # the opposite of itself reversed, and it has not changed which side
        # of anything it is on -- the whole block moved, and nothing inside
        # it did.
        if not equation:
            reflect_path(el)
    return True


def _furniture_rules() -> frozenset:
    from pagebirdy.idml.rtl_rules import FURNITURE_RULES
    return FURNITURE_RULES


def _fixed_furniture(spread, by_object: dict, masters: dict) -> list:
    """Bounds, in `spread`'s coordinates, of every fixed template item on it.

    Two sources: furniture placed on the spread itself (a master item a page
    has overridden, the badge, the vertical title), and the items of each
    page's applied master, carried from the master page that sits where the
    page does -- which is where a master item prints.
    """
    boxes: list = []
    for el in spread:
        if not _is_page_item(el):
            continue
        d = by_object.get(el.get("Self"))
        if d is not None and d.rule in _furniture_rules() and not d.moves:
            box = item_bounds(el)
            if box is not None:
                boxes.append(box)
    pages = [pg for pg in spread if _is(pg, "Page")]
    for page, (px0, py0, px1, py1) in zip(pages, page_boxes(spread)):
        master = masters.get(page.get("AppliedMaster"))
        if master is None or page.get("ShowMasterItems") == "false":
            continue
        match = _master_page_for((px0, py0, px1, py1), master)
        if match is None:
            continue
        dx, dy = px0 - match[0], py0 - match[1]
        for el in master:
            if not _is_page_item(el):
                continue
            box = item_bounds(el)
            if box is None or min(box[2], match[2]) - max(box[0], match[0]) <= 0:
                continue
            boxes.append((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy))
    return boxes


def _master_page_for(page_box, master) -> tuple | None:
    """The page of `master` that prints under a document page at `page_box`.

    The master page sitting where the document page does; a one-page master
    applies wherever its page is used."""
    master_pages = page_boxes(master)
    match = next((mp for mp in master_pages
                  if abs(mp[0] - page_box[0]) <= _EDGE_TOL
                  and abs(mp[2] - page_box[2]) <= _EDGE_TOL), None)
    if match is None and len(master_pages) == 1:
        match = master_pages[0]
    return match


def _removed_master_items(page) -> set:
    """Master items `page` deleted its override of, so they do not print there.

    `OverrideList` pairs each overridden master item with the page item that
    replaced it, or with `n` when the page removed it outright."""
    tokens = (page.get("OverrideList") or "").split()
    return {tokens[i] for i in range(0, len(tokens) - 1, 2) if tokens[i + 1] == "n"}


def template_bands(spread, masters: dict) -> list:
    """Per page of `spread`, the side strips its applied master prints there.

    A strip is a master shape carrying no text that runs down most of the page
    at one outer edge -- the Family Letter's blue strip under the lesson badge
    and vertical title. Bounds are in `spread`'s coordinates. A page that hides
    its master items, or removed the strip, has none.
    """
    out: list = []
    pages = [pg for pg in spread if _is(pg, "Page")]
    for page, pbox in zip(pages, page_boxes(spread)):
        bands: list = []
        out.append(bands)
        master = masters.get(page.get("AppliedMaster"))
        if master is None or page.get("ShowMasterItems") == "false":
            continue
        match = _master_page_for(pbox, master)
        if match is None:
            continue
        removed = _removed_master_items(page)
        dx, dy = pbox[0] - match[0], pbox[1] - match[1]
        height, mid = match[3] - match[1], (match[0] + match[2]) / 2.0
        for el in master:
            if not _is_page_item(el) or el.get("Self") in removed \
                    or _carries_text(el):
                continue
            box = item_bounds(el)
            # Only what the master draws on the page under this one: a
            # facing master's other page carries its own template.
            if box is None or dominant_page(box, page_extents(master)) != \
                    page_boxes(master).index(match):
                continue
            covered = min(box[3], match[3]) - max(box[1], match[1])
            if covered < _SIDE_BAND_HEIGHT_SHARE * height:
                continue
            at_left = box[0] <= match[0] + _EDGE_TOL and box[2] < mid
            at_right = box[2] >= match[2] - _EDGE_TOL and box[0] > mid
            if at_left or at_right:
                bands.append((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy))
    return out


def on_template_band(box, page_box, bands) -> bool:
    """True when `box` reaches onto one of its page's template strips.

    An item spanning the page's whole width is a backdrop the strip is drawn
    over, not something set on the strip."""
    if box is None:
        return False
    if box[0] <= page_box[0] + _EDGE_TOL and box[2] >= page_box[2] - _EDGE_TOL:
        return False
    return any(min(box[2], bx1) - max(box[0], bx0) > _OVERLAP_EPS
               and min(box[3], by1) - max(box[1], by0) > _OVERLAP_EPS
               for bx0, by0, bx1, by1 in bands)


def apply_plan(documents: dict, plan) -> dict:
    """Carry out a transformation plan. The only code here that moves anything.

    There is no walk that decides anything. Every object is looked up by its
    `Self`, its decision is read, and exactly what that decision permits is
    done. An object with no decision is left untouched, which is the safe
    direction to fail in: a missing decision leaves the English geometry, never
    a mirrored guess.

    `a b c d` are never negated. Orientation changes go through
    :func:`reflect_graphic`, which composes a reflection onto the frame's
    *children* about the frame's own centre and so leaves the frame's own
    matrix and computed bounds alone; that check runs for every object with a
    decision, independently of its position action, because orientation and
    position are separate questions (a decorative photo inside an otherwise
    static component still needs its own mirror answer).

    A standalone object's `RTL_REPOSITION` reflects its own bounds about its
    own page, here. A component's members -- everything sharing a `.component`
    id -- are moved together by :func:`_move_component`, which the anchor's
    decision (the one member whose `rule` is not `"component.bound"`) drives;
    a bound member is otherwise skipped here entirely; see that function's
    docstring for why a group and a cluster need different arithmetic, and for
    both actions.
    """
    from pagebirdy.idml import rtl_plan as _plan

    by_object = plan.by_object()
    members_by_component: dict = {}
    for d in plan.decisions:
        if d.component is not None:
            members_by_component.setdefault(d.component, []).append(d)
    # Units whose inside is kept as drawn when a mirror reaches them: their own
    # decision is a rigid move, or they sit inside one. Read from each object's
    # own rule, since a group's child carries `component.bound` instead.
    rigid = frozenset(d.object for d in plan.decisions
                      if d.action in (_plan.RTL_REPOSITION, _plan.KEEP_GEOMETRY)
                      or d.rigid)
    # Object -> the equation block it belongs to. A block whose members sit
    # directly on a spread is moved by `_move_component`; a block drawn among
    # the children of a group that mirrors is moved by that group's own
    # `_mirror_arrangement`, which needs to know which of its children travel
    # together. Same membership, two places it can be carried out.
    blocks = {d.object: d.component for d in plan.decisions
              if d.component_kind == "equation" and d.component is not None}

    masters = {spread.get("Self"): spread
               for name, tree in documents.items()
               if name.startswith("MasterSpreads/")
               for spread in tree.iter("MasterSpread")}

    report = {"rtl_items_repositioned": 0, "rtl_graphics_mirrored": 0,
              "rtl_components_restructured": 0, "rtl_items_kept": 0,
              "rtl_geometry_locked": 0, "rtl_graphics_refused": 0}
    unclassified = 0
    # Frames whose picture has already been turned round, so a descendant
    # carrying its own MIRROR_GRAPHIC cannot turn it back; see :func:`_flip`.
    reflected: set = set()

    for name, tree in documents.items():
        if not name.startswith(("Spreads/", "MasterSpreads/")):
            continue
        for spread in tree.iter("Spread", "MasterSpread"):
            extents = page_extents(spread)
            if not extents:
                continue
            centre = spread_axis(spread)
            axes = content_axes(
                page_boxes(spread),
                _fixed_furniture(spread, by_object, masters))
            # Built once per spread so a cluster's members -- separate spread
            # siblings, not descendants an anchor's own subtree would yield --
            # can be found by `Self` regardless of where in the tree they sit.
            index = {el.get("Self"): el for el in spread.iter()
                     if _is_page_item(el)}
            moved_components: set = set()

            for el in spread.iter():
                if not _is_page_item(el):
                    continue
                self_id = el.get("Self")
                decision = by_object.get(self_id)
                if decision is None:
                    # Two shapes, both safe. The `<Spread>`/`<MasterSpread>`
                    # element itself carries an `ItemTransform` (usually
                    # identity) and so matches `_is_page_item` on every walk,
                    # but `rtl_features.collect` never treats the spread as a
                    # feature and no rule ever names it -- it is simply never
                    # a candidate for a decision. The other shape is a nested
                    # part of a parent that already has one -- a form
                    # control's own `<State>` children, in the one real book
                    # checked. Its `ItemTransform` is relative to that
                    # parent, so it is carried correctly when the parent
                    # moves, without needing a decision of its own. Neither
                    # is ever moved on its own account, only ever carried by
                    # a page item that is; logged below so this is a visible
                    # fact about the run rather than a silent gap in the
                    # plan's log.
                    unclassified += 1
                    continue

                if decision.component is not None and decision.position_bound:
                    # This member's position is not its own to decide -- it
                    # is carried out below, once, when the component's
                    # anchor is reached (`moved_components` makes that
                    # order-independent). Orientation is still an
                    # independent question per object, so that still runs.
                    if decision.new_orientation == _plan.MIRROR_GRAPHIC:
                        _flip(el, decision, reflected, report)
                    continue

                if decision.action == _plan.KEEP_GEOMETRY:
                    report["rtl_geometry_locked"] += 1
                    continue

                if decision.action in _plan.MOVING_ACTIONS:
                    if decision.component is not None:
                        moved = False
                        if decision.component not in moved_components:
                            moved = _move_component(
                                decision, members_by_component[decision.component],
                                index, extents, centre, rigid, axes, blocks)
                            moved_components.add(decision.component)
                        if moved:
                            if decision.action == _plan.RTL_RESTRUCTURE:
                                report["rtl_components_restructured"] += 1
                            else:
                                report["rtl_items_repositioned"] += 1
                    else:
                        box = item_bounds(el)
                        axis = (mirror_axis_for(box, extents, centre, axes)
                                if box is not None else None)
                        if axis is not None:
                            dx = keep_on_page(
                                box, 2.0 * axis - (box[0] + box[2]), extents)
                            t = parse_transform(el.get("ItemTransform"))
                            el.set("ItemTransform",
                                   format_transform(t[:4] + (t[4] + dx, t[5])))
                            reflect_path(el)
                            if (decision.action == _plan.RTL_MIRROR
                                    and _is(el, "Group")
                                    and self_id not in rigid):
                                _mirror_arrangement(el, rigid, blocks)
                            if decision.action == _plan.RTL_RESTRUCTURE:
                                report["rtl_components_restructured"] += 1
                            else:
                                report["rtl_items_repositioned"] += 1
                elif decision.action in (_plan.KEEP_POSITION,
                                         _plan.TEXT_ONLY_RTL,
                                         _plan.MIRROR_GRAPHIC):
                    report["rtl_items_kept"] += 1

                if decision.new_orientation == _plan.MIRROR_GRAPHIC:
                    _flip(el, decision, reflected, report)

    # An inline group lives in its story, not on a spread, and the text flow
    # already sets it against the line's new start edge. What is left for the
    # plan to change is the arrangement inside it -- a problem's text frame
    # crossing to the other side of its own box (`rtl_plan._sets_text_in_a_
    # box`) -- which is a reflection about the group's own centre and needs
    # no page to measure against.
    for name, tree in documents.items():
        if not name.startswith("Stories/"):
            continue
        for el in tree.iter("Group"):
            decision = by_object.get(el.get("Self"))
            if decision is None or decision.action != _plan.RTL_RESTRUCTURE:
                continue
            if _mirror_arrangement(el, rigid, blocks):
                report["rtl_components_restructured"] += 1

    if unclassified:
        logger.debug(
            "rtl: %d page item(s) visited with no plan decision -- see "
            "apply_plan's docstring for why that is safe", unclassified)
    if report["rtl_graphics_refused"]:
        logger.warning(
            "rtl: %d decision(s) asked for MIRROR_GRAPHIC on a frame that "
            "cannot be turned round; the plan and the log say those pictures "
            "were reversed and the document has them as drawn",
            report["rtl_graphics_refused"])

    return report


def _flip(el, decision, reflected: set, report: dict) -> bool:
    """Turn one frame's picture round, recording what actually happened.

    Two things this exists for beyond calling :func:`reflect_graphic`.

    A refusal is never silent. `reflect_graphic` declines a frame it cannot
    safely reverse -- a group, a frame setting type of its own, a rotated one --
    and a plan that asked for the flip anyway would otherwise print
    `MIRROR_GRAPHIC` in the log while the document shipped the picture as
    drawn. A promised transformation that does not happen has to be visible, or
    the plan stops being a record of what was done.

    And a picture is turned round once. `reflect_graphic` composes its mirror
    onto the frame's *children*, and `apply_plan` reaches those children later
    in the same walk; a descendant carrying its own `MIRROR_GRAPHIC` would flip
    the picture back with its geometry displaced. No book in the corpus has a
    nested pair, so this is a guard rather than a fix.
    """
    if any(a.get("Self") in reflected for a in el.iterancestors()):
        logger.debug("rtl: %s already turned round by an ancestor",
                     decision.object)
        return False
    if reflect_graphic(el):
        reflected.add(el.get("Self"))
        report["rtl_graphics_mirrored"] += 1
        return True
    report["rtl_graphics_refused"] += 1
    logger.warning(
        "rtl: %s (%s) asked for MIRROR_GRAPHIC via %s but cannot be turned "
        "round; left as drawn", decision.object, decision.type, decision.rule)
    return False


# ---- text direction --------------------------------------------------------


def is_rtl_bound(preferences) -> bool:
    """True when the document is already bound right-to-left.

    The guard against mirroring an RTL-authored source a second time.
    """
    if preferences is None:
        return False
    for el in preferences.iter():
        if _is(el, "DocumentPreference"):
            return el.get("PageBinding") == "RightToLeft"
    return False


def _character_style_index(documents: dict) -> tuple[dict, set]:
    """Character styles by id, and which of them a text run actually uses.

    A bullet's character style can name a font of its own, and turning a
    dingbat bullet round means moving that font with it -- but only while the
    style is bullet furniture and nothing else. A style applied to a run sets
    type a reader can see; see :func:`_substitute_bullet`.
    """
    styles: dict = {}
    used: set = set()
    for name, tree in documents.items():
        if not name.startswith(("Stories/", "Resources/")):
            continue
        for el in tree.iter():
            tag = _localname(el)
            if tag == "CharacterStyle":
                if el.get("Self"):
                    styles[el.get("Self")] = el
            elif tag == "CharacterStyleRange":
                applied = el.get("AppliedCharacterStyle")
                if applied:
                    used.add(applied)
    return styles, used


# How far a frame's x-axis may tilt off the page's before the alignment it
# carries stops being a reading-direction property and starts being a
# position. Well under any deliberate rotation and well over the float noise
# a 90-degree transform comes out of IDML with (`0 1.0000000000000004 -1 0`).
_AXIS_EPS = 1e-9


def _lies_along_the_page(transform) -> bool:
    """Does this transform leave the frame's x-axis along the page's own?

    A frame's `Justification` and its left/right indents are measured along
    the frame's x-axis, which a transform maps to `(a, b)`. When `b` is zero
    that axis is still the page's horizontal -- upright, or turned a half
    turn, or mirrored -- and text still runs across the page, so flipping
    left for right is the reading-direction change it appears to be. Any
    other `b` has swung the axis off the horizontal, and the same flip moves
    the text along the page's *vertical* instead.
    """
    return abs(transform[1]) <= _AXIS_EPS


def _turned_story_ids(documents: dict) -> frozenset:
    """Stories flowed by a frame whose x-axis has left the page's horizontal.

    Composed down the tree rather than read off each frame: rotation is just
    as often carried by an enclosing `<Group>`, and a frame with an identity
    transform of its own inside a turned group is turned on the page.

    A story with no frame at all -- one this document never places -- is not
    in the set, so nothing is held for it and the ordinary flip stands.
    """
    turned: set = set()

    def walk(node, parent):
        for el in node:
            if not _is_page_item(el):
                continue
            t = compose(parent, parse_transform(el.get("ItemTransform")))
            story = el.get("ParentStory")
            if story and not _lies_along_the_page(t):
                turned.add(story)
            walk(el, t)

    for name, tree in documents.items():
        if not name.startswith(("Spreads/", "MasterSpreads/")):
            continue
        for spread in tree.iter("Spread", "MasterSpread"):
            walk(spread, IDENTITY)
    return frozenset(turned)


def _paragraph_styles_by_id(documents: dict) -> dict:
    styles: dict = {}
    for name, tree in documents.items():
        if not name.startswith(("Resources/", "Stories/")):
            continue
        for el in tree.iter():
            if _localname(el) == "ParagraphStyle" and el.get("Self"):
                styles[el.get("Self")] = el
    return styles


def _effective_alignment(para, styles: dict, default: str | None) -> str | None:
    """What InDesign aligns this paragraph by, before this pass changes anything.

    Its own declaration, else the nearest style up the `BasedOn` chain that
    declares one, else the document default. The corpus's vertical lesson
    title declares none at any level, which is exactly why flipping the
    document default reaches it.
    """
    own = para.get("Justification")
    if own:
        return own
    seen: set = set()
    style = styles.get(para.get("AppliedParagraphStyle"))
    while style is not None and id(style) not in seen:
        seen.add(id(style))
        declared = style.get("Justification")
        if declared:
            return declared
        props = style.find("./{*}Properties")
        based = _property(props, "BasedOn") if props is not None else None
        style = styles.get((based.text or "").strip()) if based is not None else None
    return default


def _hold_turned_alignment(documents: dict, preferences, turned: frozenset) -> list:
    """`(paragraph, alignment)` for every paragraph in a turned frame.

    Read before this pass flips anything, and written back after it, so that
    a paragraph inheriting its alignment cannot be moved by the flip applied
    to whatever it inherits from. Only alignments the flip would actually
    have moved are held: a centred paragraph is unaffected either way, and a
    binding-relative one resolves against `PageBinding`, which this pipeline
    never flips.
    """
    if not turned:
        return []
    default = None
    if preferences is not None:
        for el in preferences.iter():
            if _localname(el) == "TextDefault":
                default = el.get("Justification")
                break
    styles = _paragraph_styles_by_id(documents)
    held: list = []
    for name, tree in documents.items():
        if not name.startswith("Stories/"):
            continue
        for story in tree.iter("Story"):
            if story.get("Self") not in turned:
                continue
            for para in story.iter("{*}ParagraphStyleRange"):
                alignment = _effective_alignment(para, styles, default)
                if alignment in _ALIGN_FLIP:
                    held.append((para, alignment))
    return held


def _turned_story_documents(documents: dict, turned: frozenset) -> frozenset:
    """The `Stories/*.xml` holding a turned story, by document name.

    Resolved by reading each story's own `Self` rather than by assuming the
    `Story_<id>.xml` filename, which is a convention rather than a guarantee.
    """
    if not turned:
        return frozenset()
    return frozenset(
        name for name, tree in documents.items()
        if name.startswith("Stories/")
        and any(story.get("Self") in turned for story in tree.iter("Story")))


def set_text_direction(documents: dict, preferences=None, fonts=None) -> int:
    """Turn stories right-to-left and flip absolute paragraph alignment.

    Purely typographic -- it moves no geometry, and it does not touch
    `PageBinding`. Binding governs which page a reader turns to next and,
    critically, which side of a spread each page renders on -- flipping it
    is what used to turn page 84/85 into a spread displaying 85 on the left
    and 84 on the right, exactly the "flipped pages" a reviewer comparing
    page numbers against the English source does not want. This pipeline
    leaves every page exactly where the English document put it and changes
    only how the *text* on it reads.

    Alignment is flipped only where it is absolute (`LeftAlign`/`RightAlign`);
    binding-relative and centred alignments are left alone -- correctly:
    `AwayFromBindingSide` etc. resolve against whatever `PageBinding` already
    says, unmoved.

    And only in a frame whose x-axis still lies along the page's. Alignment
    and the left/right indents are measured along the frame's *own* x-axis,
    so in an upright frame flipping them is the reading-direction change it
    appears to be -- but in a frame turned 90 degrees that axis runs down the
    page, and the same flip walks the text from one end of the column to the
    other *vertically*. That is a position, not a direction: it is how the
    vertical lesson title, which declares no alignment at any level and so
    takes the document default this pass flips, used to slide from the top of
    its side margin to the bottom with its `ItemTransform` never changing.
    A paragraph in a turned frame therefore keeps the alignment and indents
    the source resolved to, and still gets every genuine direction change --
    `ParagraphDirection`, digits, composer, bullet. Position and text are
    independent fields, and this is where they had been conflated. See
    :func:`_lies_along_the_page` and :func:`_hold_turned_alignment`.

    `fonts` is `Resources/Fonts.xml`, wanted only because turning a one-way
    dingbat bullet round moves it to another face, and a face the package never
    declares is a face InDesign substitutes on open.
    """
    changed = 0
    character_styles, styled_runs = _character_style_index(documents)
    bullet_faces = _bullet_character_styles(documents)

    # Read before anything below flips: a paragraph in a turned frame keeps
    # the alignment and indents it has, because in that frame both are
    # measured along an axis that is not the page's horizontal. See
    # :func:`_lies_along_the_page`.
    turned = _turned_story_ids(documents)
    turned_documents = _turned_story_documents(documents, turned)
    held_alignment = _hold_turned_alignment(documents, preferences, turned)

    if preferences is not None:
        for el in preferences.iter():
            name = _localname(el)
            if name == "StoryPreference":
                el.set("StoryDirection", _RTL)
                changed += 1
            elif name == "TextDefault":
                # What every paragraph that overrides nothing inherits. Left
                # Latin and left-aligned it quietly re-imposes both on the bulk
                # of the document, however many paragraph styles were flipped.
                el.set("ParagraphDirection", _RTL)
                el.set("DigitsType", _DIGITS)
                flipped = _ALIGN_FLIP.get(el.get("Justification"))
                if flipped:
                    el.set("Justification", flipped)
                _swap_indents(el)
                _set_world_ready_composer(el)
                changed += _mirror_bullet(el, character_styles, styled_runs,
                                          fonts, bullet_faces)
                changed += 1

    for name, tree in documents.items():
        if not name.startswith(("Stories/", "Resources/")):
            continue
        if tree is preferences:
            # Preferences is handed in explicitly *and* lives under
            # `Resources/`. Letting the loop reach it too would re-decide what
            # the pass above already decided, and inflate the count with work
            # that never happened.
            continue
        for el in tree.iter():
            tag = _localname(el)
            if tag == "StoryPreference":
                el.set("StoryDirection", _RTL)
                changed += 1
            elif tag in ("Table", "TableStyle"):
                # A table's columns are ordered by its own direction, not the
                # story's. Left alone, the header column stays on the left
                # while every cell's text runs the other way.
                #
                # `TableStyle` carries the same property and is where a table
                # that overrides nothing gets it, exactly as `ParagraphStyle`
                # is for a paragraph: flipping only the tables written inline
                # leaves every styled table still reading left to right.
                el.set("TableDirection", _RTL)
                changed += 1
            elif tag in ("ParagraphStyleRange", "ParagraphStyle"):
                el.set("ParagraphDirection", _RTL)
                if name not in turned_documents:
                    flipped = _ALIGN_FLIP.get(el.get("Justification"))
                    if flipped:
                        el.set("Justification", flipped)
                    _swap_indents(el)
                _set_world_ready_composer(el)
                el.set("DigitsType", _DIGITS)
                changed += _mirror_bullet(el, character_styles, styled_runs,
                                          fonts, bullet_faces)
                changed += 1

    # Last, so that a paragraph inheriting its alignment is not left following
    # a style or a document default this pass has just flipped for everyone
    # else. Writing the value the source resolved to makes the inheritance
    # explicit rather than changing what it says.
    for para, alignment in held_alignment:
        para.set("Justification", alignment)
    return changed


# Every indent pair measured from an absolute edge. The paragraph's own
# indents move a bullet's hanging indent across with the text; the rule indents
# move the rule drawn above or below it. `LH Investigate` sets
# `RuleBelowLeftIndent="169"` so its rule starts clear of the badge beside it --
# left unswapped, the badge moves right and the rule runs straight through it.
_INDENT_PAIRS = (
    ("LeftIndent", "RightIndent"),
    ("RuleAboveLeftIndent", "RuleAboveRightIndent"),
    ("RuleBelowLeftIndent", "RuleBelowRightIndent"),
    # The shading behind a callout paragraph and the border drawn around it are
    # boxes measured from the text edges, exactly as the rule indents are. Left
    # unswapped they keep hugging the edge the text has just left, so a tinted
    # panel inset 18pt on one side sits 18pt proud on the other.
    ("ParagraphShadingLeftOffset", "ParagraphShadingRightOffset"),
    ("ParagraphBorderLeftOffset", "ParagraphBorderRightOffset"),
    ("ParagraphBorderLeftLineWeight", "ParagraphBorderRightLineWeight"),
    ("ParagraphBorderLeftLineColor", "ParagraphBorderRightLineColor"),
    ("ParagraphBorderLeftLineTint", "ParagraphBorderRightLineTint"),
    ("ParagraphBorderLeftLineType", "ParagraphBorderRightLineType"),
)

# A rounded corner on one side of a shading or border box travels with the box.
# The top-left/top-right and bottom-left/bottom-right corners exchange; the
# option and its radius have to move together or a `Rounded` corner ends up
# with the square corner's 1pt radius.
_CORNER_PAIRS = tuple(
    (f"Paragraph{box}{v}Left{suffix}", f"Paragraph{box}{v}Right{suffix}")
    for box in ("Shading", "Border")
    for v in ("Top", "Bottom")
    for suffix in ("CornerOption", "CornerRadius")
)


def _swap_indents(el) -> None:
    """Exchange each left/right pair a paragraph measures from an edge.

    Indents, the rule indents that keep a rule clear of a badge beside it, and
    the shading/border box drawn around the paragraph -- all measured from the
    left or right text edge, so all of them move with the text.

    `FirstLineIndent` is deliberately untouched: it is measured from the
    paragraph's *leading* edge, which `ParagraphDirection` has already moved,
    and flipping it as well would mirror it twice and turn a hanging indent
    back into a first-line one.
    """
    for left_name, right_name in _INDENT_PAIRS + _CORNER_PAIRS:
        left, right = el.get(left_name), el.get(right_name)
        if left is None and right is None:
            continue
        # Only write back what the source actually declared -- inventing a "0"
        # where it was silent overrides what the paragraph style supplied, and
        # a one-sided indent has to *move* edges rather than gain a twin.
        if right is not None:
            el.set(left_name, right)
        elif left_name in el.attrib:
            del el.attrib[left_name]
        if left is not None:
            el.set(right_name, left)
        elif right_name in el.attrib:
            del el.attrib[right_name]


def _bullet_character_styles(documents: dict) -> dict:
    """For each style declaring a bullet, every character style that draws it.

    A paragraph style built `BasedOn` another inherits its `BulletChar` without
    declaring one of its own -- and may still override `BulletsCharacterStyle`,
    which is exactly what `_Family Letter:FL Direction line (Activity)` does in
    the sample books, naming an orange face where its parent names a blue one.

    Substituting the bullet on the style that *declares* it therefore reaches
    only one of the faces the new codepoint is drawn from. Every derived style
    keeps pointing at a character style still set in the dingbat face, which
    has no glyph at the substituted codepoint, and prints a missing-glyph box
    precisely where the arrow was -- in the source's own colour, which is what
    made it look like a deliberate orange square.

    Keyed by the declaring element itself, so a bullet's whole family of faces
    is known before any of them is retargeted.
    """
    styles: dict = {}
    for name, tree in documents.items():
        if not name.startswith(("Resources/", "Stories/")):
            continue
        for el in tree.iter():
            if _localname(el) == "ParagraphStyle" and el.get("Self"):
                styles[el.get("Self")] = el

    def inherited(el, name: str):
        """The nearest ancestor declaring `name`, and the declaration."""
        seen: set = set()
        while el is not None and id(el) not in seen:
            seen.add(id(el))
            props = el.find("./{*}Properties")
            if props is None:
                return None, None
            found = _property(props, name)
            if found is not None:
                return el, found
            based = _property(props, "BasedOn")
            el = styles.get((based.text or "").strip()) if based is not None else None
        return None, None

    faces: dict = {}
    for style in styles.values():
        owner, _ = inherited(style, "BulletChar")
        if owner is None:
            continue
        _, applied = inherited(style, "BulletsCharacterStyle")
        name = (applied.text or "").strip() if applied is not None else ""
        faces.setdefault(owner, set())
        if name:
            faces[owner].add(name)
    return faces


def _mirror_bullet(el, character_styles=None, styled_runs=(), fonts=None,
                   bullet_faces=None) -> int:
    """Turn a directional bullet round to face the text.

    A bullet whose mirror image is a real codepoint in the same block is turned
    where it stands. A one-way dingbat arrow is turned by moving it to a face
    that has a mirrored glyph -- what `_BULLET_SUBSTITUTE` names and
    :func:`_substitute_bullet` carries out. A bullet neither table knows is
    left as the source drew it, glyph and bullet font intact.

    Only a `BulletCharacterValue` that really is a codepoint is touched:
    `GlyphWithFont` stores a glyph index into a particular face, and reading
    that as a codepoint swaps one unrelated glyph for another.
    """
    bullet = el.find(".//{*}BulletChar")
    if bullet is None:
        return 0
    if (bullet.get("BulletCharacterType") or "UnicodeOnly").startswith("Glyph"):
        return 0
    try:
        value = int(bullet.get("BulletCharacterValue"))
    except (TypeError, ValueError):
        return 0

    substitute = _BULLET_SUBSTITUTE.get(value)
    if substitute is not None:
        return _substitute_bullet(bullet, substitute, character_styles or {},
                                  styled_runs, fonts, bullet_faces or {})

    mirrored = _BULLET_MIRROR.get(value)
    if mirrored is None:
        # No counterpart in this glyph's own face, and no face named that has
        # one. The bullet keeps the character and the font the source gave it:
        # a rightwards arrow is still the pointer the author chose, where a
        # missing-glyph box is nothing at all.
        return 0
    bullet.set("BulletCharacterValue", str(mirrored))
    return 1


def _property(props, name: str):
    """The `<Name type="string">value</Name>` child of a `Properties` block."""
    return next((c for c in props if _localname(c) == name), None)


def _set_property(props, after, name: str, value: str) -> None:
    """Set such a child, adding it beside `after` when the block has none."""
    el = _property(props, name)
    if el is None:
        el = etree.Element(name)
        el.set("type", "string")
        props.insert(list(props).index(after) + 1, el)
    el.text = value


def _substitute_bullet(bullet, mirrored: int, character_styles: dict,
                       styled_runs, fonts, bullet_faces: dict | None = None) -> int:
    """Turn a bullet round by moving it to a face that has the mirrored glyph.

    Two things name the bullet's font and both have to move, or the new
    codepoint is drawn from a face with no such glyph and the arrow comes out
    a missing-glyph box. `BulletsFont`/`BulletsFontStyle` is the font the
    bullet character is set in. `BulletsCharacterStyle` is the style carrying
    its colour and size, and a character style naming a font of its own
    overrides the first.

    *Every* character style that draws this bullet moves, not only the one
    named beside it: a style based on this one inherits the codepoint and can
    still name a face of its own, and one left behind prints the box the
    substitution exists to prevent. `bullet_faces` is what
    :func:`_bullet_character_styles` resolved.

    Retargeting a shared style is only safe while it is bullet furniture.
    Applied to a run as well it sets type a reader can see, and moving its font
    would restyle that text, so there the bullet is left exactly as authored --
    the same trade the substitution exists to avoid, taken the other way
    because a wrong arrow beats wrong type. The trade is taken for the family
    as a whole: half a substitution is the box again, in the one style that
    could not follow.
    """
    family, style = _BULLET_FALLBACK
    props = bullet.getparent()

    names = set((bullet_faces or {}).get(props.getparent(), ()))
    applied = _property(props, "BulletsCharacterStyle")
    if applied is not None and (applied.text or "").strip():
        names.add((applied.text or "").strip())

    retarget = []
    for name in sorted(names):
        scoped = character_styles.get(name)
        if scoped is None:
            continue
        font = scoped.find("./{*}Properties/{*}AppliedFont")
        if font is None or (font.text or "").strip() == family:
            continue
        if scoped.get("Self") in styled_runs:
            return 0
        retarget.append((scoped, font))
    for scoped, font in retarget:
        font.text = family
        scoped.set("FontStyle", style)

    bullet.set("BulletCharacterValue", str(mirrored))
    _set_property(props, bullet, "BulletsFontStyle", style)
    _set_property(props, bullet, "BulletsFont", family)
    register_font(fonts, family, (style,))
    return 1


def _set_world_ready_composer(el) -> None:
    """Move this paragraph onto the World-Ready composer.

    A paragraph that names no composer inherits one, so silence is not
    neutral: it is how a run reaches InDesign with the Latin composer still in
    force. An already-World-Ready value is left as it is.
    """
    current = el.get("Composer")
    if current is None:
        el.set("Composer", _DEFAULT_COMPOSER)
    elif current in _COMPOSER_WORLD_READY:
        el.set("Composer", _COMPOSER_WORLD_READY[current])


# ---- keeping left-to-right content left-to-right ----------------------------

# What a run has to hold before it is worth pinning. A run of punctuation or
# spaces has no direction of its own and takes one from its neighbours, so
# pinning it would break the line it sits in rather than protect it; see
# `script.is_ltr_only`.
_LTR = "LeftToRightDirection"


def preserve_ltr_content(documents: dict) -> int:
    """Pin runs that read left-to-right so bidi cannot reorder them.

    An Arabic paragraph is not wholly Arabic. It carries `10x + 15y = 150`, a
    URL, a file name, a variable, a page reference -- and each of those has to
    keep the order it was written in.

    The Unicode bidi algorithm gets the *letters and digits* right on its own,
    which is why `set_text_direction` leaves `CharacterDirection` at its
    default and lets runs inherit the paragraph's direction. What it does not
    get right is the neutrals *between* them. In an RTL paragraph the `+` and
    `=` in `10x + 15y = 150` are resolved against the paragraph's direction,
    not the expression's, so the operators migrate and the equation prints in
    pieces; a trailing `.` or `)` jumps to the far end of the line the same
    way.

    Declaring the run itself left-to-right resolves those neutrals inside the
    run, where they belong. Only a run that reads left-to-right and holds
    nothing that does not is pinned: a run with a single Arabic letter in it is
    left alone, because pinning that would be the mirror image of the bug.

    Returns the number of runs pinned.
    """
    from pagebirdy import script as _script

    pinned = 0
    for name, tree in documents.items():
        if not name.startswith("Stories/"):
            continue
        for el in tree.iter():
            if _localname(el) != "CharacterStyleRange":
                continue
            if el.get("CharacterDirection") is not None:
                # The source already decided this run's direction. Overriding a
                # deliberate declaration is not this function's business.
                continue
            text = "".join(_run_text(c) for c in el.iter()
                           if _localname(c) == "Content")
            if not _script.is_ltr_only(text):
                continue
            el.set("CharacterDirection", _LTR)
            pinned += 1
    return pinned


def _run_text(content) -> str:
    """Every piece of text in a `<Content>`, markers and breaks included.

    A run is not always plain text -- InDesign parks prose in `.text` and in
    each child's `.tail` around `<Br/>` and `<?ACE?>` markers -- so reading
    only `.text` would judge a run's direction from a fraction of it.
    """
    parts = [content.text or ""]
    parts.extend(child.tail or "" for child in content)
    return "".join(parts)


# ---- mirror-sensitive item properties --------------------------------------


def _property_owner_index(documents: dict, plan) -> dict:
    """Element -> the decision of the nearest page item enclosing it.

    A side-naming property is a property *of an object*, so whether it may be
    flipped is that object's decision to make. This walks the spreads once and
    hands every descendant the decision of the nearest page item above it, so
    a wrap offset on a frame and an anchored-object setting nested inside it
    both answer to the same decision.
    """
    by_object = plan.by_object()
    # A cluster member's position is its component's to decide (`position_
    # bound`), so its own decision reads `KEEP_POSITION` however far the
    # cluster carried it. Answering to that left the Game Time graphic under
    # RCM07 L03's gamepad with its wrap gap facing the page margin while the
    # text met its bare edge.
    anchors = {d.component: d for d in plan.decisions
               if d.component is not None and not d.position_bound}
    owners: dict = {}

    def walk(node, decision):
        for el in node:
            here = decision
            if _is_page_item(el):
                own = by_object.get(el.get("Self"))
                if own is not None and own.position_bound:
                    own = anchors.get(own.component, own)
                # A page item carried by a moving ancestor -- a group's child,
                # a picture in its frame -- changed sides as surely as the
                # ancestor did, though its own decision says it did not move
                # on its own account.
                if own is None:
                    here = decision
                elif decision is not None and decision.moves and not own.moves:
                    here = decision
                else:
                    here = own
            # Keyed by the element, not `id(el)`: lxml hands out a fresh proxy
            # each time a node is reached, and once one is collected its id is
            # reused by another -- holding the element keeps its proxy, and so
            # its identity, alive for the lookup below.
            owners[el] = here
            walk(el, here)

    for name, tree in documents.items():
        if not name.startswith(("Spreads/", "MasterSpreads/")):
            continue
        for spread in tree.iter("Spread", "MasterSpread"):
            walk(spread, None)
    return owners


def mirror_item_properties(documents: dict, plan=None, anchors: bool = True) -> int:
    """Flip the properties that name a side rather than a position.

    The geometric mirror moves a frame's `tx`; it cannot know that the frame
    also carries a wrap contour biased to one side, an inset that is wider on
    the left, or an inline icon offset to the right of its text. Each of those
    keeps pointing the old way after the move, which is how a mirrored page
    still reads as half-mirrored.

    Runs over stories, spreads and resources alike: wrap and inset live on page
    items in `Spreads/`, anchored-object settings live inside the story that
    owns the inline object -- and every one of the three also has a default in
    `Resources/`. Most frames override nothing, so an object style whose wrap
    contour, inset or anchor still names the old side quietly re-imposes it on
    the bulk of the document however many frames were mirrored inline. This is
    the same reason `apply_rtl` pulls `Resources/Styles.xml` into the
    text-direction pass, one level up from paragraphs.

    **With a `plan`, this is decided per object, not per document.** All of the
    above holds while every item moves, which is what the legacy whole-page
    mirror does -- and `plan=None` keeps exactly that behaviour for the targets
    still using it. Under the semantic engine almost nothing moves, so flipping
    every side-naming property in the package is no longer a matching
    correction but an independent transformation nobody asked for. Measured on
    one book: zero items repositioned and seventy-four properties flipped,
    including the wrap offset of a frame the plan had locked `KEEP_GEOMETRY`
    precisely so its diagram would not be disturbed -- the offset moved, and
    the diagram that had not moved took its bite out of the wrong side of every
    line of type beside it.

    **But not every side-naming property names a side of the page.** Two kinds
    live here and they follow different things:

    * A wrap contour (`TextWrapSide`, `TextWrapOffset`) and a frame inset
      (`InsetSpacing`) are measured against the page and the frame. They are a
      correction that belongs with a *move*, so they flip only where the owning
      object actually changed sides, and a `Resources/` default -- inherited by
      the whole document -- is left alone.
    * An anchored object's settings (`AnchorXoffset`, `HorizontalAlignment`,
      `AnchorPoint`) are measured against the *text*. An inline badge pinned to
      the corner where its sentence begins has to change corner when the
      sentence changes direction, and it has to do so whether or not one page
      item moved: the thing that moved under it is the text. Gating these on
      movement left every problem number anchored `BottomRightAnchor` in a
      right-to-left paragraph, which prints it at the end of the line it is
      supposed to introduce.

    So these flip with the story's direction, not with the page geometry, and
    that is why this pass still reads `Stories/` and `Resources/` even when a
    plan is driving the rest of it.
    """
    changed = 0
    owners = _property_owner_index(documents, plan) if plan is not None else {}
    by_object = plan.by_object() if plan is not None else {}
    for name, tree in documents.items():
        if not name.startswith(("Stories/", "Spreads/", "MasterSpreads/",
                                "Resources/")):
            continue
        for el in tree.iter():
            tag = _localname(el)
            if plan is not None and tag != "AnchoredObjectSetting":
                # A wrap contour and a frame inset name a side of the *page*:
                # they are a correction that belongs with a move, so they flip
                # only where the owning object actually changed sides. An
                # object with no decision -- a `Resources/` default inherited
                # by the whole document, or anything outside the spreads -- is
                # left alone, since flipping a default to suit the few objects
                # that moved re-imposes the old side on everything that did
                # not.
                owner = owners.get(el)
                if owner is None or not owner.moves:
                    continue
            if tag == "TextWrapPreference":
                flipped = _WRAP_SIDE_FLIP.get(el.get("TextWrapSide"))
                if flipped:
                    el.set("TextWrapSide", flipped)
                    changed += 1
            elif tag == "TextWrapOffset":
                if plan is not None and _keeps_its_inside(el, by_object):
                    changed += _mirror_wrap_offset(el)
                else:
                    changed += _swap_attrs(el, "Left", "Right")
            elif tag == "InsetSpacing":
                changed += _mirror_inset(el)
            elif tag == "AnchoredObjectSetting" and anchors:
                changed += _mirror_anchor(el)
    return changed


def mirror_anchored_object_settings(documents: dict) -> int:
    """Flip every inline object's own text-relative position to match its
    story's new direction. Returns how many attributes changed.

    `mirror_item_properties` already contains this correction (`_mirror_
    anchor`, applied to `AnchoredObjectSetting`) and, per that function's own
    docstring, applies it unconditionally even under a geometry plan: an
    anchor's `AnchorXoffset`, `HorizontalAlignment` and `AnchorPoint` are
    measured against the *text*, not the page, so "the thing that moved
    under it is the text" whether or not the object it sits on is one the
    geometry engine repositioned. `apply_rtl` does build a plan now --
    `idml.rtl_rules`' rule table repositions, restructures or mirrors the
    categories of object it recognises, for every RTL target -- but that
    does not change why this correction is safe to call unconditionally:
    unlike the wrap-contour and inset corrections in `mirror_item_properties`,
    which *are* gated on a page item actually having moved, precisely to
    avoid re-flipping a frame that stayed put, this one was never gated on
    any object's movement in the first place. This function runs only that
    one correction, so it is safe to call for every RTL target regardless of
    what the geometry engine did to the object underneath it.

    Left uncorrected, a problem-number badge anchored `BottomRightAnchor` /
    `LeftAlign` -- the right corner for a paragraph that opened left-to-right
    -- keeps sitting at the end of the line it was meant to introduce, once
    `set_text_direction` turns that same paragraph right-to-left: the number
    reads as trailing its sentence instead of leading it.
    """
    changed = 0
    for name, tree in documents.items():
        if not name.startswith(("Stories/", "Spreads/", "MasterSpreads/",
                                "Resources/")):
            continue
        for el in tree.iter():
            if _localname(el) == "AnchoredObjectSetting":
                changed += _mirror_anchor(el)
    return changed


def _keeps_its_inside(el, by_object: dict) -> bool:
    """True when the page item owning `el` moves without its inside mirroring.

    A frame's picture is turned round only on `MIRROR_GRAPHIC`, and a group's
    arrangement is reflected only on a non-rigid `RTL_MIRROR`; anything else
    that moves carries its content across the page exactly as drawn.
    """
    from pagebirdy.idml import rtl_plan as _plan

    item = next((a for a in el.iterancestors() if _is_page_item(a)), None)
    if item is None:
        return False
    own = by_object.get(item.get("Self"))
    if own is None or own.flips:
        return False
    if _is(item, "Group"):
        return own.rigid or own.action in (_plan.RTL_REPOSITION, _plan.KEEP_GEOMETRY)
    return True


def _mirror_wrap_offset(el) -> int:
    """Mirror a wrap offset around content that is not itself mirrored.

    A positive offset is a gap kept between the object and the type beside
    it: it belongs to the layout and crosses to the mirrored side. A negative
    one reaches *into* the frame, over margin the picture has on that side --
    the RCM07 L03 gamepad photo's `Left=-12` -- and that margin is still on the
    same side of a picture that was not turned round. Carrying the inset across
    let type 12pt into the photograph itself.
    """
    try:
        left, right = float(el.get("Left")), float(el.get("Right"))
    except (TypeError, ValueError):
        return 0
    new_left = max(right, 0.0) + min(left, 0.0)
    new_right = max(left, 0.0) + min(right, 0.0)
    if (new_left, new_right) == (left, right):
        return 0
    el.set("Left", _num(new_left))
    el.set("Right", _num(new_right))
    return 1


def _swap_attrs(el, a: str, b: str) -> int:
    """Exchange two attributes, writing nothing where the source was silent."""
    va, vb = el.get(a), el.get(b)
    if va is None or vb is None:
        return 0
    if va == vb:
        return 0
    el.set(a, vb)
    el.set(b, va)
    return 1


def _mirror_inset(el) -> int:
    """Swap the left and right members of a four-part frame inset.

    `InsetSpacing` is written two ways. As `type="unit"` it is a single value
    already applying to all four sides, and a mirror cannot change it. As
    `type="list"` it is four `ListItem`s in `top left bottom right` order, and
    only the middle pair moves.
    """
    items = [c for c in el if _localname(c) == "ListItem"]
    if len(items) != 4:
        return 0
    if items[1].text == items[3].text:
        return 0
    items[1].text, items[3].text = items[3].text, items[1].text
    return 1


def _mirror_anchor(el) -> int:
    """Reflect an anchored object across its anchor.

    `AnchorXoffset` on a side-aligned anchor is measured *outward from that
    side* (calibrated in InDesign 2026: a positive offset moves a `LeftAlign`
    object left of the frame's left edge and a `RightAlign` one right of its
    right edge), so flipping the side already mirrors it and the value keeps
    its sign. Negating it too pushed every problem-number badge -- `LeftAlign`,
    `-16`, sitting in its paragraph's hanging indent -- 16pt outside the
    frame's new right edge. Only a centre-aligned offset, measured rightwards,
    negates. An anchor naming no alignment inherits one; in every sample book
    that is `LeftAlign`, which is also InDesign's default.

    `HorizontalAlignment` names an absolute side and flips, and `AnchorPoint`
    -- the corner of the object pinned to the anchor -- flips with it. Moving
    the anchor without moving the corner it holds re-pins the object by its
    old edge, which slides it sideways by its own width: a figure anchored
    `TopLeftAnchor` lands a frame-width away from everything mirrored around
    it, often over the gutter and onto the facing page. The vertical offset is
    untouched: a mirror about a vertical axis does not move it.
    """
    changed = 0
    offset = el.get("AnchorXoffset")
    side_measured = el.get("HorizontalAlignment", "LeftAlign") in ("LeftAlign", "RightAlign")
    if offset is not None and not side_measured:
        try:
            value = float(offset)
        except ValueError:
            value = None
        if value is not None and value != 0.0:
            el.set("AnchorXoffset", _num(-value))
            changed += 1
    flipped = _ALIGN_FLIP.get(el.get("HorizontalAlignment"))
    if flipped:
        el.set("HorizontalAlignment", flipped)
        changed += 1
    corner = _ANCHOR_POINT_FLIP.get(el.get("AnchorPoint"))
    if corner:
        el.set("AnchorPoint", corner)
        changed += 1
    return changed


# ---- fonts -----------------------------------------------------------------


def register_font(fonts, family: str | None,
                  styles: tuple[str, ...] = ("Regular",)) -> int:
    """Declare `family` in `Resources/Fonts.xml` if it is not already there.

    `package.apply` writes the target language's face onto every rewritten run
    as `AppliedFont`, but naming a family the package never declares is not
    enough: InDesign opens the document with a missing-font warning and
    substitutes a face, which for an Arabic run means the glyphs are drawn from
    something that has none of them. Registering the family is what makes the
    `AppliedFont` resolve.

    `styles` names the faces to declare. A family declared with `Regular` alone
    is a family with no bold: `package.apply` maps each run's inherited weight
    onto one of these, so a `Bold` it names and the package never declares gets
    the same missing-style substitution the family registration exists to
    prevent. The two lists come from the same place --
    `languages.Language.idml_font_styles` -- so they cannot drift apart.

    The entry is deliberately minimal -- family, name and PostScript name. The
    rest of what InDesign writes here (version strings, Typekit ids, install
    status) describes the authoring machine's copy of the font, not the
    document, and InDesign fills it in on open.
    """
    if fonts is None or not family:
        return 0
    for el in fonts.iter():
        if _localname(el) == "FontFamily" and el.get("Name") == family:
            return 0

    root = fonts if _localname(fonts) != "Fonts" else fonts
    slug = "".join(ch for ch in family if ch.isalnum())
    fam = etree.SubElement(root, "FontFamily")
    fam.set("Self", f"pagebirdy{slug}")
    fam.set("Name", family)
    for style in styles or ("Regular",):
        face = etree.SubElement(fam, "Font")
        face.set("Self", f"pagebirdy{slug}Font{style.replace(' ', '')}")
        face.set("FontFamily", family)
        face.set("Name", f"{family} {style}")
        # InDesign's own convention: the family with its spaces removed, a
        # hyphen, then the style with its spaces removed -- "AdobeArabic-Bold".
        face.set("PostScriptName",
                 f"{family.replace(' ', '')}-{style.replace(' ', '')}")
        face.set("FontStyleName", style)
        face.set("Status", "Installed")
    return 1


# ---- the stage -------------------------------------------------------------

# Neither is parsed on ingest; `IdmlPackage.document` fetches them on demand so
# an LTR job re-serialises nothing it never touched.
PREFERENCES = "Resources/Preferences.xml"
STYLES = "Resources/Styles.xml"
FONTS = "Resources/Fonts.xml"


def apply_rtl(pkg, *, document: str, language: str, idml_font: str | None = None,
              font_styles: tuple[str, ...] = ("Regular",),
              keep_upright: tuple = ()) -> dict:
    """Turn a translated IDML package right-to-left. Returns report counters.

    The one call the pipeline makes for an RTL target. Reading direction
    changes for every story, via :func:`set_text_direction` (stories,
    paragraphs, tables, and the typographic properties that travel with
    them: alignment, indents, a paragraph's shading/border box, and a
    directional bullet glyph substituted for its mirror image) and
    :func:`preserve_ltr_content` (pinning runs that must keep reading
    left-to-right -- an equation, a URL, a file name -- inside a paragraph
    that otherwise flows right to left).

    `Resources/Styles.xml` is pulled in alongside the preferences because most
    frames never override their paragraph style: flipping only the alignment
    written inline in the stories leaves everything that inherits from `Body`
    still left-aligned, however many runs were rewritten.

    No run is ever forced *right*-to-left. Forcing runs right-to-left would
    reorder the contents of `10x + 15y = 150`. What :func:`preserve_ltr_content`
    does is the opposite and only where it is safe: a run holding nothing but
    left-to-right content is pinned left-to-right, so the neutral `+` and `=`
    between its numbers resolve inside the expression instead of against the
    Arabic paragraph around it. Every run with so much as one Arabic letter is
    left to inherit the paragraph's direction and be placed by bidi, which is
    what mixed prose needs.

    Object geometry then goes through the rule table
    (`idml.rtl_plan.build_plan` + :func:`apply_plan`, `document` and
    `language` threaded straight through): template furniture stays, every
    piece of the page's content mirrors within its page, and each moved
    frame's side-naming properties -- wrap offset, text inset -- turn with it
    (:func:`mirror_item_properties`). A source already bound right to left is
    left where it is. `keep_upright` is threaded into that same call as an
    exception list: the link URIs the artwork stage already relinked to a
    translated picture, whose pixels must never be turned round.

    Two more passes run after the two above. :func:`mirror_anchored_object_
    settings` flips every inline badge's own text-relative position
    (`AnchorXoffset`, `HorizontalAlignment`, `AnchorPoint`) to match its
    paragraph's new direction -- unconditionally, unlike the rest of
    `mirror_item_properties`, because these three are measured against the
    text rather than the page (see that function's docstring). `idml.
    rtl_subparts.normalize_subpart_indentation` gives a group of sibling
    sub-part labels (`a.`, `b.`, `c.`, ... or `1.`, `2.`, `3.`, ...) -- very
    often one small frame per label, flush on a shared left edge in English
    -- the one shared start edge they no longer have once mirrored to
    right-aligned text, each now hugging its own frame's differently-placed
    right edge instead. Neither writes a frame's geometry or position. See
    each function's own docstring for the full reasoning.
    """
    prefs = pkg.document(PREFERENCES)
    pkg.document(STYLES)  # parsed for the loop below; edited there, not here

    report = {
        "rtl_text_direction_set": set_text_direction(pkg.documents, prefs,
                                                     pkg.document(FONTS)),
        "rtl_ltr_runs_pinned": preserve_ltr_content(pkg.documents),
        "rtl_font_registered": register_font(pkg.document(FONTS), idml_font,
                                             font_styles),
        "rtl_anchors_mirrored": mirror_anchored_object_settings(pkg.documents),
    }

    from pagebirdy.idml import rtl_plan

    plan = rtl_plan.build_plan(pkg.documents, document=document, language=language,
                               keep_upright=keep_upright)
    if is_rtl_bound(prefs):
        # Already laid out right to left: its content is where an RTL reader
        # expects it, and mirroring would put it back where English had it.
        # Text direction above still applies; geometry is left as it is.
        plan = rtl_plan.Plan(document=plan.document, language=plan.language,
                             rules_family=plan.rules_family, decisions=[])
    report.update(apply_plan(pkg.documents, plan))
    # A frame that crossed the page takes its side-naming properties with it:
    # a wrap cut 18pt into the type on its left now has to cut into the type
    # on its right, and a text inset wider on the left becomes wider on the
    # right. Anchored-object settings were already turned with the text above.
    report["rtl_side_properties_mirrored"] = mirror_item_properties(
        pkg.documents, plan, anchors=False)

    # A lettered or numbered sub-part list is very often one small frame per
    # label. Must run after the swap above: it reads each paragraph's
    # already-mirrored `RightIndent`, and it writes no frame geometry.
    from pagebirdy.idml import rtl_subparts

    report.update(rtl_subparts.normalize_subpart_indentation(pkg.documents))
    return report
