"""The units a designer composed, found before anything is classified.

Classifying objects one at a time tears compositions apart: an arrow flips
while the sentence it introduces stays put. So the objects are grouped first
and the group is classified as one thing.

Several sources, and an object joins at most one member list. The frames
spelling out one equation are a component because their arrangement is the
mathematics and must survive the page turning round -- found first, so a
block can claim part of a group's children; see "equation blocks" below. An
explicit `<Group>` is a component because the designer said so. Siblings
that sit on one line within a short gap of each other are a component
because that is how these books draw a direction line -- arrow and sentence,
never grouped. An anchored object belongs to its host's component, not to
whatever it happens to land beside.

**Adjacency is not evidence of direction.** An image next to a caption is a
component, but a component that is preserved: it is recomposed only when
something *names* it directional -- a direction-marker paragraph style, a
directional object style, or an explicit entry in the family's table.
Guessing from shape is how a coordinate plane gets reversed.

**Proximity clustering needs two more guards than "share a line, small gap"
suggests**, both found by running this over real books rather than trusting
the geometry in isolation:

* A pair of boxes that *overlap* in x -- a full-bleed background rectangle
  sitting behind an entire line of foreground frames, say -- is not "beside"
  anything; see `_gap`. Scoring that as some found gap (the naive formula's
  failure mode) let one background rectangle single-link an entire line of
  otherwise-unrelated frames into one component, in every one of the four
  books this was checked against.
* Single-linkage chaining has no sense of when to stop: three genuinely
  close pairs can still add up to a family-letter body column, a Math Tools
  sidebar and a vertical lesson title all becoming one "component" spanning
  87% of the page, each link individually well within gap. A hard span/member
  cap (`_MAX_CLUSTER_SPAN_FRACTION`, `_MAX_CLUSTER_MEMBERS`) is the backstop:
  past it, the cluster dissolves entirely rather than keeping some arbitrary
  truncated subset, because an object left unclustered lands on "leave it
  where it is" -- the safe default this whole project exists to prefer over
  a wrong, actively-transformed group.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

# Largest horizontal gap, in points, across which two siblings still read as
# one composition -- measured, not assumed. Across four real books
# (RCM06/RCM07/RCM08/iRCM01 -- different titles, different lessons; ~955
# same-line disjoint sibling pairs total), the one unambiguous composition in
# the sample -- a direction arrow beside its sentence, carrying the family's
# own `_Family Letter:FL caret` marker -- sits 8.45pt apart. Nothing else in
# the measurement cleanly separates "one composition" from "two unrelated
# frames the grid happened to put on the same line": the single busiest band
# in the whole distribution (158 of ~955 pairs) sits at 20-25pt, a page
# gutter width repeated all over the layout, and three other marked
# compositions sit as far as 68-70pt apart -- inside the same range the
# gutter noise occupies. There is no gap value that admits the 70pt cases
# without also admitting most of the 20-25pt noise, so this is set tight,
# just above the one clean measurement (with a couple of points of headroom
# so a real 10pt gap doesn't ride the boundary): a real composition wider
# than this is left unclustered rather than risk pulling in a neighbour that
# only looks related. See `_MAX_CLUSTER_SPAN_FRACTION` for the same "fails
# safe" choice applied to chain length instead of link distance.
_CLUSTER_GAP = 12.0

# IDML's own interactive form-control kinds, plus the plain-Rectangle style
# this book family draws a fill-in-the-blank underline or answer box with.
# Owned here, not in rtl_rules, because containment clustering (detect(),
# below) needs the same check and rtl_rules already imports from this
# module -- the dependency only runs one way.
FORM_FIELD_KINDS = ("TextBox", "CheckBox", "RadioButton")
FORM_FIELD_STYLE = "Form Fields"


def is_form_field(feature) -> bool:
    return feature.kind in FORM_FIELD_KINDS or feature.object_style == FORM_FIELD_STYLE


# A cluster whose union would cross this fraction of its own page's width, or
# collect more than this many members, does not form at all -- see `detect`
# step 2. This is the hard backstop for single-linkage chaining, which has
# no sense of when to stop on its own: three genuinely close pairs added up
# to a family-letter body column, a Math Tools sidebar and a vertical lesson
# title all becoming one component spanning 87% of a real page, each link
# individually well within `_CLUSTER_GAP`; a full-bleed background rectangle
# (fixed separately in `_gap`, but worth the margin) chained across an
# entire line at 97-102%. The floor this can be set to is not "wherever the
# real data looks clean" -- it isn't; see `_CLUSTER_GAP`'s note that no gap
# value cleanly separates real compositions from grid noise, and the same is
# true of span. It is set instead just above the two calibration cases this
# module is required to keep clustering (an arrow beside a full sentence at
# 49% of a 612pt page, an image beside a wide caption at 65.4%), and well
# under every confirmed-bad chain measured (87%+). 70%/6 members is that
# compromise: it keeps both calibration cases and rejects everything over
# roughly three quarters of a page's width, which is where every measured
# bad chain lives.
_MAX_CLUSTER_SPAN_FRACTION = 0.70
_MAX_CLUSTER_MEMBERS = 6

# Minimum vertical overlap, as a fraction of the shorter item, for two items to
# count as sharing a line.
_LINE_OVERLAP = 0.5

# Fraction of the smaller box's own area that must sit inside the larger
# box for one to count as the other's decorative backdrop, not just an
# incidental overlap. Measured against the real case this exists for:
# RCM07_NA_SW_U01_L03's grid-box backdrop contains its own form field's
# border at 100% (every edge of the smaller box sits inside the larger
# one). Set at 90%, not 100%, so ordinary floating-point/measurement noise
# in real books doesn't miss a genuine match -- but strict enough that a
# loose, partial touch (the false-positive shape this must not catch)
# cannot qualify.
_CONTAINMENT_FRACTION = 0.90


def _area(box) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def _containment_fraction(inner, outer) -> float:
    """What fraction of `inner`'s own area sits inside `outer`. 0 if
    `inner` has no area (a degenerate box), never a division error."""
    ix0 = max(inner[0], outer[0])
    iy0 = max(inner[1], outer[1])
    ix1 = min(inner[2], outer[2])
    iy1 = min(inner[3], outer[3])
    intersection = _area((ix0, iy0, ix1, iy1))
    inner_area = _area(inner)
    return intersection / inner_area if inner_area > 0 else 0.0


@dataclass(frozen=True)
class DirectionMarkers:
    """What a family accepts as evidence that a component is directional."""
    paragraph_styles: frozenset
    object_styles: frozenset
    component_ids: frozenset


@dataclass(frozen=True)
class Component:
    component_id: str
    # "group" | "cluster" | "containment" | "equation" -- never "anchored".
    # The anchored step below only ever joins an anchored object onto an
    # existing component; it never forms one of its own. An anchor whose host claimed no component at all
    # is simply absent from the returned list, left for whatever classifies
    # lone objects next -- the safe default, not a gap in this module.
    kind: str
    member_ids: tuple
    bounds: tuple
    page_index: int | None
    spread: str
    directional: bool
    evidence: str
    # True when this component is a mathematical expression: its members'
    # left-to-right arrangement *is* the mathematics, so it crosses the page
    # as one rigid unit and nothing inside it is rearranged. Set on the
    # `"equation"` components step 3 finds, and on an explicit `<Group>` the
    # designer drew an equation with. See `_forms_an_equation`.
    math: bool = False


def _union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _shares_a_line(a, b) -> bool:
    overlap = min(a[3], b[3]) - max(a[1], b[1])
    shorter = min(a[3] - a[1], b[3] - b[1])
    return shorter > 0 and overlap / shorter >= _LINE_OVERLAP


def _gap(a, b) -> float:
    """Horizontal gap between two boxes that sit beside each other.

    Returns `inf` when the boxes actually overlap in x, rather than the
    negative number the naive "whichever side is which" formula produces --
    a full-bleed background rectangle sitting behind an entire line of
    foreground frames overlaps every one of them in x, and a large negative
    number is `<= _CLUSTER_GAP` just as readily as a small positive one is.
    That is precisely how one background rectangle single-linked an entire
    line into one component when this was run over real books. An overlap
    means one box is stacked on or straddling the other, not sitting beside
    it, so it can never satisfy the "beside" test regardless of threshold.
    """
    if a[2] <= b[0]:
        return b[0] - a[2]
    if b[2] <= a[0]:
        return a[0] - b[2]
    return float("inf")


def _shares_a_column(a, b) -> bool:
    """Horizontal-overlap counterpart to `_shares_a_line` -- same ratio
    test, rotated to the x-axis, for two boxes stacked vertically."""
    overlap = min(a[2], b[2]) - max(a[0], b[0])
    shorter = min(a[2] - a[0], b[2] - b[0])
    return shorter > 0 and overlap / shorter >= _LINE_OVERLAP


def _vertical_gap(a, b) -> float:
    """Vertical counterpart to `_gap`. `inf` when the boxes share a line
    -- same reasoning as `_gap`'s own docstring: sharing a line means they sit
    beside each other, not stacked vertically."""
    if _shares_a_line(a, b):
        return float("inf")
    if a[3] <= b[1]:
        return b[1] - a[3]
    if b[3] <= a[1]:
        return a[1] - b[3]
    return 0.0


def _vertical_cluster_eligible(f) -> bool:
    """Non-text placed content with no structural signal that would put it
    under a named rule ahead of the catch-all (master item, or a form
    field, or math styling reachable via object_style). This module
    cannot import rtl_rules (rtl_rules already imports this module), so
    this mirrors the *shape* of those exclusions using only what
    ObjectFeature already exposes -- see the design spec's "Vertical
    adjacency cluster" section for why each check is here."""
    if f.content_kind not in ("raster", "vector"):
        return False
    if f.is_master_item:
        return False
    if is_form_field(f):
        return False
    if f.full_bleed:
        return False
    return True



def _page_width(f) -> float | None:
    """A feature's own page width in points, recovered from its `x_band`.

    `rtl_features.collect` already normalises `x_band` to
    `(left / page_width, right / page_width)`; inverting that is cheaper and
    more honest than re-deriving page geometry here, which this module never
    parses. `None` when the feature carries no band (defensive only -- every
    member reaching this point has `page_index is not None`, which implies a
    band was measured) or the band has zero width.
    """
    if f.x_band is None:
        return None
    dx = f.x_band[1] - f.x_band[0]
    if dx <= 0:
        return None
    return (f.bounds[2] - f.bounds[0]) / dx


def _directional(members, markers) -> tuple:
    """(is_directional, evidence sentence)."""
    for f in members:
        hit = f.paragraph_styles & markers.paragraph_styles
        if hit:
            return True, f"paragraph style {sorted(hit)[0]!r} marks direction"
        if f.object_style in markers.object_styles:
            return True, f"object style {f.object_style!r} is directional"
        if f.self_id in markers.component_ids:
            return True, f"{f.self_id} listed in the family component table"
    return False, "no direction marker among the members"


# ---- equation blocks -------------------------------------------------------
#
# A designer builds "3 · 4 = 12" out of five text frames set side by side,
# and a stack of those rows out of seven more. Their left-to-right arrangement
# is the mathematics: it is not a reading order, and it does not turn round
# when the page does. Reflecting each frame about the page axis on its own --
# which is what RTL_MIRROR means, and is right for every other composition --
# prints the row as "12 = 4 · 3"; reflecting each *row* about its own union
# instead breaks the vertical alignment between rows whose widths differ.
#
# So the block is found here, as a component, and classified `math.equation`
# -> RTL_REPOSITION: one delta, computed once from the block's union, applied
# to every member. Relative offsets survive by construction.

# Two or more pieces, because one frame holding a whole equation already
# behaves correctly: reflecting a single box about the page axis is a
# translation, and `rtl.preserve_ltr_content` pins its run left-to-right.
_EQUATION_MIN_MEMBERS = 2

# How tall a block may be, as a fraction of its page's *width* -- the one
# page measurement `_page_width` recovers honestly from a feature's own
# `x_band`, and close enough to a page's proportions to size a cap against.
# A block of equation rows is a few lines of type; a third of the page's
# width is roughly a quarter of its height, which is more room than the
# seven-row grids in these books need and well under the runaway chains
# measured on the corpus.
_MAX_EQUATION_HEIGHT_FRACTION = 0.33


def _equation_seed_eligible(f) -> bool:
    """True for a text frame holding a piece of an expression and nothing else.

    Only a seed can start a block or extend its chain. Master furniture and
    turned frames are refused outright: furniture takes part in no
    composition (`build_plan` filters it out before `detect` is called at
    all, and this keeps the answer the same for a direct caller), and a
    rotated frame's own space is not the page's, so "this row reads left to
    right across the page" stops being a statement about page coordinates.
    """
    return (f.content_kind == "text" and f.math_text
            and not f.is_master_item and not f.rotated)


def _equation_neutral_eligible(f) -> bool:
    """True for a non-prose piece an expression may be drawn with.

    A fraction bar, a long-division bracket, an answer box, a placed piece of
    mathematical vector artwork. These may *join* a block that already exists
    but may never seed one or extend its chain: they carry no text to
    identify them, so letting them link would be adjacency standing in for
    evidence, which is the mistake this module's own docstring warns about.

    A photograph is deliberately not here. A picture beside an equation is
    page content that mirrors, not part of the expression.
    """
    if f.is_master_item or f.full_bleed or f.rotated:
        return False
    return is_form_field(f) or f.content_kind in ("vector", "path", "empty")


def _equation_row_gap(members) -> float:
    """How far apart two rows of one block may sit, vertically.

    One line's worth of leading, taken from the block's own tallest member
    rather than fixed in points, so a block of 24pt display type and a block
    of 8pt answer-key type are each judged against their own setting. A
    constant here would be a page measurement smuggled in as a threshold.
    """
    return max((m.bounds[3] - m.bounds[1]) for m in members)


def _equation_links(box, other, row_gap: float) -> bool:
    """Is `other` part of the same block as the members `box` covers?

    Beside them on the same line, or stacked directly under them in the same
    column: the two ways an equation grows on a page. Both reuse the gap
    arithmetic proximity clustering already uses, so an overlap can never
    score as a small gap -- see `_gap`.
    """
    if _shares_a_line(box, other) and _gap(box, other) <= _CLUSTER_GAP:
        return True
    return (_shares_a_column(box, other)
            and _vertical_gap(box, other) <= row_gap)


def _same_place(a, b) -> bool:
    return (a.spread == b.spread and a.layer == b.layer
            and a.page_index == b.page_index)


def _forms_an_equation(members) -> bool:
    """True when this set of members is an equation and nothing else.

    Asked of an explicit `<Group>` the designer drew: every member has to be
    a piece of an expression or something an expression is drawn with, at
    least one has to be text that reads as mathematics, and at least one has
    to carry a relation or a binary operator. That last clause is what keeps
    a pair of bare numbers -- a figure label beside a folio -- from reading
    as an equation and being frozen.
    """
    if len(members) < _EQUATION_MIN_MEMBERS:
        return False
    seeds = [m for m in members if _equation_seed_eligible(m)]
    if not seeds:
        return False
    if not all(_equation_seed_eligible(m) or _equation_neutral_eligible(m)
               for m in members):
        return False
    return any(m.math_operator for m in seeds)


# How much of a non-member has to sit inside a block's rectangle before the
# block is not a unit any more, as a fraction of that object's own area.
# Not an edge tolerance in points: frames on a grid touch and overlap each
# other by a point or two everywhere in these books -- a paragraph whose box
# ends 3pt into the line below it is not standing in anything's way -- while
# a value table drawn across the same rows plainly is. Set low because the
# question is "is any real part of it in here", not "is it mostly in here":
# an object half inside the block is as much in the way as one wholly
# inside.
_BLOCK_INTRUSION_FRACTION = 0.1


def _ancestry(f, by_id):
    """`f`'s enclosing page items, innermost first."""
    out, parent, seen = [], f.parent_id, set()
    while parent is not None and parent not in seen:
        out.append(parent)
        seen.add(parent)
        parent = by_id[parent].parent_id if parent in by_id else None
    return out


def _stands_alone(members, others, by_id) -> bool:
    """Does the block occupy its own rectangle, with nothing else in it?

    The one guard a shared delta needs, and the reason is arithmetic. Every
    other composition on the page is *reflected*: each piece ends up at the
    mirror of where it was, so two pieces that did not overlap in English
    cannot overlap in Arabic. A block does something different -- every
    member moves by one delta taken from the block's union, which is what
    keeps its rows aligned with one another -- and a member of a three-row
    block therefore does *not* land at the mirror of its own position. It
    lands at the mirror of the block's, offset by where it sits inside it.

    Mixing the two on one rectangle is what collides. Measured on the
    calibration corpus: with no guard, four of the ten books grew new
    overlaps (`test_mirroring_adds_no_visible_overlap`) -- a worked
    solution's prose sentence reflected onto the equations it introduces,
    and two equation grids on one page, each reflected about its own union,
    landing on each other.

    So a block forms only where it is the whole of what sits in its
    rectangle. Where it is not, it dissolves and its frames mirror one by
    one as they did before: the equation reads backwards, which is the
    defect this module exists to fix, but a page that overlaps itself hides
    the text completely, and a visible wrong answer beats an invisible one.
    """
    box = _union([m.bounds for m in members])
    ids = {m.self_id for m in members}

    def kin(f) -> bool:
        """Is `f` an ancestor of a member, or a member's own descendant?

        Either way it travels with the block rather than standing in its
        way: an ancestor carries every member at once, and a descendant is
        carried by the member it sits in.

        Ancestry, not geometry. A box that merely *contains* the block is
        not necessarily taking it anywhere: iRCM01's number-bond artwork
        contains the four digit frames drawn over it and is mirrored by
        `math.vector_art` on its own account, so exempting it for holding
        them put the diagram on the far side of its own labels.
        """
        parent, seen = f.parent_id, set()
        while parent is not None and parent not in seen:
            if parent in ids:
                return True
            seen.add(parent)
            parent = by_id[parent].parent_id if parent in by_id else None
        return any(f.self_id == a for m in members
                   for a in _ancestry(m, by_id))

    for other in others:
        if other.self_id in ids or other.bounds is None:
            continue
        o = other.bounds
        # Whatever carries the block, or is carried by it, travels with it.
        if kin(other):
            continue
        if _containment_fraction(o, box) >= _BLOCK_INTRUSION_FRACTION:
            return False
    return True


def _fits(members, candidates, seed) -> bool:
    """Would the block still be one expression with `candidates` added?

    The cap is checked *before* each step rather than after the chain has
    finished, which is the difference between a block that stops at the
    edge of its own equation and one that swallows the page and is then
    thrown away whole. Single linkage has no sense of when to stop -- the
    same weakness proximity clustering caps with
    `_MAX_CLUSTER_SPAN_FRACTION` -- and restricting the chain to
    mathematical text does not fix it, because a worksheet *is* a page of
    mathematical text: uncapped, one chain on RCM08 L13 reached 504pt by
    257pt, six unrelated solutions moving as one rigid slab, which then
    landed on the prose introducing them.

    Both caps are fractions of the block's own page, never point values.
    Width reuses proximity clustering's; height is its own, because this
    chain grows in two directions where that one grows in one.
    """
    page_width = _page_width(seed)
    if page_width is None:
        return True
    box = _union([m.bounds for m in list(members) + list(candidates)])
    return ((box[2] - box[0]) <= _MAX_CLUSTER_SPAN_FRACTION * page_width
            and (box[3] - box[1]) <= _MAX_EQUATION_HEIGHT_FRACTION * page_width)


def _row_of(start, pool, taken, member_ids) -> list:
    """`start` and every seed chained to it along its own line.

    Horizontal single linkage, against each member rather than the growing
    union: a block is two-dimensional, and once the union covers three rows
    an interior token sits *inside* it, where it neither sits beside the
    union (`_gap` reports the overlap, correctly, as no gap at all) nor
    under it (`_vertical_gap` says they share a line). Measured against the
    union, the middle of a block could never join it.
    """
    row = [start]
    row_ids = {start.self_id}
    changed = True
    while changed:
        changed = False
        for other in pool:
            if other.self_id in taken or other.self_id in row_ids \
                    or other.self_id in member_ids:
                continue
            if not _same_place(other, start):
                continue
            if any(_shares_a_line(m.bounds, other.bounds)
                   and _gap(m.bounds, other.bounds) <= _CLUSTER_GAP
                   for m in row):
                row.append(other)
                row_ids.add(other.self_id)
                changed = True
    return row


def _group_is_an_equation(group, children, in_a_block, page_neighbours,
                          by_id) -> bool:
    """Is this `<Group>` an equation the designer drew as one object?

    Judged over *every* child, never over whichever ones a block left
    unclaimed. A group whose working is already a block and whose heading
    is not would otherwise be asked "is this heading an equation?", and for
    a heading that happens to read as one the answer is yes -- two rigid
    units on one rectangle, each reflected about its own union, landing on
    each other. So a group any of whose children a block claimed is not
    itself an equation: the block speaks for those children and the group
    mirrors as usual.

    The same "nothing else in its rectangle" guard applies as to a block,
    and for the same reason: a unit that moves by one delta instead of
    being reflected does not land at the mirror of each of its parts.
    """
    if group.self_id in in_a_block:
        return True
    if any(c.self_id in in_a_block for c in children):
        return False
    if not _forms_an_equation([c for c in children if c.bounds is not None]):
        return False
    if group.bounds is None or group.page_index is None:
        return True
    return _stands_alone(
        [group], page_neighbours.get((group.spread, group.page_index), ()),
        by_id)


def _equation_blocks(features: list, claimed: set) -> list:
    """Every equation block among `features`, as (parent_id, members) pairs.

    Chained among siblings only -- the members of one block share a parent,
    so the single delta the executor applies is both measured and applied in
    one coordinate space.

    **A row at a time.** The seed's own line is completed first, then rows
    are added under (or over) it one whole row at a time, and a row that
    would push the block past `_fits` is refused rather than the block being
    dissolved. Rows go in whole because a half-added row is the failure this
    module exists to prevent, in miniature: the tokens that joined travel by
    the block's delta and the ones that did not are reflected about the page
    axis, so they cross each other.

    Neutral pieces -- a fraction bar, an answer box, a piece of mathematical
    artwork -- are attached last and never extend the chain: they carry no
    text to identify them, so letting them link would be adjacency standing
    in for evidence, the mistake this module's own docstring warns about.
    """
    by_id = {f.self_id: f for f in features}
    buckets: dict = {}
    for f in features:
        if f.self_id in claimed or f.bounds is None or f.page_index is None:
            continue
        if _equation_seed_eligible(f) or _equation_neutral_eligible(f):
            buckets.setdefault(f.parent_id, []).append(f)

    # Everything that could stand in a block's way. Master furniture is left
    # out: it never moves, so a block passing under a running head collides
    # with nothing, and `build_plan` filters it before calling this anyway.
    on_the_page: dict = {}
    for f in features:
        if f.bounds is None or f.page_index is None or f.is_master_item:
            continue
        on_the_page.setdefault((f.spread, f.page_index), []).append(f)

    blocks: list = []
    taken: set = set()
    for parent_id, bucket in buckets.items():
        seeds = [f for f in bucket if _equation_seed_eligible(f)]
        for seed in sorted(seeds, key=lambda f: f.z_index):
            if seed.self_id in taken:
                continue
            members = _row_of(seed, seeds, taken, set())
            member_ids = {m.self_id for m in members}
            if not _fits(members, (), seed):
                continue

            # Then whole rows, nearest first, for as long as they fit.
            growing = True
            while growing:
                growing = False
                row_gap = _equation_row_gap(members)
                for other in sorted(seeds, key=lambda f: f.bounds[1]):
                    if other.self_id in taken or other.self_id in member_ids:
                        continue
                    if not _same_place(other, seed):
                        continue
                    if not any(_shares_a_column(m.bounds, other.bounds)
                               and _vertical_gap(m.bounds, other.bounds) <= row_gap
                               for m in members):
                        continue
                    row = _row_of(other, seeds, taken, member_ids)
                    if not _fits(members, row, seed):
                        continue
                    members.extend(row)
                    member_ids.update(m.self_id for m in row)
                    growing = True
                    break

            if not any(m.math_operator for m in members):
                continue

            # Neutral pieces: beside a member, drawn inside one, or standing
            # among them inside the block's own rectangle -- which is where
            # a fraction bar ruled between two rows sits, sharing a gap with
            # nothing on either side.
            box = _union([m.bounds for m in members])
            row_gap = _equation_row_gap(members)
            for other in bucket:
                if other.self_id in taken or other.self_id in member_ids:
                    continue
                if _equation_seed_eligible(other) \
                        or not _same_place(other, seed):
                    continue
                if (_containment_fraction(other.bounds, box) >= _CONTAINMENT_FRACTION
                        or any(_equation_links(m.bounds, other.bounds, row_gap)
                               or _containment_fraction(other.bounds, m.bounds)
                               >= _CONTAINMENT_FRACTION
                               for m in members)):
                    members.append(other)
                    member_ids.add(other.self_id)

            if len(members) < _EQUATION_MIN_MEMBERS:
                continue
            if not _stands_alone(members,
                                 on_the_page.get((seed.spread, seed.page_index), ()),
                                 by_id):
                continue
            members.sort(key=lambda m: m.z_index)
            taken.update(member_ids)
            blocks.append((parent_id, members))
    return blocks


def _expand_descendants(member_ids, by_id, children_by_parent):
    """Every feature transitively reachable from a component's own members.

    A component's `member_ids` names only what it directly claimed: a nested
    `<Group>`'s own children stay in that inner group's *separate*
    component (see step 1), and an anchored object's own further-anchored
    children are only reachable by walking down from it. But all of it moves
    together with the outer component when the outer component is
    transformed, so a direction marker buried several levels down is still
    real evidence for the *outer* decision. This widens what `_directional`
    is allowed to see without touching `member_ids` itself -- membership
    stays exactly as already decided by steps 1-3; only the evidence search
    reaches further than the shallow list it was built from.
    """
    resolved: list = []
    seen: set = set()
    stack = list(member_ids)
    while stack:
        mid = stack.pop()
        if mid in seen:
            continue
        seen.add(mid)
        f = by_id.get(mid)
        if f is not None:
            resolved.append(f)
        stack.extend(child.self_id for child in children_by_parent.get(mid, ()))
    return resolved


def detect(features: list, markers: DirectionMarkers) -> list:
    """Group `features` into components. Document order is preserved."""
    by_id = {f.self_id: f for f in features}
    claimed: set = set()
    components: list = []

    # 0. Equation blocks, ahead of everything: the pieces of one expression
    #    are a composition whichever container they happen to sit in, and
    #    finding them first is what lets a block claim *some* of a group's
    #    children -- a worked example whose heading is prose and whose
    #    working is an equation. A block covering every child of a `<Group>`
    #    is left unformed on purpose: that group *is* the equation, and step
    #    1 marks it `math` so it crosses the page as one unit with nothing
    #    inside it rearranged. Forming both would put the same members in
    #    two components.
    children_of: dict = {}
    page_neighbours: dict = {}
    for f in features:
        children_of.setdefault(f.parent_id, []).append(f)
        if f.bounds is not None and f.page_index is not None \
                and not f.is_master_item:
            page_neighbours.setdefault((f.spread, f.page_index), []).append(f)
    in_a_block: set = set()
    for parent_id, members in _equation_blocks(features, claimed):
        parent = by_id.get(parent_id)
        if parent is not None and parent.kind == "Group" \
                and len(members) == len(children_of.get(parent_id, ())):
            # This group *is* the equation; step 1 marks it, and forming a
            # block as well would put the same members in two components.
            in_a_block.add(parent_id)
            continue
        in_a_block.update(m.self_id for m in members)
        claimed.update(m.self_id for m in members)
        directional, why = _directional(members, markers)
        components.append(Component(
            component_id=f"equation:{members[0].self_id}", kind="equation",
            member_ids=tuple(m.self_id for m in members),
            bounds=_union([m.bounds for m in members]),
            page_index=members[0].page_index, spread=members[0].spread,
            directional=directional, evidence=why, math=True))

    # 1. Explicit groups. Deepest first, so a nested group claims its own
    #    children before its parent sees them.
    groups = [f for f in features if f.kind == "Group"]
    for g in sorted(groups, key=lambda f: -f.z_index):
        members = [f for f in features
                   if f.parent_id == g.self_id and f.self_id not in claimed
                   and f.bounds is not None]
        if not members:
            continue
        claimed.update(f.self_id for f in members)
        directional, why = _directional(members, markers)
        components.append(Component(
            component_id=g.self_id, kind="group",
            member_ids=tuple(f.self_id for f in members),
            bounds=_union([f.bounds for f in members]),
            page_index=g.page_index, spread=g.spread,
            directional=directional, evidence=why,
            math=_group_is_an_equation(
                g, children_of.get(g.self_id, ()), in_a_block,
                page_neighbours, by_id)))

    # 2. Containment clusters: a plain vector/path object whose bounds sit
    #    almost entirely inside a form field's own bounds is that field's
    #    decorative backdrop, not independent content -- see
    #    docs/superpowers/specs/2026-09-11-content-region-rtl-mirroring-design.md,
    #    "The RCM07 grid box: real relationship evidence, not spatial
    #    coincidence". Anchored on the form field deliberately: whatever the
    #    field's own decision is (today always KEEP_POSITION, from
    #    rtl_rules.form.field), the backdrop inherits it through the same
    #    component.bound path every other component member already uses --
    #    no new executor behaviour, only a new membership.
    remaining = [f for f in features if f.self_id not in claimed
                and f.bounds is not None and f.page_index is not None]
    fields = [f for f in remaining if is_form_field(f)]
    for field in fields:
        if field.self_id in claimed:
            continue
        backdrops = [
            f for f in remaining
            if f.self_id != field.self_id and f.self_id not in claimed
            and not is_form_field(f)
            and f.content_kind in ("vector", "path")
            and f.spread == field.spread
            and f.page_index == field.page_index
            and max(_containment_fraction(f.bounds, field.bounds),
                    _containment_fraction(field.bounds, f.bounds)) >= _CONTAINMENT_FRACTION
        ]
        if not backdrops:
            continue
        member_ids = (field.self_id,) + tuple(b.self_id for b in backdrops)
        claimed.update(member_ids)
        directional, why = _directional([field] + backdrops, markers)
        components.append(Component(
            component_id=field.self_id, kind="containment",
            member_ids=member_ids,
            bounds=_union([field.bounds] + [b.bounds for b in backdrops]),
            page_index=field.page_index, spread=field.spread,
            directional=directional, evidence=why))

    # 3. Proximity clusters among the remaining top-level siblings.
    free = [f for f in features
            if f.self_id not in claimed and f.kind != "Group"
            and f.bounds is not None and f.page_index is not None
            and by_id.get(f.parent_id) is None]
    for f in sorted(free, key=lambda f: f.z_index):
        if f.self_id in claimed:
            continue
        members = [f]
        changed = True
        while changed:
            changed = False
            box = _union([m.bounds for m in members])
            for other in free:
                if other.self_id in claimed or other in members:
                    continue
                # Same spread as well as same page: `page_index` counts within
                # its own spread, so page 0 exists in every spread and without
                # this guard two unrelated items on different spreads that
                # happen to share a y-band would cluster into one component.
                if (other.spread != f.spread or other.layer != f.layer
                        or other.page_index != f.page_index):
                    continue
                if _shares_a_line(box, other.bounds) and \
                        _gap(box, other.bounds) <= _CLUSTER_GAP:
                    members.append(other)
                    changed = True
        if len(members) < 2:
            continue
        box = _union([m.bounds for m in members])
        page_width = _page_width(f)
        too_wide = (page_width is not None
                    and (box[2] - box[0]) > _MAX_CLUSTER_SPAN_FRACTION * page_width)
        too_many = len(members) > _MAX_CLUSTER_MEMBERS
        if too_wide or too_many:
            # The chain formed but blew past a hard safety cap: dissolve it
            # entirely rather than keep some arbitrary truncated subset --
            # which members to cut would be an arbitrary choice on the same
            # single-linkage chain that produced the oversized blob. Every
            # member is left unclaimed, to be classified individually, which
            # is the safe default: an object with no component is left where
            # it is, where a wrong cluster gets actively recomposed.
            continue
        claimed.update(m.self_id for m in members)
        directional, why = _directional(members, markers)
        members.sort(key=lambda m: m.z_index)
        components.append(Component(
            component_id=f"cluster:{members[0].self_id}", kind="cluster",
            member_ids=tuple(m.self_id for m in members),
            bounds=box,
            page_index=f.page_index, spread=f.spread,
            directional=directional, evidence=why))

    # 4. Vertical adjacency clusters: two or more non-text placed graphics,
    #    neither already claimed by anything above and neither eligible for
    #    a named rule ahead of the catch-all, stacked within the same gap
    #    tolerance the horizontal case uses and sharing substantial x-axis
    #    overlap. This is deliberately not "the horizontal algorithm
    #    rotated" -- content_kind/is_master_item/is_form_field are checked
    #    first specifically so a header sitting above a paragraph, or
    #    furniture sitting above content, never qualifies regardless of
    #    spacing. See the design spec's "Component detection" section.
    remaining_vert = [f for f in features
                      if f.self_id not in claimed and f.kind != "Group"
                      and f.bounds is not None and f.page_index is not None
                      and by_id.get(f.parent_id) is None
                      and _vertical_cluster_eligible(f)]
    for f in sorted(remaining_vert, key=lambda f: f.z_index):
        if f.self_id in claimed:
            continue
        members = [f]
        changed = True
        while changed:
            changed = False
            box = _union([m.bounds for m in members])
            for other in remaining_vert:
                if other.self_id in claimed or other in members:
                    continue
                if (other.spread != f.spread or other.layer != f.layer
                        or other.page_index != f.page_index):
                    continue
                if _shares_a_column(box, other.bounds) and \
                        _vertical_gap(box, other.bounds) <= _CLUSTER_GAP:
                    members.append(other)
                    changed = True
        if len(members) < 2:
            continue
        box = _union([m.bounds for m in members])
        page_width = _page_width(f)
        too_wide = (page_width is not None
                   and (box[2] - box[0]) > _MAX_CLUSTER_SPAN_FRACTION * page_width)
        too_many = len(members) > _MAX_CLUSTER_MEMBERS
        if too_wide or too_many:
            continue
        claimed.update(m.self_id for m in members)
        directional, why = _directional(members, markers)
        members.sort(key=lambda m: m.z_index)
        components.append(Component(
            component_id=f"cluster:{members[0].self_id}", kind="cluster",
            member_ids=tuple(m.self_id for m in members),
            bounds=box,
            page_index=f.page_index, spread=f.spread,
            directional=directional, evidence=why))

    # 5. Anchored objects join their host's component; an anchor with no
    #    component of its own is left to be classified as a lone object.
    for f in features:
        if not f.anchored or f.self_id in claimed:
            continue
        host = next((c for c in components if f.parent_id in c.member_ids
                     or f.parent_id == c.component_id), None)
        if host is None:
            continue
        claimed.add(f.self_id)
        components[components.index(host)] = replace(
            host, member_ids=host.member_ids + (f.self_id,))

    # 4. Directionality is decided over each component's fully-resolved
    #    descendant set, not the shallow list it was built from in steps 1-2.
    #    An anchored join in step 3 can hand a component its first marker,
    #    and a nested group's own children never entered its parent's
    #    `member_ids` at all (they belong to the inner group's own
    #    component, from step 1). This is the one point in `detect` where
    #    every join has already happened, so it is the only point where the
    #    full picture exists to classify from.
    children_by_parent: dict = {}
    for feat in features:
        children_by_parent.setdefault(feat.parent_id, []).append(feat)
    resolved: list = []
    for c in components:
        full = _expand_descendants(c.member_ids, by_id, children_by_parent)
        directional, why = _directional(full, markers)
        resolved.append(replace(c, directional=directional, evidence=why))
    return resolved
