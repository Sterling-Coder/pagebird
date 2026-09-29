"""Content mirrored within its page never lands on a neighbouring page.

The target keeps the source's left-to-right binding (`validate` rejects a
`PageBinding` change), so the edge an item bleeds off in English is still an
outer edge only in English. Reflect a band that bleeds off a right-hand page's
outer trim and its bleed arrives over the spine, printing on the facing page --
the Understand question bar on RCM07 L03 page 49 did exactly that. Every move
the executor makes is therefore held to its owning page on each side where
another page sits, and a component is held as one piece so its members keep
their arrangement.

Every expectation here is derived from the page geometry of the fixture, never
from a coordinate of a real book.
"""

from lxml import etree
import pytest

from pagebirdy.idml import rtl, rtl_plan, rtl_validate

PAGE_W = 612.0

_HEAD = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="{count}" ItemTransform="1 0 0 1 0 0">
    {pages}
    {items}
  </Spread>
</idPkg:Spread>
"""


def _spread_xml(page_x0s, items):
    pages = "\n".join(
        f'<Page Self="p{i}" GeometricBounds="0 0 792 {PAGE_W:g}" '
        f'ItemTransform="1 0 0 1 {x0:g} -396"/>'
        for i, x0 in enumerate(page_x0s))
    return _HEAD.format(count=len(page_x0s), pages=pages, items=items)


FACING = (-PAGE_W, 0.0)                       # pages (-612, 0) and (0, 612)
THREE = (-1.5 * PAGE_W, -0.5 * PAGE_W, 0.5 * PAGE_W)
SINGLE = (0.0,)


def _rect(self_id, x0, x1, y0=-50.0, y1=50.0, tx=0.0, inner=""):
    return f"""
    <Rectangle Self="{self_id}" ItemTransform="1 0 0 1 {tx:g} 0">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="{x0} {y0}"/><PathPointType Anchor="{x0} {y1}"/>
        <PathPointType Anchor="{x1} {y1}"/><PathPointType Anchor="{x1} {y0}"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>{inner}
    </Rectangle>"""


def _group(self_id, children, tx=0.0):
    return f'<Group Self="{self_id}" ItemTransform="1 0 0 1 {tx:g} 0">{children}</Group>'


def _docs(page_x0s, items):
    return {"Spreads/S.xml": etree.fromstring(_spread_xml(page_x0s, items).encode())}


def _plan(*decisions):
    return rtl_plan.Plan(document="d", language="ar", rules_family="f",
                         decisions=list(decisions))


def _d(obj, action, **over):
    base = dict(page=0, spread="spr", object=obj, component=None,
                type="Rectangle", layer=None, object_style=None,
                paragraph_styles=(), bounds=None, new_bounds=None,
                orientation=rtl_plan.KEEP_ORIENTATION,
                new_orientation=rtl_plan.KEEP_ORIENTATION,
                action=action, text=rtl_plan.KEEP_TEXT, rule="t", reason="t")
    base.update(over)
    return rtl_plan.Decision(**base)


def _el(docs, self_id):
    return docs["Spreads/S.xml"].find(f".//*[@Self='{self_id}']")


def _box(docs, self_id):
    """`self_id`'s bounds in spread coordinates, through every ancestor."""
    el = _el(docs, self_id)
    t = rtl.IDENTITY
    for a in reversed([a for a in el.iterancestors()
                       if rtl._is_page_item(a) and not rtl._is(a, "Spread")]):
        t = rtl.compose(t, rtl.parse_transform(a.get("ItemTransform")))
    return rtl.item_bounds(el, t)


def _extents(docs):
    return rtl.page_extents(next(docs["Spreads/S.xml"].iter("Spread")))


def _neighbour_overlap(box, extents, page):
    """How far `box` reaches into each page beside `page`, in points."""
    px0, px1 = extents[page]
    out = 0.0
    for i, (ox0, ox1) in enumerate(extents):
        if i != page:
            out = max(out, min(box[2], ox1) - max(box[0], ox0))
    return max(out, 0.0)


def _snapshot(docs):
    return {k: etree.fromstring(etree.tostring(v)) for k, v in docs.items()}


TOL = 1e-6


# ---- a lone item -----------------------------------------------------------

def test_an_item_bleeding_off_a_right_page_s_outer_edge_stops_at_the_spine():
    bleed = 13.5
    docs = _docs(FACING, _rect("bar", 400, PAGE_W + bleed))
    before = _snapshot(docs)
    rtl.apply_plan(docs, _plan(_d("bar", rtl_plan.RTL_MIRROR)))
    x0, y0, x1, y1 = _box(docs, "bar")
    assert x0 == pytest.approx(0.0), "the bleed crossed the spine"
    # A translation only: same width, same height, same vertical place.
    assert x1 - x0 == pytest.approx(PAGE_W + bleed - 400)
    assert (y0, y1) == pytest.approx((-50.0, 50.0))
    assert rtl_validate.page_crossings(before, docs) == []


def test_an_item_bleeding_off_a_left_page_s_outer_edge_stops_at_the_spine():
    bleed = 13.5
    docs = _docs(FACING, _rect("bar", -PAGE_W - bleed, -400))
    rtl.apply_plan(docs, _plan(_d("bar", rtl_plan.RTL_MIRROR)))
    x0, _, x1, _ = _box(docs, "bar")
    assert x1 == pytest.approx(0.0), "the bleed crossed the spine"
    assert x1 - x0 == pytest.approx(PAGE_W + bleed - 400)


def test_a_full_width_item_keeps_its_bleed_on_the_outer_edge():
    """Reflected about its page it would put the bleed over the spine; held to
    its page it comes back exactly where it was."""
    docs = _docs(FACING, _rect("band", 0, PAGE_W + 13.5))
    rtl.apply_plan(docs, _plan(_d("band", rtl_plan.RTL_MIRROR)))
    assert _box(docs, "band")[0] == pytest.approx(0.0)
    assert _box(docs, "band")[2] == pytest.approx(PAGE_W + 13.5)


def test_an_item_wholly_inside_its_page_mirrors_exactly_as_before():
    docs = _docs(FACING, _rect("box", 100, 200))
    rtl.apply_plan(docs, _plan(_d("box", rtl_plan.RTL_MIRROR)))
    assert _box(docs, "box")[::2] == pytest.approx((PAGE_W - 200, PAGE_W - 100))


def test_a_bleed_on_a_single_page_spread_still_mirrors_freely():
    """No page beside it: both trims are outer edges and nothing is held."""
    docs = _docs(SINGLE, _rect("band", 400, PAGE_W + 13.5))
    rtl.apply_plan(docs, _plan(_d("band", rtl_plan.RTL_MIRROR)))
    assert _box(docs, "band")[0] == pytest.approx(-13.5)


def test_a_rigid_reposition_is_held_to_its_page_too():
    docs = _docs(FACING, _rect("eq", 450, PAGE_W + 20))
    rtl.apply_plan(docs, _plan(_d("eq", rtl_plan.RTL_REPOSITION)))
    assert _box(docs, "eq")[0] == pytest.approx(0.0)


# ---- components ------------------------------------------------------------

def test_a_group_near_the_spine_fits_its_page_and_keeps_its_arrangement():
    bleed = 13.5
    docs = _docs(FACING, _group("g", _rect("bar", 300, PAGE_W + bleed)
                                + _rect("icon", 310, 340)))
    rtl.apply_plan(docs, _plan(
        _d("g", rtl_plan.RTL_MIRROR, type="Group", component="g",
           component_kind="group"),
        _d("bar", rtl_plan.KEEP_POSITION, component="g", component_kind="group",
           position_bound=True, rule="component.bound"),
        _d("icon", rtl_plan.KEEP_POSITION, component="g", component_kind="group",
           position_bound=True, rule="component.bound")))
    g, bar, icon = _box(docs, "g"), _box(docs, "bar"), _box(docs, "icon")
    assert g[0] == pytest.approx(0.0), "the group crossed the spine"
    assert g[2] - g[0] == pytest.approx(PAGE_W + bleed - 300)
    # The icon led the bar at its left end; it leads it at the right end now,
    # the same 10pt in from the bar's edge.
    assert bar[2] - icon[2] == pytest.approx(10.0)


def _cluster(action, *members):
    anchor, *rest = members
    return [_d(anchor, action, component="c", component_kind="cluster")] + [
        _d(m, rtl_plan.KEEP_POSITION, component="c", component_kind="cluster",
           position_bound=True, rule="component.bound") for m in rest]


@pytest.mark.parametrize("action", [rtl_plan.RTL_MIRROR, rtl_plan.RTL_REPOSITION])
def test_a_cluster_near_the_spine_moves_as_one_piece_and_fits_its_page(action):
    bleed = 13.5
    docs = _docs(FACING, _rect("bar", 400, PAGE_W + bleed) + _rect("icon", 420, 440))
    before = _snapshot(docs)
    rtl.apply_plan(docs, _plan(*_cluster(action, "bar", "icon")))
    bar, icon = _box(docs, "bar"), _box(docs, "icon")
    assert min(bar[0], icon[0]) == pytest.approx(0.0), "the cluster crossed the spine"
    if action == rtl_plan.RTL_MIRROR:
        # Mirrored arrangement: the icon keeps its 20pt from the bar's leading edge.
        assert bar[2] - icon[2] == pytest.approx(20.0)
    else:
        # Rigid: the icon keeps its 20pt from the bar's left edge.
        assert icon[0] - bar[0] == pytest.approx(20.0)
    assert rtl_validate.page_crossings(before, docs) == []


def test_a_component_member_nested_in_a_group_is_measured_where_it_prints():
    """A form field's backdrop drawn inside another group: its path is written
    in that group's space. Measured there, the component's union seemed to
    straddle both pages, was mirrored about the spread centre, and the field
    printed on the facing page."""
    group_tx = 400.0
    # The backdrop prints at 70..300 on the right page; locally it reads
    # -330..-100, which is on the *left* page.
    docs = _docs(FACING,
                 _group("g", _rect("backdrop", 70 - group_tx, 300 - group_tx)
                        + _rect("art", 20 - group_tx, 60 - group_tx), tx=group_tx)
                 + _rect("field", 145, 447))
    before = _snapshot(docs)
    rtl.apply_plan(docs, _plan(
        _d("g", rtl_plan.RTL_MIRROR, type="Group"),
        _d("art", rtl_plan.KEEP_POSITION, rule="nested.carried"),
        _d("field", rtl_plan.RTL_MIRROR, component="field",
           component_kind="containment"),
        _d("backdrop", rtl_plan.KEEP_POSITION, component="field",
           component_kind="containment", position_bound=True,
           rule="component.bound")))
    extents = _extents(docs)
    field = _box(docs, "field")
    assert rtl.dominant_page(field, extents) == 1, "the field changed page"
    assert field[::2] == pytest.approx((PAGE_W - 447, PAGE_W - 145))
    assert rtl_validate.page_crossings(before, docs) == []
    # Carried by its group, not moved a second time on its own account: it
    # prints exactly where reflecting it about its page puts it, which is
    # where the group's own mirror already took it.
    assert _box(docs, "backdrop")[::2] == pytest.approx((PAGE_W - 300, PAGE_W - 70))


# ---- page furniture is never used to make room -----------------------------

def test_furniture_at_the_spine_is_not_moved_to_compensate():
    docs = _docs(FACING, _rect("tab", -10, 10) + _rect("bar", 400, PAGE_W + 13.5))
    tab = _box(docs, "tab")
    rtl.apply_plan(docs, _plan(
        _d("tab", rtl_plan.KEEP_POSITION, rule="master.item"),
        _d("bar", rtl_plan.RTL_MIRROR)))
    assert _box(docs, "tab") == tab
    assert _box(docs, "bar")[0] == pytest.approx(0.0)


def test_content_mirrored_about_a_narrowed_content_area_still_fits_its_page():
    """A side strip of fixed furniture moves the content axis off the page
    centre; an item reaching into the strip's side then reflects past the
    opposite trim unless it is held. The strip itself never moves."""
    strip_x0 = PAGE_W - 22
    docs = _docs(FACING, _rect("strip", strip_x0, PAGE_W, y0=-396, y1=396)
                 + _rect("panel", 300, 600))
    strip = _box(docs, "strip")
    before = _snapshot(docs)
    rtl.apply_plan(docs, _plan(
        _d("strip", rtl_plan.KEEP_POSITION, rule="structure.vertical_title"),
        _d("panel", rtl_plan.RTL_MIRROR)))
    assert _box(docs, "strip") == strip
    panel = _box(docs, "panel")
    assert panel[0] >= -TOL, "the panel crossed the spine"
    assert panel[2] - panel[0] == pytest.approx(300.0)
    assert rtl_validate.page_crossings(before, docs) == []


# ---- multi-page spreads ----------------------------------------------------

def _three_page_items():
    """Items on every page of a three-page spread, pressed against and past
    each page's edges -- including the middle page, which has a page on both
    sides."""
    items, ids = [], []
    for page, px0 in enumerate(THREE):
        px1 = px0 + PAGE_W
        for n, (a, b) in enumerate(((px0 + 5, px0 + 200),       # near left edge
                                    (px1 - 250, px1),            # flush right
                                    (px1 - 250, px1 + 13.5),     # bleeds right
                                    (px0 - 13.5, px0 + 250),     # bleeds left
                                    (px0 + 100, px1 - 60))):     # wide, inside
            self_id = f"p{page}i{n}"
            items.append(_rect(self_id, a, b))
            ids.append(self_id)
    return "".join(items), ids


def test_no_item_on_page_n_reaches_page_n_minus_1_or_n_plus_1():
    items, ids = _three_page_items()
    docs = _docs(THREE, items)
    before = _snapshot(docs)
    owner = {i: rtl.dominant_page(_box(docs, i), _extents(docs)) for i in ids}
    rtl.apply_plan(docs, _plan(*[_d(i, rtl_plan.RTL_MIRROR) for i in ids]))
    extents = _extents(docs)
    for i in ids:
        box = _box(docs, i)
        assert rtl.dominant_page(box, extents) == owner[i], i
        assert _neighbour_overlap(box, extents, owner[i]) <= TOL, i
    assert rtl_validate.page_crossings(before, docs) == []


def test_an_item_spanning_two_pages_is_left_to_span_them():
    """A banner across the gutter belongs to no single page, so there is no
    page to hold it to; containment must not drag it onto one."""
    docs = _docs(FACING, _rect("banner", -300, 300))
    rtl.apply_plan(docs, _plan(_d("banner", rtl_plan.RTL_MIRROR)))
    assert _box(docs, "banner")[::2] == pytest.approx((-300.0, 300.0))


# ---- the validator ---------------------------------------------------------

def test_page_crossings_reports_an_item_pushed_onto_the_facing_page():
    src = _docs(FACING, _rect("bar", 400, PAGE_W + 13.5))
    out = _snapshot(src)
    el = _el(out, "bar")
    el.set("ItemTransform", "1 0 0 1 -413.5 0")       # now -13.5 .. 212
    found = rtl_validate.page_crossings(src, out)
    assert len(found) == 1 and "bar" in found[0]


def test_page_crossings_ignores_an_overhang_the_source_already_had():
    """A frame the designer dragged past the spine and nothing moved is not
    something the transform introduced."""
    src = _docs(FACING, _rect("tail", -300, 20))
    assert rtl_validate.page_crossings(src, _snapshot(src)) == []
