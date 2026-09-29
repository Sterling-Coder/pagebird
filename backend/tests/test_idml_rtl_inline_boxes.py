"""Text set inside an inline box starts at the box's leading edge.

A problem box in this corpus is one inline group anchored in a story -- a
backdrop rectangle, the box outline, and a text frame holding the word problem
-- with the picture for that problem placed on the spread over the part of the
box the text frame leaves empty. The picture mirrors with the page. The group
is placed by text flow, and once its paragraph reads right to left InDesign
sets it against the frame's right edge, so the box itself lands mirrored. What
nothing moved was the text frame *inside* the box: it stayed on the left, which
is where the mirrored picture now is, and the problem printed underneath its
own graph (RCM07 U01 L04, pages 6-7).

Where a text frame sits inside its own backdrop is an indent, and an indent
turns with reading direction. Where labels sit around an equation is not, so
only a box -- backdrops spanning the whole group, text frames set inside them
-- is rearranged.
"""

from __future__ import annotations

import glob
import os

import pytest
from lxml import etree

from pagebirdy.idml import rtl, rtl_plan

SPREAD = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"/>
    <TextFrame Self="host" ParentStory="hs" ItemTransform="{host_transform}">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="36 -300"/><PathPointType Anchor="36 -150"/>
        <PathPointType Anchor="468 -150"/><PathPointType Anchor="468 -300"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </TextFrame>
  </Spread>
</idPkg:Spread>
"""

STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="hs">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/graphic problem box">
      <CharacterStyleRange>
        <Group Self="g" ItemTransform="1 0 0 1 -54 126">
          {children}
        </Group>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


def _shape(tag, self_id, x0, x1, extra=""):
    return f"""
    <{tag} Self="{self_id}" ItemTransform="1 0 0 1 0 0" {extra}>
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="{x0} -140"/><PathPointType Anchor="{x0} -20"/>
        <PathPointType Anchor="{x1} -20"/><PathPointType Anchor="{x1} -140"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </{tag}>"""


def _problem_box(text_x0=69, text_x1=391):
    return (_shape("Rectangle", "backdrop", 56, 576)
            + _shape("Polygon", "outline", 56, 576)
            + _shape("TextFrame", "tf", text_x0, text_x1, 'ParentStory="inner"'))


def _docs(children, host_transform="1 0 0 1 0 0"):
    return {
        "Spreads/S.xml": etree.fromstring(
            SPREAD.format(host_transform=host_transform).encode()),
        "Stories/Story_hs.xml": etree.fromstring(
            STORY.format(children=children).encode()),
    }


def _x_extent(docs, self_id):
    el = docs["Stories/Story_hs.xml"].find(f".//*[@Self='{self_id}']")
    box = rtl.item_bounds(el)
    return (round(box[0], 3), round(box[2], 3))


def _convert(docs):
    plan = rtl_plan.build_plan(docs, document="d", language="ar")
    rtl.apply_plan(docs, plan)
    return plan


def test_a_problem_box_is_rearranged_while_its_place_is_left_to_the_text_flow():
    docs = _docs(_problem_box())
    by = rtl_plan.build_plan(docs, document="d", language="ar").by_object()

    assert by["g"].action == rtl_plan.RTL_RESTRUCTURE
    assert by["g"].rule == "anchored.text_box"
    # The pieces are carried by the group's rearrangement, never on their own.
    assert [o for o in ("backdrop", "outline", "tf") if by[o].moves] == []


def test_the_text_frame_mirrors_within_its_box_and_the_box_stays():
    docs = _docs(_problem_box())
    _convert(docs)

    # 13pt in from the box's left edge in English, 13pt in from its right in
    # Arabic: the free half of the box, where the picture was, is now on the
    # left -- which is where the mirrored picture lands.
    assert _x_extent(docs, "tf") == (241.0, 563.0)
    assert _x_extent(docs, "backdrop") == (56.0, 576.0)
    assert _x_extent(docs, "outline") == (56.0, 576.0)


def test_an_outline_ruled_along_part_of_the_box_turns_with_the_text():
    # RCM07 L05 rules its box only as far as the problem's text runs; the
    # rule has to start at the box's new leading edge with it.
    docs = _docs(_shape("Rectangle", "backdrop", 56, 486)
                 + _shape("Polygon", "outline", 56, 396)
                 + _shape("TextFrame", "tf", 69, 370, 'ParentStory="inner"'))
    plan = _convert(docs)

    assert plan.by_object()["g"].rule == "anchored.text_box"
    assert _x_extent(docs, "backdrop") == (56.0, 486.0)
    assert _x_extent(docs, "outline") == (146.0, 486.0)
    assert _x_extent(docs, "tf") == (172.0, 473.0)


def test_a_group_already_symmetric_in_its_box_does_not_move():
    docs = _docs(_problem_box(text_x0=69, text_x1=563))
    _convert(docs)
    assert _x_extent(docs, "tf") == (69.0, 563.0)


def test_labels_placed_around_an_expression_are_not_a_box():
    # "slope" and "y-intercept" point at parts of an equation that keeps its
    # left-to-right order; mirroring the labels would detach them from it.
    docs = _docs(_shape("TextFrame", "eq", 100, 250, 'ParentStory="e"')
                 + _shape("TextFrame", "slope", 100, 140, 'ParentStory="s"')
                 + _shape("TextFrame", "intercept", 200, 300, 'ParentStory="i"'))
    plan = _convert(docs)

    assert plan.by_object()["g"].action == rtl_plan.KEEP_POSITION
    assert _x_extent(docs, "slope") == (100.0, 140.0)
    assert _x_extent(docs, "intercept") == (200.0, 300.0)


def test_a_picture_beside_its_text_is_not_a_backdrop():
    docs = _docs(_shape("Rectangle", "pic", 56, 200)
                 + _shape("TextFrame", "tf", 210, 576, 'ParentStory="inner"'))
    plan = _convert(docs)

    assert plan.by_object()["g"].action == rtl_plan.KEEP_POSITION
    assert _x_extent(docs, "pic") == (56.0, 200.0)


def test_a_box_in_a_frame_turned_off_the_page_is_left_as_drawn():
    # Inside a rotated frame the group's own x axis runs down the page, so a
    # reflection about it moves the text frame down rather than across.
    docs = _docs(_problem_box(), host_transform="0 -1 1 0 0 0")
    plan = _convert(docs)

    assert not plan.by_object()["g"].moves
    assert _x_extent(docs, "tf") == (69.0, 391.0)


# ---- the book the defect was reported on ----------------------------------

BOOK = "RCM07_NA_SW_U01_L04"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _book():
    hits = sorted(h for h in glob.glob(os.path.join(HERE, "uploads", f"{BOOK}-*.idml"))
                  if ".ar" not in os.path.basename(h))
    if not hits:
        pytest.skip(f"{BOOK} not in uploads/")
    return hits[0]


def _story_text(docs, story_id):
    tree = docs.get(f"Stories/Story_{story_id}.xml")
    return "" if tree is None else "".join(c.text or "" for c in tree.iter("Content"))


def _problem_boxes(docs, needle):
    """(group, text frame, backdrop) for each inline problem box whose text
    frame's story contains `needle`."""
    out = []
    for name, tree in docs.items():
        if not name.startswith("Stories/"):
            continue
        for group in tree.iter("Group"):
            frames = [c for c in group if rtl._is(c, "TextFrame")
                      and needle in _story_text(docs, c.get("ParentStory"))]
            backdrops = [c for c in group if rtl._is(c, "Rectangle")]
            if frames and backdrops:
                out.append((group, frames[0], backdrops[0]))
    return out


def _centre(box):
    return (box[0] + box[2]) / 2.0


def test_the_ignacio_problem_no_longer_prints_under_its_graph():
    from pagebirdy.idml.package import IdmlPackage

    path = _book()
    source = IdmlPackage(path).documents
    target_pkg = IdmlPackage(path)
    rtl.apply_rtl(target_pkg, document=BOOK, language="ar")
    target = target_pkg.documents

    before = _problem_boxes(source, "Ignacio")
    after = _problem_boxes(target, "Ignacio")
    assert len(before) == len(after) == 2

    for (_, tf0, bd0), (_, tf1, bd1) in zip(before, after):
        box0, box1 = rtl.item_bounds(bd0), rtl.item_bounds(bd1)
        text0, text1 = rtl.item_bounds(tf0), rtl.item_bounds(tf1)
        assert box1 == pytest.approx(box0, abs=0.01)
        # English sets the problem in the left of the box, beside a graph on
        # the right; Arabic sets it in the right, beside the mirrored graph.
        assert _centre(text0) < _centre(box0)
        assert _centre(text1) > _centre(box1)
        assert text1[0] - box1[0] == pytest.approx(box0[2] - text0[2], abs=0.01)
        assert box1[2] - text1[2] == pytest.approx(text0[0] - box0[0], abs=0.01)
