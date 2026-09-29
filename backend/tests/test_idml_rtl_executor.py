"""The executor does exactly what the plan says, and nothing else."""

from lxml import etree

from pagebirdy.idml import rtl, rtl_plan

SINGLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"/>
    {items}
  </Spread>
</idPkg:Spread>
"""


def _rect(self_id, x0, y0, x1, y1):
    return f"""
    <Rectangle Self="{self_id}" ItemTransform="1 0 0 1 0 0">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="{x0} {y0}"/><PathPointType Anchor="{x0} {y1}"/>
        <PathPointType Anchor="{x1} {y1}"/><PathPointType Anchor="{x1} {y0}"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </Rectangle>"""


def _arrow(self_id, base_x, tip_x, y0=0, y1=20):
    """An asymmetric right-pointing arrowhead: two points on the base edge,
    one tip point on the opposite side.

    A rectangle reflects into an identical rectangle -- `item_bounds` and
    `tx` cannot tell the difference between a rectangle whose path was
    reflected and one whose path was left untouched, so no `_rect` fixture
    can ever catch a missing `reflect_path` call. This shape can: the tip's
    own local x-coordinate visibly swaps sides.
    """
    mid_y = (y0 + y1) / 2.0
    return f"""
    <Polygon Self="{self_id}" ItemTransform="1 0 0 1 0 0">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="{base_x} {y0}"/><PathPointType Anchor="{base_x} {y1}"/>
        <PathPointType Anchor="{tip_x} {mid_y}"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </Polygon>"""


def _path_xs(docs, self_id):
    """The x-coordinate of every anchor of `self_id`'s own path, in document
    order -- so index [2] is always `_arrow`'s tip, whichever way it points.
    """
    el = docs["Spreads/S.xml"].find(f".//*[@Self='{self_id}']")
    return [float(p.get("Anchor").split()[0])
            for p in el.find("./Properties/PathGeometry").iter("PathPointType")]


def _docs(items):
    return {"Spreads/S.xml": etree.fromstring(SINGLE.format(items=items).encode())}


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


def _tx(docs, self_id):
    el = docs["Spreads/S.xml"].find(f".//*[@Self='{self_id}']")
    return rtl.parse_transform(el.get("ItemTransform"))


def test_keep_position_moves_nothing():
    docs = _docs(_rect("a", 50, 0, 150, 40))
    before = _tx(docs, "a")
    rtl.apply_plan(docs, _plan(_d("a", rtl_plan.KEEP_POSITION)))
    assert _tx(docs, "a") == before


def test_rtl_reposition_reflects_tx_and_leaves_abcd_alone():
    docs = _docs(_rect("a", 50, 0, 150, 40))
    rtl.apply_plan(docs, _plan(_d("a", rtl_plan.RTL_REPOSITION)))
    a, b, c, d, tx, ty = _tx(docs, "a")
    assert (a, b, c, d) == (1.0, 0.0, 0.0, 1.0)
    # 50..150 on a 612pt page reflects to 462..562: tx moves by +412.
    assert tx == 412.0
    assert ty == 0.0


def test_rtl_reposition_reflects_an_asymmetric_paths_own_outline():
    """A rectangle can never show this: `tx` and `item_bounds` are identical
    whether or not `reflect_path` ran on a symmetric shape. An arrowhead's
    tip visibly swaps sides, which is exactly what a decorative outline's own
    handedness has to do when the item it belongs to changes which part of
    the page it faces."""
    docs = _docs(_arrow("a", base_x=50, tip_x=90))
    before = _path_xs(docs, "a")
    rtl.apply_plan(docs, _plan(_d("a", rtl_plan.RTL_REPOSITION)))
    after = _path_xs(docs, "a")
    # Local path axis is (50+90)/2 = 70; every anchor's x reflects about it.
    assert after == [2 * 70 - x for x in before]
    assert after != before


def test_mirror_graphic_flips_content_without_moving_the_frame():
    docs = _docs("""
      <Rectangle Self="ph" ItemTransform="1 0 0 1 0 0">
        <Properties><PathGeometry><GeometryPathType><PathPointArray>
          <PathPointType Anchor="0 0"/><PathPointType Anchor="0 40"/>
          <PathPointType Anchor="100 40"/><PathPointType Anchor="100 0"/>
        </PathPointArray></GeometryPathType></PathGeometry></Properties>
        <Image Self="im" ItemTransform="1 0 0 1 0 0"><Link LinkResourceURI="file:/p.png"/></Image>
      </Rectangle>""")
    before = _tx(docs, "ph")
    rtl.apply_plan(docs, _plan(
        _d("ph", rtl_plan.MIRROR_GRAPHIC,
           new_orientation=rtl_plan.MIRROR_GRAPHIC)))
    assert _tx(docs, "ph") == before          # frame did not move
    assert _tx(docs, "im")[0] == -1.0          # picture turned round


def test_keep_geometry_moves_neither_the_object_nor_its_children():
    docs = _docs(f"""<Group Self="g" ItemTransform="1 0 0 1 0 0">
                     {_rect('tick', 0, 0, 4, 20)}</Group>""")
    before = _tx(docs, "tick")
    rtl.apply_plan(docs, _plan(_d("g", rtl_plan.KEEP_GEOMETRY),
                               _d("tick", rtl_plan.KEEP_GEOMETRY)))
    assert _tx(docs, "tick") == before


def test_executor_preserves_identity_and_stacking_order():
    docs = _docs(_rect("a", 0, 0, 40, 20) + _rect("b", 60, 0, 100, 20)
                 + _rect("c", 200, 0, 260, 20))
    rtl.apply_plan(docs, _plan(_d("a", rtl_plan.RTL_REPOSITION),
                               _d("b", rtl_plan.KEEP_POSITION),
                               _d("c", rtl_plan.MIRROR_GRAPHIC)))
    spread = docs["Spreads/S.xml"].find(".//Spread")
    ids = [el.get("Self") for el in spread if rtl._is_page_item(el)]
    assert ids == ["a", "b", "c"]


def test_an_object_with_no_decision_is_left_alone():
    docs = _docs(_rect("a", 50, 0, 150, 40))
    before = _tx(docs, "a")
    rtl.apply_plan(docs, _plan())
    assert _tx(docs, "a") == before


def test_a_nested_item_with_no_decision_is_untouched_even_as_its_parent_moves(caplog):
    """The collector prunes at a non-page-item wrapper; the executor's own
    walk is flat (`spread.iter()`), so a nested page item the plan never saw
    -- a form control's own `<State>` children in the one real book checked
    -- is still visited here. It is correctly left alone: its `ItemTransform`
    is relative to its parent, so it moves with the parent's matrix without
    needing a decision of its own. This pins that as a checked invariant
    rather than an accident of traversal, and pins the debug-log count."""
    import logging

    parent = (
        '<Rectangle Self="parent" ItemTransform="1 0 0 1 0 0">'
        '<Properties><PathGeometry><GeometryPathType PathOpen="false">'
        '<PathPointArray>'
        '<PathPointType Anchor="50 0"/><PathPointType Anchor="50 40"/>'
        '<PathPointType Anchor="150 40"/><PathPointType Anchor="150 0"/>'
        '</PathPointArray></GeometryPathType></PathGeometry></Properties>'
        '<Rectangle Self="state" ItemTransform="1 0 0 1 5 5">'
        '<Properties><PathGeometry><GeometryPathType PathOpen="false">'
        '<PathPointArray>'
        '<PathPointType Anchor="0 0"/><PathPointType Anchor="0 10"/>'
        '<PathPointType Anchor="10 10"/><PathPointType Anchor="10 0"/>'
        '</PathPointArray></GeometryPathType></PathGeometry></Properties>'
        '</Rectangle>'
        '</Rectangle>'
    )
    docs = _docs(parent)
    before_state = _tx(docs, "state")

    with caplog.at_level(logging.DEBUG, logger="pagebirdy.idml.rtl"):
        report = rtl.apply_plan(docs, _plan(_d("parent", rtl_plan.RTL_REPOSITION)))

    # The parent moved (50..150 on a 612pt page: dx = 2*306 - 200 = 412)...
    assert _tx(docs, "parent")[4] == 412.0
    # ...but the nested, undecided child's own attribute is untouched -- it
    # travels with the parent's matrix, not by being edited itself.
    assert _tx(docs, "state") == before_state
    assert report["rtl_items_repositioned"] == 1
    # 2, not 1: `<Spread>` itself carries an `ItemTransform` (identity, in
    # every fixture here) and so matches `_is_page_item` too -- it is never
    # given a decision either, and was always silently skipped before this
    # counter existed. Both are safe for the same reason: neither is ever
    # moved on its own account, only ever carried by a page item that is.
    assert any("2 page item(s) visited with no plan decision" in r.message
              for r in caplog.records)


def test_counters_report_what_happened():
    docs = _docs(_rect("a", 0, 0, 40, 20) + _rect("b", 60, 0, 100, 20))
    report = rtl.apply_plan(docs, _plan(_d("a", rtl_plan.RTL_REPOSITION),
                                        _d("b", rtl_plan.KEEP_POSITION)))
    assert report["rtl_items_repositioned"] == 1
    assert report["rtl_items_kept"] == 1


def test_a_legacy_language_still_gets_the_whole_page_mirror(tmp_path):
    """he/fa/ur must be byte-identical to the old behaviour."""
    from pagebirdy.idml import rtl_legacy
    docs_new = _docs(_rect("a", 50, 0, 150, 40))
    docs_old = _docs(_rect("a", 50, 0, 150, 40))
    rtl_legacy.mirror_geometry(docs_old)
    # The semantic engine leaves it; the legacy engine moves it.
    rtl.apply_plan(docs_new, _plan(_d("a", rtl_plan.KEEP_POSITION)))
    assert _tx(docs_old, "a")[4] == 412.0
    assert _tx(docs_new, "a")[4] == 0.0


# ---- RTL_RESTRUCTURE vs RTL_REPOSITION, group and cluster ------------------
#
# A component's members carry KEEP_POSITION/"component.bound" (Task 5); only
# the anchor carries the real action, and `_move_component` carries it out
# for every member at once. A *group* anchor is the `<Group>` element itself,
# whose children's `tx` is written in the group's own coordinate space, so
# moving the anchor already carries them -- RTL_REPOSITION touches only the
# anchor, and RTL_RESTRUCTURE leaves the anchor's own outline untouched and
# rearranges only the children, about their own union centre. A *cluster*
# anchor is one sibling among several independent spread children with
# nothing to piggyback on -- RTL_REPOSITION must move every member by one
# shared delta so their arrangement survives, and RTL_RESTRUCTURE must move
# every member (the anchor included) about the *members'* own union centre,
# never the page axis: the component rearranges internally and does not, as
# a whole, change which side of the page it is on.


def _badge_and_label():
    # badge: an asymmetric arrowhead, x 0..10, so a missing `reflect_path`
    # call on a rearranged child is visible; label: x 20..100 (a plain rect
    # is fine here -- only one asymmetric shape is needed to catch the bug).
    # Union centre of the two is 50.
    return _arrow("badge", base_x=0, tip_x=10, y0=0, y1=10) + \
        _rect("label", 20, 0, 100, 10)


def _group_component(action, rule="component.direction_line"):
    docs = _docs(f'<Group Self="g" ItemTransform="1 0 0 1 0 0">'
                f'{_badge_and_label()}</Group>')
    plan = _plan(
        _d("g", action, component="g", component_kind="group", rule=rule),
        _d("badge", rtl_plan.KEEP_POSITION, component="g",
           component_kind="group", rule="component.bound"),
        _d("label", rtl_plan.KEEP_POSITION, component="g",
           component_kind="group", rule="component.bound"),
    )
    return docs, plan


def test_rtl_restructure_rearranges_a_groups_children_without_moving_the_group():
    """The group's own outline -- what the page mirror computed for it -- must
    stay exactly where it is; only what is inside rearranges. And the badge's
    own outline has to turn round as well as move, or it ends up on the other
    side of the label still pointing the way it pointed in English."""
    docs, plan = _group_component(rtl_plan.RTL_RESTRUCTURE)
    before_g = _tx(docs, "g")
    before_badge, before_label = _tx(docs, "badge"), _tx(docs, "label")
    before_badge_path = _path_xs(docs, "badge")

    rtl.apply_plan(docs, plan)

    assert _tx(docs, "g") == before_g          # the anchor did not move
    after_badge, after_label = _tx(docs, "badge"), _tx(docs, "label")
    # Union centre of [0,10] and [20,100] is 50.
    assert after_badge[4] == before_badge[4] + 90.0   # 0..10 -> 90..100
    assert after_label[4] == before_label[4] - 20.0   # 20..100 -> 0..80
    # `a b c d` are never touched on either child.
    assert after_badge[:4] == before_badge[:4] == (1.0, 0.0, 0.0, 1.0)
    assert after_label[:4] == before_label[:4] == (1.0, 0.0, 0.0, 1.0)
    # The badge's own outline reflected about its own local axis (0+10)/2=5
    # -- a rectangle (label) cannot show this, only the asymmetric badge can.
    after_badge_path = _path_xs(docs, "badge")
    assert after_badge_path == [2 * 5 - x for x in before_badge_path]
    assert after_badge_path != before_badge_path


def test_rtl_reposition_moves_a_group_exactly_once_children_not_double_moved():
    """The composition travels intact: the anchor moves once, and its
    children -- whose `tx` is already relative to it -- are not moved again."""
    docs, plan = _group_component(rtl_plan.RTL_REPOSITION, rule="nav.control")
    before_badge, before_label = _tx(docs, "badge"), _tx(docs, "label")

    rtl.apply_plan(docs, plan)

    # The group spans 0..100 (badge 0..10, label 20..100) on a 612pt page:
    # axis 306, dx = 2*306 - 100 = 512.
    assert _tx(docs, "g")[4] == 512.0
    # Children's own (group-relative) transforms are untouched -- they travel
    # with the group's matrix, not by having their own `tx` edited too.
    assert _tx(docs, "badge") == before_badge
    assert _tx(docs, "label") == before_label


def _arrow_and_sentence():
    # arrow: an asymmetric arrowhead, x 0..40, base at 0, tip at 40 -- pointing
    # right, into the sentence beside it; sentence: x 60..300 (a plain rect is
    # fine here, only the arrow's own direction is in question). Both
    # top-level spread siblings -- no XML nesting -- as `rtl_components.detect`
    # builds a cluster.
    return _arrow("arrow", base_x=0, tip_x=40, y0=0, y1=20) + \
        _rect("sentence", 60, 0, 300, 20)


def _cluster_component(action, rule="component.direction_line"):
    docs = _docs(_arrow_and_sentence())
    plan = _plan(
        _d("arrow", action, component="cluster:arrow",
           component_kind="cluster", rule=rule),
        _d("sentence", rtl_plan.KEEP_POSITION, component="cluster:arrow",
           component_kind="cluster", rule="component.bound"),
    )
    return docs, plan


def test_rtl_restructure_swaps_a_clusters_members_without_moving_its_union_box():
    """The flagship failure this action exists to prevent: an arrow beside a
    sentence must swap sides as one recomposed unit, not fly across the page
    on its own while the sentence it introduces stays put -- and it has to
    turn round as well as move, or it crosses to the sentence's other side
    still pointing away from it, which is worse than not moving at all."""
    docs, plan = _cluster_component(rtl_plan.RTL_RESTRUCTURE)
    before_arrow, before_sentence = _tx(docs, "arrow"), _tx(docs, "sentence")
    union_before = (min(before_arrow[4] + 0, before_sentence[4] + 60),
                    max(before_arrow[4] + 40, before_sentence[4] + 300))

    rtl.apply_plan(docs, plan)

    after_arrow, after_sentence = _tx(docs, "arrow"), _tx(docs, "sentence")
    # Union of [0,40] and [60,300] is [0,300], centre 150.
    assert after_arrow[4] == before_arrow[4] + 260.0      # 0..40 -> 260..300
    assert after_sentence[4] == before_sentence[4] - 60.0  # 60..300 -> 0..240
    # The arrow crossed to the other side of the sentence...
    assert after_arrow[4] + 0 > after_sentence[4] + 300     # arrow now right of it
    # ...and the component's own union box is exactly where it was: this
    # rearranges internally and does not, as a whole, change page side.
    union_after = (min(after_arrow[4] + 0, after_sentence[4] + 60),
                   max(after_arrow[4] + 40, after_sentence[4] + 300))
    assert union_after == union_before
    # `a b c d` are never touched.
    assert after_arrow[:4] == before_arrow[:4] == (1.0, 0.0, 0.0, 1.0)
    assert after_sentence[:4] == before_sentence[:4] == (1.0, 0.0, 0.0, 1.0)

    # The arrow's own outline reflected too (local axis (0+40)/2 = 20), and
    # the reflection composed with the tx move leaves the tip pointing at the
    # sentence, not away from it. A rectangle sentence cannot show this --
    # only the asymmetric arrow can.
    tip_x, base_x = _path_xs(docs, "arrow")[2], _path_xs(docs, "arrow")[0]
    tip_world, base_world = after_arrow[4] + tip_x, after_arrow[4] + base_x
    assert tip_world == 260.0 and base_world == 300.0
    # The tip sits on the near edge, closest to the sentence at [0,240] --
    # pointing into it, exactly as it did in English before either moved.
    assert tip_world < base_world


def test_rtl_reposition_moves_every_cluster_member_by_the_same_delta():
    """Nothing else will move a cluster's other members, so RTL_REPOSITION has
    to move every one of them -- by one shared delta, so the arrow stays the
    same distance from the sentence it introduces."""
    docs, plan = _cluster_component(rtl_plan.RTL_REPOSITION, rule="nav.control")
    before_arrow, before_sentence = _tx(docs, "arrow"), _tx(docs, "sentence")
    before_arrow_path = _path_xs(docs, "arrow")
    gap_before = (before_sentence[4] + 60) - (before_arrow[4] + 40)

    rtl.apply_plan(docs, plan)

    after_arrow, after_sentence = _tx(docs, "arrow"), _tx(docs, "sentence")
    # Union of [0,40] and [60,300] is [0,300] on a 612pt page: axis 306,
    # dx = 2*306 - 300 = 312, shared by every member.
    assert after_arrow[4] == before_arrow[4] + 312.0
    assert after_sentence[4] == before_sentence[4] + 312.0
    gap_after = (after_sentence[4] + 60) - (after_arrow[4] + 40)
    assert gap_after == gap_before

    # This cluster path already called `reflect_path` before this review
    # round (only the RTL_RESTRUCTURE branches were missing it) -- the
    # arrow's own asymmetric outline proves it actually fires here too,
    # which no `_rect` fixture in this file ever could.
    after_arrow_path = _path_xs(docs, "arrow")
    assert after_arrow_path == [2 * 20 - x for x in before_arrow_path]
    assert after_arrow_path != before_arrow_path


def test_a_component_decision_missing_component_kind_is_left_alone_and_logged(caplog):
    """`build_plan` always sets `component_kind` alongside `component` -- the
    same `component_context` supplies both -- so a decision that has one
    without the other did not come from the real classifier. Guessing which
    arithmetic to use (group's, or cluster's) would be a wrong move dressed
    up as a normal one; every member is left untouched instead, loudly."""
    import logging

    docs = _docs(_rect("a", 50, 0, 150, 40))
    before = _tx(docs, "a")

    with caplog.at_level(logging.ERROR, logger="pagebirdy.idml.rtl"):
        rtl.apply_plan(docs, _plan(_d(
            "a", rtl_plan.RTL_REPOSITION, component="mystery",
            component_kind=None)))

    assert _tx(docs, "a") == before
    assert any("component_kind" in r.message for r in caplog.records)
