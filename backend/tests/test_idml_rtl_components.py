"""Grouping objects into the units a designer actually composed."""

from pagebirdy.idml import rtl_components
from pagebirdy.idml.rtl_features import ObjectFeature

MARKERS = rtl_components.DirectionMarkers(
    paragraph_styles=frozenset({"_Family Letter:FL caret"}),
    object_styles=frozenset({"long division arrow 1"}),
    component_ids=frozenset(),
)


def _feat(self_id, x0, x1, y0=0.0, y1=10.0, parent=None, pstyles=(),
          objstyle=None, kind="Rectangle", z=0, layer="ub7",
          content_kind="path", is_master_item=False):
    return ObjectFeature(
        self_id=self_id, kind=kind, spread="spr", document="Spreads/S.xml",
        bounds=(x0, y0, x1, y1), transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        rotated=False, sheared=False, page_index=0,
        x_band=(x0 / 612.0, x1 / 612.0), full_bleed=False, layer=layer,
        object_style=objstyle, paragraph_styles=frozenset(pstyles),
        content_kind=content_kind, is_master_item=is_master_item,
        applied_master=None, link_uris=frozenset(), script_mix="none",
        anchored=False, z_index=z, parent_id=parent,
    )


def test_explicit_group_becomes_one_component():
    feats = [_feat("g", 0, 100, kind="Group", z=0),
             _feat("a", 0, 40, parent="g", z=1),
             _feat("b", 60, 100, parent="g", z=2)]
    comps = rtl_components.detect(feats, MARKERS)
    (comp,) = [c for c in comps if c.kind == "group"]
    assert comp.component_id == "g"
    assert set(comp.member_ids) == {"a", "b"}


def test_adjacent_siblings_on_one_line_form_a_cluster():
    # An arrow and the sentence beside it, ungrouped in the source.
    feats = [_feat("arrow", 100, 112, pstyles=["_Family Letter:FL caret"], z=0),
             _feat("text", 120, 400, kind="TextFrame", z=1)]
    comps = rtl_components.detect(feats, MARKERS)
    (comp,) = comps
    assert comp.kind == "cluster"
    assert set(comp.member_ids) == {"arrow", "text"}


def test_a_cluster_holding_a_direction_marker_is_directional():
    feats = [_feat("arrow", 100, 112, pstyles=["_Family Letter:FL caret"], z=0),
             _feat("text", 120, 400, kind="TextFrame", z=1)]
    (comp,) = rtl_components.detect(feats, MARKERS)
    assert comp.directional is True
    assert "FL caret" in comp.evidence


def test_an_image_beside_a_caption_is_not_directional_on_shape_alone():
    # The spec is explicit: adjacency is not evidence. Without a marker the
    # component is preserved, not recomposed.
    feats = [_feat("img", 100, 300, z=0), _feat("cap", 310, 500,
                                                kind="TextFrame", z=1)]
    (comp,) = rtl_components.detect(feats, MARKERS)
    assert comp.directional is False


def test_distant_siblings_do_not_cluster():
    feats = [_feat("a", 0, 40, z=0), _feat("b", 400, 500, z=1)]
    assert rtl_components.detect(feats, MARKERS) == []


def test_an_object_belongs_to_at_most_one_component():
    feats = [_feat("g", 0, 100, kind="Group", z=0),
             _feat("a", 0, 40, parent="g", z=1),
             _feat("b", 45, 100, parent="g", z=2),
             _feat("outside", 105, 200, z=3)]
    comps = rtl_components.detect(feats, MARKERS)
    owned = [m for c in comps for m in c.member_ids]
    assert len(owned) == len(set(owned))


# --- Regressions found only by running detect() over real books --------
#
# `cluster:u888` in RCM08_NA_SW_U01_L01-09be3245.idml single-linked a
# family-letter body column, a Math Tools sidebar and a vertical lesson
# title into one 16-member, 87%-of-page-width component, each link
# individually well within the old, unmeasured _CLUSTER_GAP=24. And the
# anchored-join / nested-group steps carried a component's *original*
# directional/evidence forward unchanged instead of recomputing it, so a
# marker that only arrived once membership was final was silently dropped.
# The fixtures below reproduce both defects at unit-test scale.

def _anchored(self_id, parent, objstyle=None, pstyles=(), z=0):
    """An anchored object: positioned by text flow, so it carries no
    geometry of its own (see rtl_features.py) -- `bounds`, `page_index` and
    `x_band` are honestly None, exactly as `rtl_features.collect` would
    produce for a real one."""
    return ObjectFeature(
        self_id=self_id, kind="Rectangle", spread="spr",
        document="Stories/S.xml", bounds=None,
        transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        rotated=False, sheared=False, page_index=None,
        x_band=None, full_bleed=False, layer=None,
        object_style=objstyle, paragraph_styles=frozenset(pstyles),
        content_kind="path", is_master_item=False, applied_master=None,
        link_uris=frozenset(), script_mix="none", anchored=True,
        z_index=z, parent_id=parent,
    )


def test_a_chain_that_blows_the_span_cap_dissolves_entirely():
    # a-b and b-c are each within _CLUSTER_GAP (b is simply wide), but a-c
    # are nowhere near each other and the whole chain would cover most of
    # the page -- exactly the shape of the real family-letter/sidebar/title
    # chain. Single-linkage has no sense of when to stop on its own; the
    # span cap is what refuses to let this become one component. Nothing
    # here is claimed: every member is left to be classified individually,
    # the safe default.
    feats = [_feat("a", 0, 50, z=0),
             _feat("b", 55, 450, z=1),
             _feat("c", 460, 500, z=2)]
    assert rtl_components.detect(feats, MARKERS) == []


def test_an_anchored_marker_makes_its_already_built_host_directional():
    # "img" + "cap" is the exact non-directional cluster from
    # test_an_image_beside_a_caption_is_not_directional_on_shape_alone.
    # An anchored decoration then arrives inside "cap" carrying the
    # family's directional object style -- the host's directionality must
    # be recomputed with it in the picture, not carried forward from before
    # the join.
    feats = [_feat("img", 100, 300, z=0),
             _feat("cap", 310, 500, kind="TextFrame", z=1),
             _anchored("deco", parent="cap",
                       objstyle="long division arrow 1", z=2)]
    (comp,) = rtl_components.detect(feats, MARKERS)
    assert "deco" in comp.member_ids
    assert comp.directional is True
    assert "long division arrow 1" in comp.evidence


def test_a_marker_on_a_nested_groups_descendant_makes_the_outer_group_directional():
    # "inner" is itself a <Group> nested inside "outer": step 1 gives it its
    # own separate component ("marked" is inner's member, not outer's), so
    # outer's own member_ids never mention "marked" directly. But visually
    # "marked" moves with "outer" too, so its marker must still count as
    # evidence for outer.
    feats = [
        _feat("outer", 0, 200, kind="Group", z=0),
        _feat("plain", 0, 40, parent="outer", z=1),
        _feat("inner", 50, 200, kind="Group", parent="outer", z=2),
        _feat("marked", 60, 90, parent="inner",
              pstyles=["_Family Letter:FL caret"], z=3),
    ]
    comps = rtl_components.detect(feats, MARKERS)
    outer = next(c for c in comps if c.component_id == "outer")
    inner = next(c for c in comps if c.component_id == "inner")
    assert set(outer.member_ids) == {"plain", "inner"}
    assert set(inner.member_ids) == {"marked"}
    assert outer.directional is True
    assert "FL caret" in outer.evidence


def test_an_overlapping_background_does_not_bridge_unrelated_frames():
    # "bg" overlaps both "left" and "right" in x (it's a full-bleed
    # background rectangle behind a whole line of foreground frames, the
    # shape that produced 97-102%-of-page-width "clusters" in every one of
    # four real books before this was fixed). Overlap is not "beside",
    # regardless of how small the naive gap formula would have measured it
    # as, so it must never bridge two otherwise-unrelated frames together.
    feats = [_feat("bg", 0, 600, kind="Rectangle", z=0),
             _feat("left", 10, 50, kind="TextFrame", z=1),
             _feat("right", 560, 590, kind="TextFrame", z=2)]
    assert rtl_components.detect(feats, MARKERS) == []


def test_is_form_field_matches_the_interactive_kinds():
    for kind in ("TextBox", "CheckBox", "RadioButton"):
        f = _feat("f", 0, 50, kind=kind)
        assert rtl_components.is_form_field(f)


def test_is_form_field_matches_the_style_name():
    f = _feat("f", 0, 50, kind="Rectangle", objstyle="Form Fields")
    assert rtl_components.is_form_field(f)


def test_is_form_field_false_for_ordinary_content():
    f = _feat("f", 0, 50, kind="Rectangle")
    assert not rtl_components.is_form_field(f)


def test_a_backdrop_fully_containing_a_form_field_clusters_with_it():
    backdrop = _feat("bg", -531.5, -80.5, y0=-102.6, y1=287.4, content_kind="vector")
    field = _feat("field", -522.0, -90.0, y0=-77.7, y1=278.5,
                  kind="TextBox", content_kind="empty", objstyle="Form Fields")
    components = rtl_components.detect([backdrop, field], MARKERS)
    (comp,) = [c for c in components if "bg" in c.member_ids]
    assert comp.kind == "containment"
    assert set(comp.member_ids) == {"bg", "field"}
    # anchored on the form field, not the backdrop
    assert comp.component_id == "field"


def test_a_loosely_overlapping_backdrop_does_not_cluster():
    # Overlaps the field by roughly half its own area -- well under the 90%
    # containment threshold. Must not cluster.
    backdrop = _feat("bg", -600.0, -500.0, y0=-150.0, y1=250.0, content_kind="vector")
    field = _feat("field", -522.0, -90.0, y0=-77.7, y1=278.5,
                  kind="TextBox", content_kind="empty", objstyle="Form Fields")
    components = rtl_components.detect([backdrop, field], MARKERS)
    assert not any("bg" in c.member_ids and c.kind == "containment" for c in components)


def test_containment_only_considers_form_fields_not_arbitrary_pairs():
    # Two ordinary rectangles, one fully inside the other -- neither is a
    # form field, so no containment component should form (this is not a
    # generic "nested boxes cluster" rule).
    outer = _feat("outer", 0, 200, y0=0, y1=200, content_kind="vector")
    inner = _feat("inner", 50, 150, y0=50, y1=150, content_kind="vector")
    components = rtl_components.detect([outer, inner], MARKERS)
    assert not any(c.kind == "containment" for c in components)


def test_two_stacked_graphics_within_gap_cluster_together():
    icon = _feat("icon", -228.81, -78.66, y0=-322.14, y1=-220.86,
                content_kind="raster")
    diagram = _feat("diagram", -237.0, -70.76, y0=-220.90, y1=-123.30,
                    content_kind="vector")
    components = rtl_components.detect([icon, diagram], MARKERS)
    (comp,) = [c for c in components if "icon" in c.member_ids]
    assert set(comp.member_ids) == {"icon", "diagram"}
    assert comp.kind == "cluster"


def test_two_stacked_graphics_beyond_gap_do_not_cluster():
    icon = _feat("icon", -228.81, -78.66, y0=-322.14, y1=-220.86,
                content_kind="raster")
    far = _feat("far", -237.0, -70.76, y0=-180.0, y1=-82.4,  # 40pt below icon's bottom
               content_kind="vector")
    components = rtl_components.detect([icon, far], MARKERS)
    assert not any("icon" in c.member_ids and "far" in c.member_ids
                  for c in components)


def test_a_header_above_a_paragraph_never_clusters_regardless_of_spacing():
    # Both text_kind -- vertical clustering only ever considers raster/vector
    # content, so a text-over-text pair (or text-over-graphic) must never
    # merge no matter how close together they sit.
    header = _feat("header", -228.81, -78.66, y0=-322.14, y1=-320.86,
                   kind="TextFrame", content_kind="text")
    paragraph = _feat("para", -237.0, -70.76, y0=-320.80, y1=-220.0,
                      kind="TextFrame", content_kind="text")
    components = rtl_components.detect([header, paragraph], MARKERS)
    assert not any("header" in c.member_ids and "para" in c.member_ids
                  for c in components)


def test_vertical_clustering_skips_objects_already_matching_a_named_rule():
    # is_master_item=True stands in here for "a named rule ahead of the
    # catch-all already governs this" -- must not be pulled into a generic
    # vertical cluster even if the shape would otherwise qualify.
    icon = _feat("icon", -228.81, -78.66, y0=-322.14, y1=-220.86,
                content_kind="raster")
    furniture = _feat("furniture", -237.0, -70.76, y0=-220.90, y1=-123.30,
                      content_kind="vector", is_master_item=True)
    components = rtl_components.detect([icon, furniture], MARKERS)
    assert not any("icon" in c.member_ids and "furniture" in c.member_ids
                  for c in components)



