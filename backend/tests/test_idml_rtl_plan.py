"""The plan is the single source of decision truth."""

import json

from pagebirdy.idml import rtl_plan


def _decision(**over):
    base = dict(
        page=3, spread="Spread_u851", object="u872", component=None,
        type="TextFrame", layer="ub7", object_style="$ID/[Normal Text Frame]",
        paragraph_styles=("_Master Page Styles:FL LESSON",),
        bounds=(501.8, -325.8, 560.3, -308.6), new_bounds=None,
        orientation=rtl_plan.KEEP_ORIENTATION,
        new_orientation=rtl_plan.KEEP_ORIENTATION,
        action=rtl_plan.KEEP_POSITION, text=rtl_plan.TEXT_RTL,
        rule="master.lesson_badge",
        reason="structural RTL element remains on right")
    base.update(over)
    return rtl_plan.Decision(**base)


def test_plan_round_trips_through_json():
    plan = rtl_plan.Plan(document="d.idml", language="ar",
                         rules_family="curriculum-associates-rcm",
                         decisions=[_decision()])
    back = rtl_plan.Plan.from_json(plan.to_json())
    assert back == plan


def test_json_is_stable_and_readable():
    plan = rtl_plan.Plan(document="d.idml", language="ar",
                         rules_family="fam", decisions=[_decision()])
    blob = json.loads(plan.to_json())
    assert blob["decisions"][0]["action"] == "KEEP_POSITION"
    assert blob["decisions"][0]["reason"].startswith("structural")


def test_every_position_orientation_combination_is_representable():
    combos = [
        (rtl_plan.KEEP_POSITION, rtl_plan.KEEP_ORIENTATION),
        (rtl_plan.RTL_REPOSITION, rtl_plan.KEEP_ORIENTATION),
        (rtl_plan.KEEP_POSITION, rtl_plan.MIRROR_GRAPHIC),
        (rtl_plan.RTL_REPOSITION, rtl_plan.MIRROR_GRAPHIC),
    ]
    for action, orientation in combos:
        d = _decision(action=action, new_orientation=orientation)
        assert d.action == action
        assert d.new_orientation == orientation


def test_log_line_carries_page_object_action_and_reason():
    plan = rtl_plan.Plan(document="d.idml", language="ar",
                         rules_family="fam", decisions=[_decision()])
    (line,) = plan.log_lines()
    assert "Page 3" in line
    assert "u872" in line
    assert "KEEP_POSITION" in line
    assert "structural RTL element remains on right" in line


def test_log_line_says_unchanged_rather_than_repeating_bounds():
    plan = rtl_plan.Plan(document="d.idml", language="ar",
                         rules_family="fam", decisions=[_decision()])
    (line,) = plan.log_lines()
    assert "unchanged" in line


from lxml import etree

from pagebirdy.idml import rtl_rules

SINGLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"/>
    {items}
  </Spread>
</idPkg:Spread>
"""


def _rect(self_id, x0, y0, x1, y1, extra=""):
    return f"""
    <Rectangle Self="{self_id}" ItemTransform="1 0 0 1 0 0" {extra}>
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="{x0} {y0}"/><PathPointType Anchor="{x0} {y1}"/>
        <PathPointType Anchor="{x1} {y1}"/><PathPointType Anchor="{x1} {y0}"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </Rectangle>"""


def _docs(items):
    return {"Spreads/S.xml": etree.fromstring(SINGLE.format(items=items).encode())}


def test_every_object_gets_exactly_one_decision():
    plan = rtl_plan.build_plan(_docs(_rect("a", 0, 0, 50, 20)
                                     + _rect("b", 300, 0, 350, 20)),
                              document="d.idml", language="ar")
    assert sorted(d.object for d in plan.decisions) == ["a", "b"]


def test_an_unrecognised_object_mirrors_in_every_rtl_language():
    for language in ("ar", "he", "fa", "ur"):
        plan = rtl_plan.build_plan(_docs(_rect("lonely", 10, 0, 60, 20)),
                                   document="d.idml", language=language)
        (d,) = plan.decisions
        assert d.action == rtl_plan.RTL_MIRROR, language
        assert d.rule == "default.mirror"


def test_build_plan_classifies_and_leaves_geometry_to_the_executor():
    # `build_plan` seeds `new_bounds` with the source `bounds` and leaves the
    # reflected geometry to `apply_plan`.
    plan = rtl_plan.build_plan(_docs(_rect("lonely", 10, 0, 60, 20)),
                               document="d.idml", language="ar")
    (d,) = plan.decisions
    assert d.new_bounds == d.bounds


def test_every_object_on_a_plain_page_mirrors_whatever_the_language():
    items = "".join(_rect(f"r{i}", i * 60, 0, i * 60 + 50, 20) for i in range(8))
    for language in ("ar", "he"):
        plan = rtl_plan.build_plan(_docs(items), document="d.idml", language=language)
        assert [d for d in plan.decisions if d.moves] == plan.decisions


def test_every_object_in_a_plain_page_is_repositioned_for_arabic():
    # The AR-gated counterpart: the same page of ordinary frames, for the one
    # language/family combination with a calibrated reference corpus, moves
    # every object -- none of them is recognised by any rule but the
    # AR-gated catch-all.
    items = "".join(_rect(f"r{i}", i * 60, 0, i * 60 + 50, 20) for i in range(8))
    plan = rtl_plan.build_plan(_docs(items), document="d.idml", language="ar")
    assert [d for d in plan.decisions if d.moves] == plan.decisions


def test_component_members_inherit_the_component_decision():
    # Two members whose own properties would independently match different
    # rules -- "arrow" carries the family's direction-marker object style, so
    # its own component is directional and it would, left to itself, match
    # component.directional_pair (RTL_RESTRUCTURE, i.e. it moves). "art" is a
    # keep_upright-linked raster, which independently matches
    # graphic.translated_artwork (KEEP_POSITION) -- an earlier rule in the
    # table, so first_match would never even reach component.directional_pair
    # for it. Left unbound, one member of "g" moves and the other doesn't:
    # exactly the "arrow flips while the sentence stays put" failure this
    # design exists to prevent. Both must come out identically bound to the
    # component instead.
    items = f"""<Group Self="g" ItemTransform="1 0 0 1 0 0">
      <Rectangle Self="arrow" ItemTransform="1 0 0 1 0 0"
                 AppliedObjectStyle="ObjectStyle/long division arrow 1">
        <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
          <PathPointType Anchor="0 0"/><PathPointType Anchor="0 20"/>
          <PathPointType Anchor="20 20"/><PathPointType Anchor="20 0"/>
        </PathPointArray></GeometryPathType></PathGeometry></Properties>
      </Rectangle>
      <Rectangle Self="art" ItemTransform="1 0 0 1 0 0">
        <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
          <PathPointType Anchor="25 0"/><PathPointType Anchor="25 20"/>
          <PathPointType Anchor="100 20"/><PathPointType Anchor="100 0"/>
        </PathPointArray></GeometryPathType></PathGeometry></Properties>
        <Image Self="im"><Link LinkResourceURI="file:/out/links_ar/fig.ar.png"/></Image>
      </Rectangle>
    </Group>"""
    plan = rtl_plan.build_plan(_docs(items), document="d.idml", language="ar",
                               keep_upright=("file:/out/links_ar/fig.ar.png",))
    by = plan.by_object()
    assert by["arrow"].component == "g"
    assert by["art"].component == "g"
    assert by["arrow"].action == by["art"].action == rtl_plan.KEEP_POSITION
    assert by["arrow"].rule == by["art"].rule == "component.bound"
    assert not by["arrow"].moves and not by["art"].moves


def test_a_math_unit_moves_whole_and_its_inside_never_moves_on_its_own():
    items = (f"""<Group Self="g" ItemTransform="1 0 0 1 0 0"
                        AppliedObjectStyle="ObjectStyle/problem box">
                 {_rect('tick', 0, 0, 4, 20)}
                 </Group>""")
    plan = rtl_plan.build_plan(_docs(items), document="d.idml", language="ar")
    by = plan.by_object()
    assert by["g"].action == rtl_plan.RTL_REPOSITION
    assert by["g"].rigid
    assert not by["tick"].moves


def test_nothing_nested_below_a_moving_unit_moves_on_its_own_account():
    # "leaf" sits two levels below the group's member "mid" (mid -> inner ->
    # leaf). Its transform is written in inner's space, so any move of its own
    # would be a second move measured in the wrong space.
    items = f"""
    <Group Self="outer" ItemTransform="1 0 0 1 0 0"
           AppliedObjectStyle="ObjectStyle/problem box">
      <Rectangle Self="mid" ItemTransform="1 0 0 1 0 0">
        <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
          <PathPointType Anchor="0 0"/><PathPointType Anchor="0 20"/>
          <PathPointType Anchor="90 20"/><PathPointType Anchor="90 0"/>
        </PathPointArray></GeometryPathType></PathGeometry></Properties>
        <Rectangle Self="inner" ItemTransform="1 0 0 1 0 0">
          <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
            <PathPointType Anchor="0 0"/><PathPointType Anchor="0 10"/>
            <PathPointType Anchor="30 10"/><PathPointType Anchor="30 0"/>
          </PathPointArray></GeometryPathType></PathGeometry></Properties>
          {_rect('leaf', 0, 0, 10, 5)}
        </Rectangle>
      </Rectangle>
    </Group>"""
    plan = rtl_plan.build_plan(_docs(items), document="d.idml", language="ar")
    by = plan.by_object()
    assert by["outer"].moves
    assert [o for o in ("mid", "inner", "leaf") if by[o].moves] == []
    assert by["leaf"].rule == "nested.carried"


def test_keep_upright_links_are_never_flipped():
    items = _rect("photo", -6, -459, 618, -330, extra="") + """
      <Rectangle Self="art" ItemTransform="1 0 0 1 0 0">
        <Properties><PathGeometry><GeometryPathType><PathPointArray>
          <PathPointType Anchor="0 0"/><PathPointType Anchor="0 40"/>
          <PathPointType Anchor="100 40"/><PathPointType Anchor="100 0"/>
        </PathPointArray></GeometryPathType></PathGeometry></Properties>
        <Image Self="im"><Link LinkResourceURI="file:/out/links_ar/fig.ar.png"/></Image>
      </Rectangle>"""
    plan = rtl_plan.build_plan(_docs(items), document="d.idml", language="ar",
                               keep_upright=("file:/out/links_ar/fig.ar.png",))
    assert plan.by_object()["art"].new_orientation == rtl_plan.KEEP_ORIENTATION


def test_plan_records_the_family_it_used():
    plan = rtl_plan.build_plan(_docs(_rect("a", 0, 0, 10, 10)),
                               document="d.idml", language="ar")
    assert plan.rules_family == rtl_rules.DEFAULT_FAMILY


def test_an_unclassified_component_and_its_border_mirror_as_one_unit():
    """A content frame grouped with its border: the group mirrors and carries
    both; neither moves on its own account, or it would move twice."""
    items = f"""<Group Self="g" ItemTransform="1 0 0 1 0 0">
      {_rect('content', 20, 0, 100, 40)}
      {_rect('border', 15, -5, 105, 45)}
    </Group>"""
    plan = rtl_plan.build_plan(_docs(items), document="d.idml", language="ar")
    by = plan.by_object()

    assert by["g"].rule == "default.mirror"
    assert by["g"].action == rtl_plan.RTL_MIRROR
    assert by["content"].component == "g" and by["border"].component == "g"
    assert by["content"].rule == by["border"].rule == "component.bound"
    assert not by["content"].moves and not by["border"].moves


def test_a_math_unit_and_an_unrelated_sibling_both_cross_the_page():
    """The whole page mirrors: a rigid math unit and an ordinary sibling
    both move, the unit whole, the sibling on its own."""
    items = (f"""<Group Self="locked" ItemTransform="1 0 0 1 0 0"
                        AppliedObjectStyle="ObjectStyle/problem box">
                 {_rect('tick', 0, 0, 4, 20)}
                 </Group>"""
             + _rect("unrelated", 200, 0, 260, 20))
    plan = rtl_plan.build_plan(_docs(items), document="d.idml", language="ar")
    by = plan.by_object()

    assert by["locked"].action == rtl_plan.RTL_REPOSITION
    assert not by["tick"].moves
    assert by["unrelated"].rule == "default.mirror"
    assert by["unrelated"].moves


def test_classification_is_independent_per_spread_across_a_multi_spread_document():
    """No cross-spread leakage: an unclassified object on one spread and its
    twin (same shape, different spread) on another are each classified and
    mirrored against their own spread's page axis, not each other's."""
    # `Feature.spread` comes from the `<Spread Self=...>` attribute itself,
    # not the documents-dict key, so each spread needs its own distinct
    # `Self` -- reusing SINGLE's default "spr" for both would collapse the
    # two spreads' identities and make the very leakage this test checks for
    # unobservable.
    docs = {
        "Spreads/S1.xml": etree.fromstring(
            SINGLE.format(items=_rect("a", 10, 0, 60, 20))
            .replace('Self="spr"', 'Self="spr1"').encode()),
        "Spreads/S2.xml": etree.fromstring(
            SINGLE.format(items=_rect("b", 10, 0, 60, 20))
            .replace('Self="spr"', 'Self="spr2"').encode()),
    }
    plan = rtl_plan.build_plan(docs, document="d.idml", language="ar")
    by = plan.by_object()

    assert by["a"].spread != by["b"].spread
    assert by["a"].moves and by["b"].moves
    assert by["a"].new_bounds == by["b"].new_bounds  # identical shape, identical page width -> identical reflection


def test_page_furniture_never_joins_a_content_cluster():
    """A vertical title set right beside a math console is close enough to
    cluster with it; bound to the cluster it would be carried across the page
    with it. Furniture takes part in no composition."""
    title = f"""
    <TextFrame Self="title" ParentStory="st" ItemTransform="0 1 -1 0 588 -238">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="0 0"/><PathPointType Anchor="0 32"/>
        <PathPointType Anchor="500 32"/><PathPointType Anchor="500 0"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </TextFrame>"""
    console = _rect("console", 548, -238, 554, 0,
                    'AppliedObjectStyle="ObjectStyle/math console"')
    docs = _docs(title + console)
    docs["Stories/Story_st.xml"] = etree.fromstring(b"""
      <idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
        <Story Self="st">
          <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/_Family Letter%3aFL lesson title">
            <CharacterStyleRange><Content>Title</Content></CharacterStyleRange>
          </ParagraphStyleRange>
        </Story>
      </idPkg:Story>""")
    plan = rtl_plan.build_plan(docs, document="d.idml", language="ar")
    by = plan.by_object()
    assert by["title"].rule == "structure.vertical_title"
    assert by["title"].component is None
    assert not by["title"].moves
    assert by["console"].moves


def test_a_rigid_equation_does_not_freeze_the_cluster_it_anchors():
    """An equation's rigidity is about its own inside. A diagram that merely
    sits beside it mirrors piece by piece, so the cluster mirrors."""
    items = (_rect("eq", 400, 0, 460, 20,
                   'AppliedObjectStyle="ObjectStyle/math console"')
             + _rect("diagram", 465, 0, 560, 20))
    plan = rtl_plan.build_plan(_docs(items), document="d.idml", language="ar")
    by = plan.by_object()
    assert by["eq"].component is not None
    assert by["eq"].component == by["diagram"].component
    assert by["eq"].action == rtl_plan.RTL_MIRROR
    assert by["eq"].rigid


def test_a_form_field_first_in_document_order_does_not_freeze_its_cluster():
    """A cluster of an ordinary object and a form-field-styled object, with
    the form field first in document order, still mirrors: iteration order
    must not decide whether a composition moves."""
    items = (_rect('field', 0, 0, 50, 20,
                   extra='AppliedObjectStyle="ObjectStyle/Form Fields"')
            + _rect('content', 55, 0, 150, 20))
    plan = rtl_plan.build_plan(_docs(items), document="d.idml", language="ar")
    by = plan.by_object()
    assert by["content"].moves or by["field"].moves
