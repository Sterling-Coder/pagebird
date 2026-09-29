"""The global page mirror, kept for the RTL targets nobody has calibrated yet.

This is the original geometry pass: every top-level page item reflects within
the page it sits on, and every group's children reflect about the group's own
centre. Arabic no longer uses it -- see `rtl_plan` for the semantic engine that
replaced it, and the spec at
`docs/superpowers/specs/2026-09-08-semantic-rtl-recomposition-design.md` for the
measurements that showed a whole-page mirror is not what a human Arabic edition
looks like.

Nothing in the pipeline calls this any more: `idml.rtl.apply_rtl` now moves
geometry through the calibrated rule table in `idml.rtl_plan`/`idml.rtl_rules`
instead, for all four RTL targets -- Arabic, Hebrew, Persian and Urdu alike
get rules 1-14 (page furniture stays put, math content is geometry-locked, a
direction line restructures, a decorative bleed mirrors, and so on); only the
table's closing catch-all is narrower, mirroring an object no earlier rule
recognises for `language == "ar"` on the one calibrated book family. This
module is kept, and still tested on its own terms, as the calibration
starting point should a whole-page mirror ever be wanted again for a
language or family the semantic engine has not been calibrated against.

**How the mirror works.** An IDML page item is a child of ``<Spread>`` carrying
``ItemTransform="a b c d tx ty"`` -- the matrix mapping its own path geometry
into spread space (``x' = a*x + c*y + tx``, ``y' = b*x + d*y + ty``). The naive
mirror composes a reflection onto that matrix, which is wrong: negating ``a``
flips the item's *content*, so text renders backwards and a photograph comes
out reversed. That is the ``scaleX(-1)`` trap.

Instead we reflect only the item's *position*. We measure the item's
axis-aligned bounds in spread space, reflect that box across the spread's
vertical centre line, and add the resulting delta to ``tx`` alone::

    dx = 2*axis - (x0 + x1)

Because ``a b c d`` are never touched, width, height, rotation, scale, shear
and content orientation all survive exactly. A 90-degree-rotated caption stays
rotated the same way; it simply sits on the other side of the page.

**Each item mirrors within its own page.** The axis is the centre of the page
the item sits on, taken from that page's own ``<Page>`` bounds, so nothing is
hardcoded to a page size. Reflecting a facing-page spread about the spread
centre instead would carry every item across the gutter and swap the two pages,
printing page 17 where page 16 belongs. Page order is a property of the
document; RTL binding is expressed by ``PageBinding``, not by moving content
between pages. Only an item that genuinely spans two pages -- a full-bleed
backdrop, a banner across the gutter -- reflects about the spread centre, since
it has no single page to belong to. An item on the pasteboard never prints and
is left where it was.

**Groups mirror inside as well as out.** A group moves by its own ``tx``, and
then its children reflect about the group's own centre, which leaves the
group's outline exactly where the page mirror put it and rearranges only what
is inside. A callout is a bar, a label and a badge pinned to the end the
sentence starts at; travelling the group and leaving its composition alone puts
that badge at the *end* of an Arabic sentence. The human-authored Arabic
reference rearranges exactly these clusters.

This is the page mirror one level down, and it keeps the same two
guarantees. The axis is the centre of the children's own union, so the
group's outline is unchanged and only the arrangement inside it moves. And
a child's matrix is never negated -- only ``tx`` -- so no child's *content* is
flipped, which is the ``scaleX(-1)`` trap one level down.

There are two exceptions. A group whose children read as a horizontal run of
type -- a number bond, an equation assembled from sibling frames -- is moved
and never rearranged: reflecting siblings reverses their visual order, which
would print the expression backwards. And a *rotated* group is moved and never
rearranged either, because a child's ``tx`` runs along its group's horizontal
and under a 90-degree group that points down the page: mirroring there would
move objects vertically, which a mirror about a vertical axis must never do.
"""

from __future__ import annotations

from pagebirdy.idml.rtl import (  # noqa: F401 - re-exported for this module's use
    IDENTITY, _is, _is_page_item, compose, format_transform, item_bounds,
    mirror_axis_for, page_extents, parse_transform, reflect_graphic,
    reflect_path, spread_axis, _carries_text, _OVERLAP_EPS,
)


def is_text_sequence(children, boxes) -> bool:
    """True when the children read as a row of type rather than a composition.

    A number bond or an equation is built from sibling frames sharing one line
    -- `___ + ___ = ___`. Reflecting siblings reverses their visual order, which
    prints the expression backwards, so a group shaped like that is moved but
    never rearranged. The shape is specific: two or more text-bearing children
    that are disjoint horizontally *and* overlap vertically, which is what
    sitting side by side on a line means and what a stacked heading and
    subheading are not.
    """
    text = [b for el, b in zip(children, boxes) if b is not None and _carries_text(el)]
    for i, a in enumerate(text):
        for b in text[i + 1:]:
            side_by_side = (a[2] <= b[0] + _OVERLAP_EPS or b[2] <= a[0] + _OVERLAP_EPS)
            shares_a_line = min(a[3], b[3]) - max(a[1], b[1]) > _OVERLAP_EPS
            if side_by_side and shares_a_line:
                return True
    return False


def mirror_group(group, orientation: tuple[float, ...] = IDENTITY,
                 keep_upright=(), flipped: list | None = None) -> int:
    """Reflect a group's children about the group's own centre.

    The page-level mirror moves a group's `tx` and stops, which travels the
    group across the page with its composition intact. That is right for a
    photograph and wrong for furniture: a callout is a bar, a label and a badge
    pinned to the end the sentence *starts* at, so leaving the composition alone
    puts the badge at the end of an Arabic sentence. The human-authored Arabic
    reference rearranges exactly these clusters.

    This is the page mirror one level down, and it keeps the same two
    guarantees. The axis is the centre of the children's own union, so the
    group's outline is unchanged and only the arrangement inside it moves. And
    a child's matrix is never negated -- only `tx` -- so no child's *content* is
    flipped, which is the `scaleX(-1)` trap one level down.

    A group whose children read as a horizontal run of type is moved and not
    rearranged; see :func:`is_text_sequence`. Nested groups mirror at every
    level, each about its own centre.

    **A rotated group's own x is not the page's x.** A child's transform is
    written in its group's coordinate system, so moving its `tx` moves it along
    the *group's* horizontal. Under a 90-degree group that horizontal points
    down the page, and reflecting the children there mirrors them vertically --
    three badges in a rotated strip swapping top for bottom in a real book. A
    mirror about a vertical axis may never move anything vertically, so a group
    whose axes are no longer parallel to the page's travels as a unit and its
    composition is left exactly as designed. `orientation` is the accumulated
    transform above the group, so the test is made against where the group
    really sits rather than against its own matrix alone; a nested group that
    rotates back into square with the page is mirrored again.

    Returns the number of children moved.
    """
    children = [c for c in group if _is_page_item(c)]
    if not children:
        return 0
    # A lone child already spans the group, so its reflection about the group's
    # centre is itself and `dx` comes out zero. It is still walked, because a
    # group wrapping a single nested group is how a composition is usually
    # built and its grandchildren do have an arrangement to mirror.
    boxes = [item_bounds(c) for c in children]
    if any(b is None for b in boxes):
        return 0

    inside = compose(orientation, parse_transform(group.get("ItemTransform")))
    upright = inside[1] == 0.0 and inside[2] == 0.0
    if upright and is_text_sequence(children, boxes):
        return 0

    axis = (min(b[0] for b in boxes) + max(b[2] for b in boxes)) / 2.0
    moved = 0
    for child, box in zip(children, boxes):
        if upright:
            dx = 2.0 * axis - (box[0] + box[2])
            t = parse_transform(child.get("ItemTransform"))
            child.set("ItemTransform", format_transform(t[:4] + (t[4] + dx, t[5])))
            # Reflecting a decorative outline is a mirror in the same local x,
            # so it is as vertical as the move would be under a rotated group.
            reflect_path(child)
            if reflect_graphic(child, keep_upright) and flipped is not None:
                flipped.append(child.get("Self"))
            moved += 1
        if _is(child, "Group"):
            moved += mirror_group(child, inside, keep_upright, flipped)
    return moved


def mirror_spread(spread, keep_upright=(), flipped: list | None = None) -> int:
    """Reflect every top-level page item within the page it sits on. Returns
    the number of items moved.

    `flipped`, when given, collects the `Self` of every frame whose picture was
    turned round -- a count worth reporting separately, because it is the one
    part of the mirror that changes what a page item *contains*.
    """
    extents = page_extents(spread)
    if not extents:
        return 0
    centre = spread_axis(spread)

    moved = 0
    for el in spread:
        if not _is_page_item(el):
            continue
        box = item_bounds(el)
        if box is None:
            continue
        axis = mirror_axis_for(box, extents, centre)
        if axis is None:
            continue
        dx = 2.0 * axis - (box[0] + box[2])
        t = parse_transform(el.get("ItemTransform"))
        el.set("ItemTransform", format_transform(t[:4] + (t[4] + dx, t[5])))
        # Reflect the outline of a purely decorative item too, so an
        # asymmetric curve still points the way it pointed. Done here rather
        # than in a pass of its own so it reaches exactly the items that
        # actually moved: a pasteboard item is skipped above and must stay
        # untouched, shape included.
        reflect_path(el)
        # A photograph is turned round here too, for the same reason and on the
        # same terms: only where the item actually moved, so a pasteboard frame
        # keeps its picture exactly as parked.
        if reflect_graphic(el, keep_upright) and flipped is not None:
            flipped.append(el.get("Self"))
        moved += 1
        # A group's composition mirrors too, about the group's own centre, so a
        # badge pinned to the start of its label stays at the start.
        if _is(el, "Group"):
            moved += mirror_group(el, IDENTITY, keep_upright, flipped)
    return moved


def mirror_geometry(documents: dict, keep_upright=(),
                    flipped: list | None = None) -> int:
    """Mirror every spread and master spread in a parsed IDML package.

    Master spreads are included because folios, running heads and margin
    furniture live there; leaving them behind would strand the page number on
    the old binding edge.
    """
    moved = 0
    for name, tree in documents.items():
        if not name.startswith(("Spreads/", "MasterSpreads/")):
            continue
        for el in tree.iter("Spread", "MasterSpread"):
            moved += mirror_spread(el, keep_upright, flipped)
    return moved
