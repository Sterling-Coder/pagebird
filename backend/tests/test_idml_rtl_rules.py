"""Each rule earns its own test, named by rule id."""

from pagebirdy.idml import rtl_plan, rtl_rules
from pagebirdy.idml.rtl_features import ObjectFeature

TABLE = rtl_rules.get_rules(rtl_rules.DEFAULT_FAMILY)
CTX = rtl_rules.PageContext(page_index=0, page_width=612.0, is_master=False)


def _feat(**over):
    base = dict(
        self_id="x", kind="Rectangle", spread="spr", document="Spreads/S.xml",
        bounds=(0.0, 0.0, 100.0, 50.0), transform=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
        rotated=False, sheared=False, page_index=0, x_band=(0.0, 0.163),
        full_bleed=False, layer="ub7", object_style=None,
        paragraph_styles=frozenset(), content_kind="path",
        is_master_item=False, applied_master=None, link_uris=frozenset(),
        script_mix="none", anchored=False, z_index=0, parent_id=None)
    base.update(over)
    return ObjectFeature(**base)


def _decide(feature, component=None, ctx=CTX):
    return rtl_rules.first_match(TABLE, feature, ctx, component)


def test_unrecognised_content_mirrors():
    rule = _decide(_feat())
    assert rule.rule_id == "default.mirror"
    assert rule.action == rtl_plan.RTL_MIRROR


def test_the_table_ends_in_the_mirroring_catch_all_and_nothing_else_is_unconditional():
    assert TABLE.rules[-1].rule_id == "default.mirror"
    assert [r.rule_id for r in TABLE.rules if r.predicate is rtl_rules.p_always] \
        == ["default.mirror"]


def test_master_item_keeps_position():
    assert _decide(_feat(is_master_item=True)).rule_id == "master.item"


def test_master_lesson_badge_keeps_position():
    f = _feat(paragraph_styles=frozenset({"_Family Letter:FL Lesson #"}),
              content_kind="text", x_band=(0.806, 0.929))
    assert _decide(f).rule_id == "master.lesson_badge"
    assert _decide(f).action == rtl_plan.KEEP_POSITION


def test_vertical_lesson_title_keeps_position():
    f = _feat(paragraph_styles=frozenset({"_Family Letter:FL lesson title"}),
              content_kind="text", rotated=True, x_band=(0.908, 0.961))
    assert _decide(f).rule_id == "structure.vertical_title"


def test_styled_math_crosses_the_page_as_one_rigid_unit():
    f = _feat(paragraph_styles=frozenset({"vertical equation"}),
              content_kind="text")
    rule = _decide(f)
    assert rule.rule_id == "math.styled"
    assert rule.action == rtl_plan.RTL_REPOSITION
    assert rule.orientation == rtl_plan.KEEP_ORIENTATION


def test_placed_vector_art_mirrors_its_place_but_never_its_picture():
    rule = _decide(_feat(content_kind="vector"))
    assert rule.rule_id == "math.vector_art"
    assert rule.action == rtl_plan.RTL_MIRROR
    assert rule.orientation == rtl_plan.KEEP_ORIENTATION


def test_vector_art_inside_a_directional_component_defers_to_the_component():
    from pagebirdy.idml.rtl_components import Component
    comp = Component(component_id="c", kind="cluster", member_ids=("x",),
                     bounds=(0, 0, 100, 50), page_index=0, spread="spr",
                     directional=True, evidence="marker")
    assert _decide(_feat(content_kind="vector"), comp).rule_id != "math.vector_art"


def test_a_bleeding_photograph_on_the_page_mirrors_its_place_and_its_picture():
    f = _feat(content_kind="raster", full_bleed=True,
              bounds=(355.0, -405.0, 617.0, -216.0), x_band=(0.58, 1.01))
    rule = _decide(f)
    assert rule.rule_id == "graphic.content_bleed"
    assert rule.action == rtl_plan.RTL_MIRROR
    assert rule.orientation == rtl_plan.MIRROR_GRAPHIC


def test_full_bleed_decorative_raster_on_a_master_still_mirrors():
    # The one interaction that actually matters on the real book: u355, the
    # honeycomb header banner, sits on a master spread AND is a full-bleed
    # raster. The human Arabic reference flips it, not moves it -- so
    # is_master_item must not shadow graphic.decorative_bleed the way
    # master.item's KEEP_ORIENTATION would if it matched first.
    f = _feat(content_kind="raster", full_bleed=True, is_master_item=True,
              bounds=(-6.0, -459.0, 618.0, -330.0), x_band=(-0.01, 1.01))
    rule = _decide(f)
    assert rule.rule_id == "graphic.decorative_bleed"
    assert rule.orientation == rtl_plan.MIRROR_GRAPHIC


def test_a_family_that_opts_out_does_not_turn_its_bleed_round():
    table = rtl_rules.RuleTable(
        family="plain", rules=TABLE.rules, markers=TABLE.markers,
        mirror_decorative_bleed=False, never_flip_links=frozenset())
    f = _feat(content_kind="raster", full_bleed=True)
    rule = rtl_rules.first_match(table, f, CTX, None)
    assert rule.orientation == rtl_plan.KEEP_ORIENTATION


def test_a_listed_bleed_exception_is_not_turned_round():
    table = rtl_rules.RuleTable(
        family="x", rules=TABLE.rules, markers=TABLE.markers,
        mirror_decorative_bleed=True,
        never_flip_links=frozenset({"file:/links/map.png"}))
    f = _feat(content_kind="raster", full_bleed=True,
              link_uris=frozenset({"file:/links/map.png"}))
    rule = rtl_rules.first_match(table, f, CTX, None)
    assert rule.orientation == rtl_plan.KEEP_ORIENTATION


def test_a_prose_text_frame_mirrors_with_the_page_and_reads_right_to_left():
    f = _feat(kind="TextFrame", content_kind="text", script_mix="arabic")
    rule = _decide(f)
    assert rule.action == rtl_plan.RTL_MIRROR
    assert rule.text == rtl_plan.TEXT_RTL


def test_ltr_only_text_frame_is_pinned():
    f = _feat(kind="TextFrame", content_kind="text", script_mix="latin")
    assert _decide(f).text == rtl_plan.TEXT_RTL_LTR_PINNED


def test_a_table_frame_mirrors_with_the_page():
    f = _feat(kind="Table", content_kind="table")
    rule = _decide(f)
    assert rule.rule_id == "table.default"
    assert rule.action == rtl_plan.RTL_MIRROR


def test_unknown_family_falls_back_to_the_default_table():
    assert rtl_rules.get_rules("no-such-family").family == rtl_rules.DEFAULT_FAMILY


import pytest


def test_an_answer_field_mirrors_with_the_text_it_sits_in():
    f = _feat(kind="Rectangle", object_style="Form Fields", content_kind="path")
    rule = _decide(f)
    assert rule.rule_id == "form.field"
    assert rule.action == rtl_plan.RTL_MIRROR


@pytest.mark.parametrize("kind", ["TextBox", "CheckBox", "RadioButton"])
def test_every_form_control_kind_mirrors(kind):
    f = _feat(kind=kind, content_kind="empty")
    rule = _decide(f)
    assert rule.rule_id == "form.field", kind
    assert rule.action == rtl_plan.RTL_MIRROR


@pytest.mark.parametrize("language", [None, "ar", "he", "fa", "ur"])
def test_every_rtl_language_gets_the_same_table(language):
    """A half-mirrored page overlaps itself whatever the language, so no
    language keeps content where English left it."""
    table = rtl_rules.get_rules(rtl_rules.DEFAULT_FAMILY, language=language)
    assert table.rules == TABLE.rules
    assert rtl_rules.first_match(table, _feat(), CTX, None).action == rtl_plan.RTL_MIRROR


def test_furniture_outranks_the_content_rules():
    master = _feat(is_master_item=True, content_kind="text", kind="TextFrame")
    badge = _feat(paragraph_styles=frozenset({"_Family Letter:FL Lesson #"}),
                  content_kind="text", kind="TextFrame")
    title = _feat(paragraph_styles=frozenset({"_Family Letter:FL lesson title"}),
                  content_kind="text", kind="TextFrame", rotated=True)
    for f in (master, badge, title):
        rule = _decide(f)
        assert rule.rule_id in rtl_rules.FURNITURE_RULES
        assert rule.action == rtl_plan.KEEP_POSITION


def test_a_running_head_is_content_not_the_lesson_badge():
    """Filed in the same `_Master Page Styles:` group as the badge, but the
    human Arabic reference mirrors it with the page."""
    head = _feat(paragraph_styles=frozenset(
        {"_Master Page Styles:Navigation (Primary)"}),
        content_kind="text", kind="TextFrame", script_mix="latin")
    rule = _decide(head)
    assert rule.rule_id not in rtl_rules.FURNITURE_RULES
    assert rule.action == rtl_plan.RTL_MIRROR


def test_a_direction_line_style_is_not_mistaken_for_the_badge():
    f = _feat(paragraph_styles=frozenset({"Direction line (Lesson)"}),
              content_kind="text", kind="TextFrame")
    assert _decide(f).rule_id != "master.lesson_badge"


def test_decorative_bleed_rules_do_not_depend_on_language():
    master = _feat(content_kind="raster", full_bleed=True, is_master_item=True)
    page = _feat(content_kind="raster", full_bleed=True)
    for language in (None, "he", "fa", "ur", "ar"):
        table = rtl_rules.get_rules(rtl_rules.DEFAULT_FAMILY, language=language)
        assert rtl_rules.first_match(table, master, CTX, None).rule_id == "graphic.decorative_bleed"
        assert rtl_rules.first_match(table, page, CTX, None).rule_id == "graphic.content_bleed"
