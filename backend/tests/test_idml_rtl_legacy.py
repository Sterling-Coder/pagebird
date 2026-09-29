"""RTL layout for the IDML path: the whole-page mirror, not called by the pipeline.

`idml.rtl` was rewritten around a semantic, object-aware engine
(`idml.rtl_plan.build_plan` + `idml.rtl.apply_plan`), and then `idml.rtl.apply_rtl`
stopped calling any geometry engine at all -- production output is text-only
for every RTL target now. The original whole-page mirror this module tests
still ships, unchanged, as `idml.rtl_legacy`, reachable directly for
calibration work but not invoked from the pipeline. These tests moved from
`test_idml_rtl.py` verbatim -- only the import changed, aliasing
`rtl_legacy` as `rtl` so the bodies below read exactly as they did before the
split.
"""

import gc
import glob
import os

import pytest
from lxml import etree

from pagebirdy.idml import rtl as _rtl_shared
from pagebirdy.idml import rtl_legacy as rtl
from pagebirdy.idml.package import IdmlPackage

# A facing-page spread: two 612x783 pages meeting at x=0, so the spread runs
# -612..612 and its mirror axis is 0. Items are children of <Spread>, each
# placing its own path geometry through ItemTransform.
SPREAD = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="2" ItemTransform="1 0 0 1 0 0">
    <Page Self="pL" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 -612 -391.5"/>
    <Page Self="pR" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"/>
    {items}
  </Spread>
</idPkg:Spread>
"""

# A lone page occupying 0..612 -- the first page of a facing-pages document.
SINGLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"/>
    {items}
  </Spread>
</idPkg:Spread>
"""


def _rect(self_id, x0, y0, x1, y1, transform="1 0 0 1 0 0"):
    """A frame whose path is written in its own space and placed by transform."""
    return f"""
    <Rectangle Self="{self_id}" ItemTransform="{transform}">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="{x0} {y0}"/>
        <PathPointType Anchor="{x0} {y1}"/>
        <PathPointType Anchor="{x1} {y1}"/>
        <PathPointType Anchor="{x1} {y0}"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </Rectangle>"""


def _spread(items, template=SPREAD):
    return etree.fromstring(template.format(items=items).encode()).find("Spread")


def _item(spread, self_id):
    return spread.find(f".//*[@Self='{self_id}']")


def _bounds(spread, self_id):
    return rtl.item_bounds(_item(spread, self_id))


# ---- the mirror ------------------------------------------------------------


def test_item_reflects_inside_its_own_page():
    # 40..240 sits on the right page (0..612), so it reflects about 306.
    spread = _spread(_rect("a", 40, 100, 240, 200))
    rtl.mirror_spread(spread)
    assert _bounds(spread, "a") == pytest.approx((372, 100, 572, 200))


def test_an_item_never_crosses_the_gutter_to_the_other_page():
    # A frame 45pt in from the left page's outer edge ends up 45pt in from that
    # same page's spine edge. Mirroring about the spread centre instead would
    # land it on the right page and swap the two pages of the spread.
    spread = _spread(_rect("a", -567, 100, -400, 200))
    rtl.mirror_spread(spread)
    x0, _, x1, _ = _bounds(spread, "a")
    assert (x0, x1) == pytest.approx((-212, -45))
    assert x1 <= 0, "item left its own page"


def test_both_pages_of_a_spread_keep_their_content():
    # The left page's frame stays left and the right page's stays right, so
    # page order survives the mirror.
    spread = _spread(_rect("L", -567, 0, -400, 50) + _rect("R", 45, 0, 212, 50))
    rtl.mirror_spread(spread)
    assert _bounds(spread, "L")[2] <= 0
    assert _bounds(spread, "R")[0] >= 0


def test_an_item_spanning_the_gutter_keeps_covering_the_spread():
    spread = _spread(_rect("a", -500, 0, 500, 50))
    rtl.mirror_spread(spread)
    assert _bounds(spread, "a") == pytest.approx((-500, 0, 500, 50))


def test_a_pasteboard_item_is_not_moved():
    spread = _spread(_rect("a", 700, 0, 800, 50))
    before = _item(spread, "a").get("ItemTransform")
    assert rtl.mirror_spread(spread) == 0
    assert _item(spread, "a").get("ItemTransform") == before


def test_mirror_preserves_width_height_and_vertical_position():
    spread = _spread(_rect("a", 40, 100, 240, 205))
    before = _bounds(spread, "a")
    rtl.mirror_spread(spread)
    after = _bounds(spread, "a")
    assert after[2] - after[0] == pytest.approx(before[2] - before[0])
    assert after[3] - after[1] == pytest.approx(before[3] - before[1])
    assert (after[1], after[3]) == (before[1], before[3])


def test_mirror_never_negates_the_matrix_so_content_is_not_flipped():
    # Composing a reflection would give a=-1 and render the text backwards.
    # Only the translation may change.
    spread = _spread(_rect("a", 40, 100, 240, 200, transform="1 0 0 1 30 15"))
    rtl.mirror_spread(spread)
    a, b, c, d, _, ty = rtl.parse_transform(_item(spread, "a").get("ItemTransform"))
    assert (a, b, c, d) == (1.0, 0.0, 0.0, 1.0)
    assert ty == 15.0


def test_rotation_survives_the_mirror():
    # 90-degree rotation: "0 1 -1 0 tx ty". The glyphs must stay rotated the
    # same way, not counter-rotated, so a b c d are untouched.
    spread = _spread(_rect("a", 0, 0, 100, 20, transform="0 1 -1 0 300 -50"))
    before = _bounds(spread, "a")
    rtl.mirror_spread(spread)
    t = rtl.parse_transform(_item(spread, "a").get("ItemTransform"))
    assert t[:4] == (0.0, 1.0, -1.0, 0.0)
    after = _bounds(spread, "a")
    # The rotated box keeps its footprint and reflects as a whole, about the
    # centre of the right page (306) that it sits on.
    assert after[2] - after[0] == pytest.approx(before[2] - before[0])
    assert after[0] == pytest.approx(2 * 306 - before[2])


def test_scaling_survives_the_mirror():
    spread = _spread(_rect("a", 0, 0, 100, 50, transform="2 0 0 3 100 10"))
    rtl.mirror_spread(spread)
    t = rtl.parse_transform(_item(spread, "a").get("ItemTransform"))
    assert t[:4] == (2.0, 0.0, 0.0, 3.0)
    x0, y0, x1, y1 = _bounds(spread, "a")
    assert (x1 - x0, y1 - y0) == pytest.approx((200, 150))


def test_pages_themselves_never_move():
    spread = _spread(_rect("a", 40, 100, 240, 200))
    before = [p.get("ItemTransform") for p in spread if rtl._is(p, "Page")]
    rtl.mirror_spread(spread)
    assert [p.get("ItemTransform") for p in spread if rtl._is(p, "Page")] == before


def test_mirroring_twice_returns_to_the_source_layout():
    spread = _spread(_rect("a", 40, 100, 240, 200) + _rect("b", -500, 10, -300, 60))
    before = {i: _bounds(spread, i) for i in ("a", "b")}
    rtl.mirror_spread(spread)
    rtl.mirror_spread(spread)
    for i in ("a", "b"):
        assert _bounds(spread, i) == pytest.approx(before[i])


# ---- groups ----------------------------------------------------------------

GROUP = """
    <Group Self="g" ItemTransform="1 0 0 1 100 0">
      {children}
    </Group>"""


def _group(children, transform="1 0 0 1 100 0"):
    return GROUP.replace('ItemTransform="1 0 0 1 100 0"',
                         f'ItemTransform="{transform}"').format(children=children)


def test_group_mirrors_as_one_unit():
    # icon at 0..40, label at 50..250, both inside a group placed at +100.
    spread = _spread(_group(_rect("icon", 0, 0, 40, 40) + _rect("label", 50, 0, 250, 40)))
    rtl.mirror_spread(spread)
    # Group spans 100..350 on the right page, so about 306 it becomes 262..512.
    assert _bounds(spread, "g") == pytest.approx((262, 0, 512, 40))


def test_group_children_are_mirrored_within_the_group():
    """The badge and its label swap ends.

    A callout is a bar, a label and an icon pinned to the end the sentence
    starts at. Moving the group and leaving its composition alone puts that
    icon at the end of an Arabic sentence instead of the beginning.
    """
    spread = _spread(_group(_rect("icon", 0, 0, 40, 40) + _rect("label", 50, 0, 250, 40)))
    rtl.mirror_spread(spread)
    icon, label = _bounds(spread, "icon"), _bounds(spread, "label")
    assert label[2] <= icon[0]


def test_mirroring_a_group_leaves_its_bounds_where_the_mirror_put_them():
    """Children reflect about the group's own centre, so the group's outline is
    unchanged by the recursion -- only the arrangement inside it."""
    spread = _spread(_group(_rect("icon", 0, 0, 40, 40) + _rect("label", 50, 0, 250, 40)))
    rtl.mirror_spread(spread)
    assert _bounds(spread, "g") == pytest.approx((262, 0, 512, 40))


def test_a_group_child_keeps_its_own_matrix():
    """Only `tx` moves. Negating a child's matrix would flip its content --
    backwards type, a reversed photograph -- one level down from the trap the
    page-level mirror exists to avoid."""
    spread = _spread(_group(_rect("icon", 0, 0, 40, 40, transform="0 1 -1 0 5 5")))
    rtl.mirror_spread(spread)
    assert rtl.parse_transform(
        _item(spread, "icon").get("ItemTransform"))[:4] == (0.0, 1.0, -1.0, 0.0)


def test_a_lone_child_does_not_move_inside_its_group():
    """It already spans the group, so its reflection about the group centre is
    itself. The group's own move is what carries it across the page."""
    spread = _spread(_group(_rect("only", 0, 0, 60, 30), transform="1 0 0 1 200 0"))
    before = _item(spread, "only").get("ItemTransform")
    rtl.mirror_spread(spread)
    assert _item(spread, "only").get("ItemTransform") == before
    assert _bounds(spread, "g") == pytest.approx((352, 0, 412, 30))


def test_nested_groups_mirror_at_every_level():
    inner = _group(_rect("a", 0, 0, 20, 30) + _rect("b", 30, 0, 60, 30),
                   transform="1 0 0 1 20 0")
    spread = _spread(f'<Group Self="outer" ItemTransform="1 0 0 1 200 0">{inner}</Group>')
    rtl.mirror_spread(spread)
    # outer spans 220..280 on the right page -> 332..392, and inside it the two
    # leaves swap.
    assert _bounds(spread, "outer") == pytest.approx((332, 0, 392, 30))
    assert _bounds(spread, "b")[2] <= _bounds(spread, "a")[0]


def test_mirroring_a_group_twice_is_the_identity():
    spread = _spread(_group(_rect("icon", 0, 0, 40, 40) + _rect("label", 50, 0, 250, 40)))
    before = {k: _item(spread, k).get("ItemTransform") for k in ("g", "icon", "label")}
    rtl.mirror_spread(spread)
    rtl.mirror_spread(spread)
    for k, v in before.items():
        assert rtl.parse_transform(_item(spread, k).get("ItemTransform")) ==             pytest.approx(rtl.parse_transform(v))


def test_a_horizontal_run_of_text_frames_keeps_its_order():
    """A number bond or an equation is built from sibling frames sitting on one
    line: `___ + ___ = ___`. Reflecting siblings reverses their visual order,
    which prints the expression backwards, so a group shaped like a sequence of
    text is moved but never rearranged."""
    frames = "".join(
        f'<TextFrame Self="t{i}" ParentStory="s{i}" ItemTransform="1 0 0 1 0 0">'
        '<Properties><PathGeometry><GeometryPathType><PathPointArray>'
        f'<PathPointType Anchor="{i * 60} 0"/><PathPointType Anchor="{i * 60} 20"/>'
        f'<PathPointType Anchor="{i * 60 + 40} 20"/><PathPointType Anchor="{i * 60 + 40} 0"/>'
        '</PathPointArray></GeometryPathType></PathGeometry></Properties></TextFrame>'
        for i in range(3))
    spread = _spread(_group(frames, transform="1 0 0 1 100 0"))
    rtl.mirror_spread(spread)
    assert _bounds(spread, "t0")[0] < _bounds(spread, "t1")[0] < _bounds(spread, "t2")[0]


def test_a_stack_of_text_frames_is_still_mirrored():
    """Two labels above one another are not a sequence -- nothing about their
    order is reversed by a mirror -- so the group mirrors normally."""
    frames = (
        '<TextFrame Self="top" ParentStory="s1" ItemTransform="1 0 0 1 0 0">'
        '<Properties><PathGeometry><GeometryPathType><PathPointArray>'
        '<PathPointType Anchor="0 0"/><PathPointType Anchor="0 20"/>'
        '<PathPointType Anchor="40 20"/><PathPointType Anchor="40 0"/>'
        '</PathPointArray></GeometryPathType></PathGeometry></Properties></TextFrame>'
        '<TextFrame Self="bottom" ParentStory="s2" ItemTransform="1 0 0 1 0 0">'
        '<Properties><PathGeometry><GeometryPathType><PathPointArray>'
        '<PathPointType Anchor="60 40"/><PathPointType Anchor="60 60"/>'
        '<PathPointType Anchor="200 60"/><PathPointType Anchor="200 40"/>'
        '</PathPointArray></GeometryPathType></PathGeometry></Properties></TextFrame>')
    spread = _spread(_group(frames, transform="1 0 0 1 100 0"))
    rtl.mirror_spread(spread)
    assert _bounds(spread, "bottom")[0] < _bounds(spread, "top")[0]


def test_form_controls_are_measured_from_their_bounding_box():
    # A CheckBox declares no PathGeometry -- its appearance lives in <State>
    # children -- so reading only PathGeometry left every checkbox on a
    # worksheet stranded on the old binding edge.
    checkbox = """
    <CheckBox Self="cb" ItemTransform="1 0 0 1 200 0">
      <Properties><PathBoundingBox Left="-5" Top="-5" Right="5" Bottom="5"/></Properties>
      <State Self="cbi" Active="true"/>
    </CheckBox>"""
    spread = _spread(checkbox)
    assert _bounds(spread, "cb") == pytest.approx((195, -5, 205, 5))
    assert rtl.mirror_spread(spread) == 1
    assert _bounds(spread, "cb") == pytest.approx((407, -5, 417, 5))


# ---- package-level ---------------------------------------------------------


def test_packaging_wrapper_is_not_mistaken_for_a_page_item():
    # Every Spreads/*.xml is rooted in <idPkg:Spread>, whose local name matches
    # the real <Spread> inside it. Treating the wrapper as a spread would make
    # the real spread look like one of its page items and mirror everything a
    # second time via its container.
    root = etree.fromstring(SPREAD.format(items=_rect("a", 40, 0, 240, 50)).encode())
    spread = root.find("Spread")
    before = spread.get("ItemTransform")
    # Exactly one item moves -- the rectangle -- and the spread itself is not
    # dragged along as though it were an item on some outer spread.
    assert rtl.mirror_geometry({"Spreads/S.xml": root}) == 1
    assert spread.get("ItemTransform") == before


def test_mirror_geometry_covers_master_spreads():
    # Folios and running heads live on masters; leaving them behind would
    # strand the page number on the old binding edge.
    root = etree.fromstring(SPREAD.format(items=_rect("a", 40, 0, 240, 50)).encode())
    assert rtl.mirror_geometry({"MasterSpreads/M.xml": root}) == 1


def test_spread_without_pages_is_left_alone():
    # No pages means no axis to reflect about; guessing one would scatter the
    # pasteboard.
    root = etree.fromstring(
        SPREAD.format(items=_rect("a", 40, 0, 240, 50)).encode())
    spread = root.find("Spread")
    for page in [p for p in spread if rtl._is(p, "Page")]:
        spread.remove(page)
    before = _item(spread, "a").get("ItemTransform")
    assert rtl.mirror_geometry({"Spreads/S.xml": root}) == 0
    assert _item(spread, "a").get("ItemTransform") == before


# ---- real documents --------------------------------------------------------

# Smallest first: a parsed IdmlPackage costs roughly 30x the file on the heap,
# and holding several at once exhausts the interpreter. The fixture below keeps
# at most one alive.
_SAMPLES = sorted(glob.glob(os.path.join(
    os.path.dirname(__file__), "..", "uploads", "*.idml")), key=os.path.getsize)


@pytest.fixture
def sample():
    """A freshly parsed sample package, released before the next test.

    The package holds every zip entry plus a parsed tree per story and spread --
    around 30MB for the smallest sample. Dropping the reference is not enough:
    the buffers must be cleared and collected here, or the peak carries into
    later tests and pushes the image-heavy OCR suite into a MemoryError on this
    interpreter.
    """
    if not _SAMPLES:
        pytest.skip("no sample IDML available")
    pkg = IdmlPackage(_SAMPLES[0])
    yield pkg
    for buffer in (pkg._entries, pkg._docs, pkg._stories, pkg._node_index):
        buffer.clear()
    del pkg
    gc.collect()


@pytest.mark.skipif(not _SAMPLES, reason="no sample IDML available")
def test_real_idml_mirrors_without_distorting_any_object(sample):
    """On a real 34-page textbook: every object reflects, none is distorted."""
    pkg = sample
    before = {}
    for name, tree in pkg.documents.items():
        if not name.startswith(("Spreads/", "MasterSpreads/")):
            continue
        for spread in tree.iter("Spread", "MasterSpread"):
            extents = rtl.page_extents(spread)
            if not extents:
                continue
            centre = rtl.spread_axis(spread)
            for el in spread:
                if not rtl._is_page_item(el):
                    continue
                box = rtl.item_bounds(el)
                if box is None:
                    continue
                before[id(el)] = (
                    rtl.parse_transform(el.get("ItemTransform")), box,
                    rtl.mirror_axis_for(box, extents, centre), el, extents)

    assert before, "sample has no page items"
    top_level = sum(1 for _, _, axis, _, _ in before.values() if axis is not None)
    moved = rtl.mirror_geometry(pkg.documents)
    # `moved` counts the children mirrored inside groups too, and those are
    # nested rather than spread children, so they never appear in `before`.
    assert moved >= top_level

    for matrix, box, axis, el, extents in before.values():
        after_matrix = rtl.parse_transform(el.get("ItemTransform"))
        after_box = rtl.item_bounds(el)
        assert after_matrix[:4] == matrix[:4], "content was flipped or rescaled"
        assert after_matrix[5] == matrix[5], "item moved vertically"
        assert after_box[2] - after_box[0] == pytest.approx(box[2] - box[0])
        assert after_box[3] - after_box[1] == pytest.approx(box[3] - box[1])
        if axis is None:
            assert after_box == pytest.approx(box), "pasteboard item moved"
        else:
            dx = 2 * axis - (box[0] + box[2])
            assert after_box[0] == pytest.approx(box[0] + dx)


@pytest.mark.skipif(not _SAMPLES, reason="no sample IDML available")
def test_a_zero_width_item_mirrors_like_any_other():
    """A vertical rule has no width, so it overlaps its page by exactly zero.
    An area test reads that as pasteboard furniture and leaves it behind --
    which strands the divider at the top of a worksheet page on the old side
    while the labels either side of it swap."""
    spread = _spread(_rect("rule", 100, -50, 100, 50))
    rtl.mirror_spread(spread)
    assert _bounds(spread, "rule")[0] == pytest.approx(512.0)


def test_a_zero_width_item_on_the_pasteboard_is_still_left_alone():
    spread = _spread(_rect("parked", 900, -50, 900, 50))
    rtl.mirror_spread(spread)
    assert _bounds(spread, "parked")[0] == pytest.approx(900.0)


def test_a_zero_width_item_on_the_spine_mirrors_about_the_spread():
    """Touching both pages, it belongs to neither, so it reflects about the
    spread centre exactly as a gutter-spanning banner does."""
    spread = _spread(_rect("spine", 0, -50, 0, 50))
    rtl.mirror_spread(spread)
    assert _bounds(spread, "spine")[0] == pytest.approx(0.0)


def test_a_rotated_group_is_moved_but_never_rearranged():
    """The failure `validate_rtl_idml` found in a real book.

    A child's `tx` runs along its *group's* horizontal. Under a 90-degree group
    that points down the page, so reflecting the children mirrors them
    vertically -- three badges in a rotated strip swapped top for bottom. A
    mirror about a vertical axis may never move anything vertically.
    """
    group = f"""
    <Group Self="g" ItemTransform="0 1 -1 0 300 -100">
      {_rect("a", 0, 0, 40, 40)}{_rect("b", 60, 0, 100, 40)}
    </Group>"""
    spread = _spread(group)
    before = {k: _bounds(spread, k) for k in ("a", "b")}
    rtl.mirror_spread(spread)
    after = {k: _bounds(spread, k) for k in ("a", "b")}
    # The group travelled, so both children travelled with it by the same
    # amount -- but neither swapped with the other, and neither moved in y.
    assert after["a"][1] == before["a"][1] and after["b"][1] == before["b"][1]
    assert (after["b"][0] - after["a"][0]) == pytest.approx(
        before["b"][0] - before["a"][0])


def test_a_group_rotated_back_into_square_mirrors_again():
    """The test is against where the group really sits, not its own matrix: a
    nested group that undoes its parent's rotation is square with the page."""
    inner = f"""
      <Group Self="inner" ItemTransform="0 -1 1 0 0 0">
        {_rect("a", 0, 0, 40, 40)}{_rect("b", 60, 0, 100, 40)}
      </Group>"""
    spread = _spread(f"""
    <Group Self="outer" ItemTransform="0 1 -1 0 300 -100">{inner}</Group>""")
    before = _bounds(spread, "a")
    rtl.mirror_spread(spread)
    after = _bounds(spread, "a")
    assert after[0] != pytest.approx(before[0]), "square group was not mirrored"


def _nest(outer: str, inner: str) -> str:
    """Put one page item inside another, the way a frame holds a child frame."""
    head, _, tail = outer.rpartition("</Rectangle>")
    return head + inner + "</Rectangle>" + tail


def test_a_frame_holding_a_nested_frame_stays_on_its_page():
    """The failure `validate_rtl_idml` found in RCM07 U01 L03.

    Two rectangles of a graphic organiser, each holding a child rectangle,
    were reflected about the union of both paths. The extra shift moved them
    off the right page and across the gutter, and grew their group by the
    same amount -- reported as `items resized` and `items changed page`.
    """
    spread = _spread(_nest(_rect("outer", 337, 0, 574, 40),
                           _rect("inner", 100, 0, 150, 40)))
    rtl.mirror_spread(spread)
    x0, _, x1, _ = _bounds(spread, "outer")
    assert (x0, x1) == pytest.approx((38.0, 275.0))
    assert x0 >= 0, "the frame crossed onto the facing page"


def test_a_frame_overhanging_the_spine_stays_on_its_page_through_the_mirror():
    # End to end: the frame's outer margin becomes its spine margin, and the
    # overhang moves to the outer edge instead of onto the facing page.
    spread = _spread(_rect("q4", -576.0, 246.8, 47.5, 282.8))
    rtl.mirror_spread(spread)
    x0, _, x1, _ = _bounds(spread, "q4")
    assert (x0, x1) == pytest.approx((-659.5, -36.0))
    assert x1 <= 0, "the frame crossed onto the facing page"


def test_a_bleeding_band_keeps_the_footprint_it_had_on_its_page():
    """The sidebar band of a real book: 64.5pt on the page and 13.5pt of bleed
    hanging off the outer edge, mirrored to 64.5pt on the other side with the
    bleed hanging off the other edge.

    Nudging the band back onto the sheet instead -- to keep its overhang clear
    of the spine -- widens what it covers from 64.5pt to 78pt, and the tools
    column mirrored to sit beside it lands underneath it. There is nothing to
    keep clear of: the target is bound right-to-left, and InDesign reverses
    the spread and carries each page's items with it, so the edge the bleed
    hangs off after the mirror is an outer edge again.
    """
    spread = _spread(_rect("band", 547.5, -50, 625.5, 50))
    rtl.mirror_spread(spread)
    x0, _, x1, _ = _bounds(spread, "band")
    assert x1 == pytest.approx(64.5), "the band's inner edge moved"
    assert x0 == pytest.approx(-13.5), "the bleed did not follow the band"


def test_a_bleed_mirrors_without_resizing_its_item():
    """The mirror is a translation, so the guarantee that it never changes an
    item's size holds for a bleeding item too."""
    spread = _spread(_rect("band", 2, -50, 625.5, 50))
    before = _bounds(spread, "band")
    rtl.mirror_spread(spread)
    after = _bounds(spread, "band")
    assert after[2] - after[0] == pytest.approx(before[2] - before[0])
    assert (after[1], after[3]) == pytest.approx((before[1], before[3]))


def test_a_bleed_on_a_single_page_spread_mirrors_freely():
    """With no facing page, both edges of the sheet are outer edges."""
    spread = _spread(_rect("band", 2, -50, 625.5, 50), template=SINGLE)
    rtl.mirror_spread(spread)
    assert _bounds(spread, "band")[0] == pytest.approx(-13.5)


def test_an_item_wholly_inside_its_page_mirrors_in_place():
    spread = _spread(_rect("box", 100, -50, 200, 50))
    rtl.mirror_spread(spread)
    assert _bounds(spread, "box") == pytest.approx((412, -50, 512, 50))


def _within(box, px0, px1):
    """True when `box` sits inside the page horizontally, to float tolerance."""
    return box[0] >= px0 - rtl._OVERLAP_EPS and box[2] <= px1 + rtl._OVERLAP_EPS


def test_real_idml_keeps_every_object_on_its_original_page(sample):
    """The regression that mattered: a facing spread must not swap its pages."""
    pkg = sample
    tracked = []
    for name, tree in pkg.documents.items():
        if not name.startswith(("Spreads/", "MasterSpreads/")):
            continue
        for spread in tree.iter("Spread", "MasterSpread"):
            extents = rtl.page_extents(spread)
            if len(extents) < 2:
                continue
            for el in spread:
                if not rtl._is_page_item(el):
                    continue
                box = rtl.item_bounds(el)
                if box is None:
                    continue
                # Only items that sit wholly on one page have a page to keep.
                # Containment is measured to `_OVERLAP_EPS`, the same tolerance
                # the mirror itself uses: a frame set flush to a page edge comes
                # out of the transform arithmetic at 612.0000000000001, and a
                # bare `<=` reads that float noise as a real crossing.
                on = [i for i, (px0, px1) in enumerate(extents)
                      if _within(box, px0, px1)]
                if len(on) == 1:
                    tracked.append((el, on[0], extents))

    assert tracked, "sample has no facing spreads"
    rtl.mirror_geometry(pkg.documents)
    for el, page_index, extents in tracked:
        px0, px1 = extents[page_index]
        box = rtl.item_bounds(el)
        assert _within(box, px0, px1), "object crossed to another page"


@pytest.mark.skipif(not _SAMPLES, reason="no sample IDML available")
def test_real_idml_mirror_is_its_own_inverse(sample):
    """For an item that sits wholly on one page, mirroring twice restores it.

    Scoped to those deliberately: an item bleeding past the spine can land on a
    different page's rule after the first mirror, so the second uses a
    different axis. The corpus has no such item, but the property is not
    universal and the test should not pretend otherwise.
    """
    pkg = sample
    before = {}
    for name, tree in pkg.documents.items():
        if name.startswith(("Spreads/", "MasterSpreads/")):
            for spread in tree.iter("Spread", "MasterSpread"):
                extents = rtl.page_extents(spread)
                for el in spread:
                    if not rtl._is_page_item(el):
                        continue
                    box = rtl.item_bounds(el)
                    if box is None or not any(
                            _within(box, px0, px1) for px0, px1 in extents):
                        continue
                    before[id(el)] = (el, el.get("ItemTransform"))

    rtl.mirror_geometry(pkg.documents)
    rtl.mirror_geometry(pkg.documents)
    for el, transform in before.values():
        assert rtl.parse_transform(el.get("ItemTransform")) == pytest.approx(
            rtl.parse_transform(transform))


@pytest.mark.skipif(not _SAMPLES, reason="no sample IDML available")
def test_mirrored_idml_still_opens_as_valid_xml(sample, tmp_path):
    pkg = sample
    rtl.mirror_geometry(pkg.documents)
    prefs = pkg.document("Resources/Preferences.xml")
    pkg.document("Resources/Styles.xml")
    # `set_text_direction` is not part of the legacy geometry pass -- it is
    # shared by both engines and lives only in `idml.rtl` -- so this one call
    # reaches the real module rather than the re-exported subset.
    _rtl_shared.set_text_direction(pkg.documents, prefs)

    out = str(tmp_path / "mirrored.idml")
    pkg.save(out)

    import zipfile

    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        names = z.namelist()
        # IDML requires an uncompressed mimetype entry first.
        assert names[0] == "mimetype"
        assert z.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        for name in names:
            if name.endswith(".xml"):
                etree.fromstring(z.read(name))  # raises on malformed XML
