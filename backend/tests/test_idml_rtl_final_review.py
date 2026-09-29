"""Regressions for the defects the final whole-branch review found.

Each of these is a case where the plan, the debug log or the QA report claimed
something the shipped document did not do. The plan is meant to be the single
source of decision truth, so a promise it makes and the executor quietly drops
is worse than a wrong decision honestly recorded: nothing downstream can tell.
"""

import logging

import pytest
from lxml import etree

from pagebirdy.idml import rtl, rtl_features, rtl_plan, rtl_rules

SPREAD = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"/>
    {items}
  </Spread>
</idPkg:Spread>
"""


def _path(x0, y0, x1, y1):
    return f"""<Properties><PathGeometry><GeometryPathType PathOpen="false">
      <PathPointArray>
        <PathPointType Anchor="{x0} {y0}"/><PathPointType Anchor="{x0} {y1}"/>
        <PathPointType Anchor="{x1} {y1}"/><PathPointType Anchor="{x1} {y0}"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>"""


def _docs(items):
    return {"Spreads/S.xml": etree.fromstring(SPREAD.format(items=items).encode())}


def _el(docs, self_id):
    return docs["Spreads/S.xml"].find(f".//*[@Self='{self_id}']")


# ---- a KEEP_GEOMETRY frame keeps the side its properties name ---------------


def test_a_frame_that_stays_keeps_its_wrap_offset():
    """The frame did not move, so the type beside it must keep its bite.

    Flipping a stationary frame's wrap offset moves the gap in the text
    without moving the thing it was cut for.
    """
    from dataclasses import replace

    docs = _docs(f"""<Rectangle Self="fig" ItemTransform="1 0 0 1 0 0"
                      AppliedObjectStyle="ObjectStyle/math console">
        {_path(100, 0, 300, 120)}
        <TextWrapPreference><Properties>
          <TextWrapOffset Left="18" Right="0"/>
        </Properties></TextWrapPreference>
      </Rectangle>""")
    plan = rtl_plan.build_plan(docs, document="d", language="ar")
    plan.decisions = [replace(d, action=rtl_plan.KEEP_POSITION) for d in plan.decisions]

    rtl.apply_plan(docs, plan)
    changed = rtl.mirror_item_properties(docs, plan)

    offset = _el(docs, "fig").find(".//{*}TextWrapOffset")
    assert offset.get("Left") == "18"
    assert offset.get("Right") == "0"
    assert changed == 0


def test_a_frame_that_crosses_the_page_takes_its_wrap_offset_with_it():
    docs = _docs(f"""<Rectangle Self="fig" ItemTransform="1 0 0 1 0 0"
                      AppliedObjectStyle="ObjectStyle/math console">
        {_path(100, 0, 300, 120)}
        <TextWrapPreference><Properties>
          <TextWrapOffset Left="18" Right="0"/>
        </Properties></TextWrapPreference>
      </Rectangle>""")
    plan = rtl_plan.build_plan(docs, document="d", language="ar")
    assert plan.by_object()["fig"].moves

    rtl.apply_plan(docs, plan)
    rtl.mirror_item_properties(docs, plan, anchors=False)

    offset = _el(docs, "fig").find(".//{*}TextWrapOffset")
    assert offset.get("Left") == "0"
    assert offset.get("Right") == "18"


def test_a_document_wide_flip_is_still_what_the_legacy_engine_gets():
    """`plan=None` keeps the old behaviour for he/fa/ur, where all items move."""
    docs = _docs(f"""<Rectangle Self="fig" ItemTransform="1 0 0 1 0 0">
        {_path(100, 0, 300, 120)}
        <TextWrapPreference><Properties>
          <TextWrapOffset Left="18" Right="0"/>
        </Properties></TextWrapPreference>
      </Rectangle>""")
    assert rtl.mirror_item_properties(docs) == 1
    offset = _el(docs, "fig").find(".//{*}TextWrapOffset")
    assert offset.get("Left") == "0"
    assert offset.get("Right") == "18"


def test_an_anchored_objects_corner_flips_even_though_nothing_moved():
    """An anchor is measured against the text, not against the page.

    A problem number pinned to the corner where its sentence begins has to
    change corner when the sentence changes direction, and the page geometry
    has nothing to do with it. Gating this on movement -- as the wrap and inset
    corrections correctly are -- left every badge anchored `BottomRightAnchor`
    in a right-to-left paragraph, printing it at the end of the line it is
    supposed to introduce.
    """
    docs = _docs(f"""<TextFrame Self="body" ParentStory="st1"
                      ItemTransform="1 0 0 1 0 0">{_path(60, 0, 500, 200)}</TextFrame>""")
    docs["Stories/S.xml"] = etree.fromstring(b"""
      <idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
        <Story Self="st1">
          <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/STEM">
            <CharacterStyleRange>
              <Rectangle Self="badge" ItemTransform="1 0 0 1 0 0">
                <Properties><PathGeometry><GeometryPathType><PathPointArray>
                  <PathPointType Anchor="0 0"/><PathPointType Anchor="0 14"/>
                  <PathPointType Anchor="14 14"/><PathPointType Anchor="14 0"/>
                </PathPointArray></GeometryPathType></PathGeometry></Properties>
                <AnchoredObjectSetting AnchorPoint="BottomRightAnchor"/>
              </Rectangle>
              <Content>problem text</Content>
            </CharacterStyleRange>
          </ParagraphStyleRange>
        </Story>
      </idPkg:Story>""")

    from dataclasses import replace

    plan = rtl_plan.build_plan(docs, document="d", language="ar")
    # Hold every page item still: the point is that the anchor turns with
    # its text whether or not anything on the page moved.
    plan.decisions = [replace(d, action=rtl_plan.KEEP_POSITION) for d in plan.decisions]
    assert not any(d.moves for d in plan.decisions)

    rtl.apply_plan(docs, plan)
    rtl.mirror_item_properties(docs, plan)

    setting = docs["Stories/S.xml"].find(".//{*}AnchoredObjectSetting")
    assert setting.get("AnchorPoint") == "BottomLeftAnchor"


# ---- a promised flip either happens or is reported --------------------------


def test_a_group_is_not_ordered_to_turn_round():
    """`content_kind` credits a container with its children's content.

    A `<Group>` holding one photograph reads as `raster`, so it matched the
    decorative-bleed rule -- and `reflect_graphic` declines a group, so the
    plan printed MIRROR_GRAPHIC for a banner that shipped as drawn.
    """
    docs = _docs(f"""<Group Self="g" ItemTransform="1 0 0 1 -6 -400">
        <Rectangle Self="inner" ItemTransform="1 0 0 1 0 0">
          {_path(0, 0, 624, 130)}
          <Image Self="im" ItemTransform="1 0 0 1 0 0">
            <Link LinkResourceURI="file:/links/banner.jpg"/>
          </Image>
        </Rectangle>
      </Group>""")
    feats = {f.self_id: f for f in rtl_features.collect(docs)}
    assert feats["g"].content_kind == "raster"   # the misleading input remains
    assert feats["g"].full_bleed

    plan = rtl_plan.build_plan(docs, document="d", language="ar")
    assert plan.by_object()["g"].new_orientation == rtl_plan.KEEP_ORIENTATION
    assert plan.by_object()["g"].rule != "graphic.decorative_bleed"


def test_a_flip_the_executor_cannot_perform_is_counted_and_logged(caplog):
    """A refusal must never be silent: the plan says it happened."""
    docs = _docs(f"""<Group Self="g" ItemTransform="1 0 0 1 0 0">
        <Rectangle Self="inner" ItemTransform="1 0 0 1 0 0">{_path(0, 0, 60, 40)}</Rectangle>
      </Group>""")
    forced = rtl_plan.Decision(
        page=0, spread="spr", object="g", component=None, component_kind=None,
        type="Group", layer=None, object_style=None, paragraph_styles=(),
        bounds=None, new_bounds=None, orientation=rtl_plan.KEEP_ORIENTATION,
        new_orientation=rtl_plan.MIRROR_GRAPHIC,
        action=rtl_plan.MIRROR_GRAPHIC, text=rtl_plan.KEEP_TEXT,
        rule="graphic.decorative_bleed", reason="test")
    plan = rtl_plan.Plan(document="d", language="ar", rules_family="f",
                         decisions=[forced])

    with caplog.at_level(logging.WARNING):
        report = rtl.apply_plan(docs, plan)

    assert report["rtl_graphics_mirrored"] == 0
    assert report["rtl_graphics_refused"] == 1
    assert "cannot be turned round" in caplog.text


# ---- an anchored object is placed by text flow, not by page geometry --------


def test_an_anchored_object_is_never_given_a_positional_action():
    """`apply_plan` walks spreads, so an anchor's move could never execute."""
    story = etree.fromstring(b"""
      <idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
        <Story Self="st1">
          <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
            <CharacterStyleRange>
              <Rectangle Self="anchored" AppliedObjectStyle="ObjectStyle/callout bubble"
                         ItemTransform="1 0 0 1 0 0">
                <Properties><PathGeometry><GeometryPathType><PathPointArray>
                  <PathPointType Anchor="0 0"/><PathPointType Anchor="0 20"/>
                  <PathPointType Anchor="40 20"/><PathPointType Anchor="40 0"/>
                </PathPointArray></GeometryPathType></PathGeometry></Properties>
              </Rectangle>
              <Content>text</Content>
            </CharacterStyleRange>
          </ParagraphStyleRange>
        </Story>
      </idPkg:Story>""")
    docs = _docs("")
    docs["Stories/S.xml"] = story

    plan = rtl_plan.build_plan(docs, document="d", language="ar")
    d = plan.by_object()["anchored"]
    assert d.action == rtl_plan.KEEP_POSITION
    assert d.moves is False
    assert d.rule == "anchored.flowed"


# ---- the KEEP_GEOMETRY barrier binds descendants of a plain locked frame ----


def test_a_descendant_of_a_rigid_math_frame_never_moves_on_its_own():
    """A callout nested in a math frame is carried by the frame's move; a
    move of its own would pull it out of the diagram it annotates."""
    docs = _docs(f"""<Rectangle Self="fig" ItemTransform="1 0 0 1 0 0"
                      AppliedObjectStyle="ObjectStyle/math console">
        {_path(100, 0, 300, 120)}
        <Rectangle Self="callout" ItemTransform="1 0 0 1 0 0"
                   AppliedObjectStyle="ObjectStyle/callout bubble">
          {_path(120, 10, 180, 40)}
        </Rectangle>
      </Rectangle>""")
    plan = rtl_plan.build_plan(docs, document="d", language="ar")
    by = plan.by_object()
    assert by["fig"].moves and by["fig"].rigid
    assert by["callout"].moves is False
    assert by["callout"].rule == "nested.carried"


# ---- a malformed designmap cannot duplicate the document -------------------


def test_a_designmap_naming_one_spread_twice_does_not_duplicate_it():
    designmap = etree.fromstring(b"""
      <Document xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
        <idPkg:Spread src="Spreads/S.xml"/>
        <idPkg:Spread src="Spreads/S.xml"/>
      </Document>""")
    docs = _docs(f"""<Rectangle Self="a" ItemTransform="1 0 0 1 0 0">{_path(0, 0, 40, 20)}</Rectangle>""")
    docs["designmap.xml"] = designmap

    order = rtl_features._document_order(docs)
    assert order == ["Spreads/S.xml"]
    assert [f.self_id for f in rtl_features.collect(docs)] == ["a"]


# ---- the executor reads a structural field, not a rule name -----------------


def test_component_binding_is_a_field_not_a_rule_name():
    """Renaming a rule id must not change what the executor moves."""
    docs = _docs(f"""<Group Self="g" ItemTransform="1 0 0 1 0 0">
        <Rectangle Self="c1" ItemTransform="1 0 0 1 0 0">{_path(0, 0, 40, 20)}</Rectangle>
        <Rectangle Self="c2" ItemTransform="1 0 0 1 0 0">{_path(50, 0, 90, 20)}</Rectangle>
      </Group>""")
    plan = rtl_plan.build_plan(docs, document="d", language="ar")
    bound = [d for d in plan.decisions if d.position_bound]
    assert bound, "a group's non-anchor members should be position-bound"
    assert all(d.action == rtl_plan.KEEP_POSITION for d in bound)
    # The rule id still says so for a human reading the log, but nothing
    # branches on it.
    assert all(d.rule == "component.bound" for d in bound)
