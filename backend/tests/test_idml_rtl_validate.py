"""The harness has to catch the failures we actually fear."""

from lxml import etree

from pagebirdy.idml import rtl_features, rtl_plan, rtl_validate

SPREAD = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"
          AppliedMaster="MasterSpread/A"/>
    {items}
  </Spread>
</idPkg:Spread>
"""


def _rect(self_id):
    return f"""<Rectangle Self="{self_id}" ItemTransform="1 0 0 1 0 0">
      <Properties><PathGeometry><GeometryPathType><PathPointArray>
        <PathPointType Anchor="0 0"/><PathPointType Anchor="0 10"/>
        <PathPointType Anchor="10 10"/><PathPointType Anchor="10 0"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </Rectangle>"""


def _docs(items, master="MasterSpread/A"):
    xml = SPREAD.format(items=items).replace('AppliedMaster="MasterSpread/A"',
                                             f'AppliedMaster="{master}"')
    return {"Spreads/S.xml": etree.fromstring(xml.encode())}


def test_clean_output_reports_no_violations():
    src = _docs(_rect("a") + _rect("b"))
    out = _docs(_rect("a") + _rect("b"))
    assert rtl_validate.check_invariants(src, out) == []


def test_a_dropped_object_is_a_violation():
    src = _docs(_rect("a") + _rect("b"))
    out = _docs(_rect("a"))
    assert any("b" in v for v in rtl_validate.check_invariants(src, out))


def test_a_duplicated_object_is_a_violation():
    src = _docs(_rect("a"))
    out = _docs(_rect("a") + _rect("a"))
    assert any("duplicate" in v.lower()
               for v in rtl_validate.check_invariants(src, out))


def test_reordered_stacking_is_a_violation():
    src = _docs(_rect("a") + _rect("b"))
    out = _docs(_rect("b") + _rect("a"))
    assert any("order" in v.lower()
               for v in rtl_validate.check_invariants(src, out))


def test_a_changed_applied_master_is_a_violation():
    src = _docs(_rect("a"))
    out = _docs(_rect("a"), master="MasterSpread/B")
    assert any("master" in v.lower()
               for v in rtl_validate.check_invariants(src, out))


def test_plan_coverage_reports_the_default_keep_share():
    plan = rtl_plan.Plan(
        document="d", language="ar", rules_family="f",
        decisions=[
            rtl_plan.Decision(
                page=0, spread="spr", object=str(i), component=None,
                type="Rectangle", layer=None, object_style=None,
                paragraph_styles=(), bounds=None, new_bounds=None,
                orientation=rtl_plan.KEEP_ORIENTATION,
                new_orientation=rtl_plan.KEEP_ORIENTATION,
                action=rtl_plan.KEEP_POSITION, text=rtl_plan.KEEP_TEXT,
                rule="default.keep" if i < 3 else "text.prose", reason="r")
            for i in range(4)])
    cov = rtl_validate.plan_coverage(plan)
    assert cov["total"] == 4
    assert cov["default_keep"] == 3
    assert cov["by_rule"]["text.prose"] == 1


# ---- addition 1: a plan built before translation must be caught -----------
#
# `script_mix` is "latin" for untranslated English prose, so a plan built
# before translation classifies every prose frame as `text.ltr_only` (Latin,
# pinned) and never as `text.prose` (Arabic/mixed). At runtime the plan is
# built *after* translation and nothing else asserts that ordering, so this
# is the one guard against a plan silently scored -- or shipped -- against
# the wrong-language text.

def _decision(object_id, rule):
    return rtl_plan.Decision(
        page=0, spread="spr", object=object_id, component=None,
        type="TextFrame", layer=None, object_style=None,
        paragraph_styles=(), bounds=None, new_bounds=None,
        orientation=rtl_plan.KEEP_ORIENTATION,
        new_orientation=rtl_plan.KEEP_ORIENTATION,
        action=rtl_plan.TEXT_ONLY_RTL, text=rtl_plan.TEXT_RTL,
        rule=rule, reason="r")


def test_a_pre_translation_plan_is_flagged_for_an_rtl_target():
    # Every prose frame read as untranslated Latin script: text.ltr_only
    # fires, text.prose never does. That combination is the tell.
    plan = rtl_plan.Plan(document="d", language="ar", rules_family="f",
                         decisions=[_decision("t1", "text.ltr_only"),
                                    _decision("t2", "text.ltr_only")])
    cov = rtl_validate.plan_coverage(plan)
    assert cov["warnings"]
    assert any("untranslated" in w or "before translation" in w
               for w in cov["warnings"])


def test_a_post_translation_plan_is_not_flagged():
    # Once translated, at least some prose reads as Arabic/mixed and
    # text.prose fires -- the same page shape, no warning.
    plan = rtl_plan.Plan(document="d", language="ar", rules_family="f",
                         decisions=[_decision("t1", "text.prose"),
                                    _decision("t2", "text.ltr_only")])
    cov = rtl_validate.plan_coverage(plan)
    assert cov["warnings"] == []


def test_an_ltr_target_language_is_never_flagged():
    # The failure mode is specific to RTL targets (script_mix driving
    # text.ltr_only vs text.prose only matters when direction is rtl).
    plan = rtl_plan.Plan(document="d", language="es", rules_family="f",
                         decisions=[_decision("t1", "text.ltr_only"),
                                    _decision("t2", "text.ltr_only")])
    cov = rtl_validate.plan_coverage(plan)
    assert cov["warnings"] == []


# ---- addition 2: a full-bleed raster must be classified as bleed ----------
#
# An earlier defect had exactly this shape: a master-page rule (`master.item`)
# shadowed `graphic.decorative_bleed`, so the honeycomb header banner shipped
# un-mirrored. This is a corpus invariant a validator should have caught.

def _bleed_docs():
    # A 612pt-wide page; a raster that overhangs both edges is full bleed
    # (see test_idml_rtl_features.test_collect_marks_a_full_bleed_item).
    items = """<Rectangle Self="banner" ItemTransform="1 0 0 1 0 0">
      <Properties><PathGeometry><GeometryPathType><PathPointArray>
        <PathPointType Anchor="-6 0"/><PathPointType Anchor="-6 100"/>
        <PathPointType Anchor="618 100"/><PathPointType Anchor="618 0"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
      <Image Self="im"><Link LinkResourceURI="file:/links/banner.png"/></Image>
    </Rectangle>"""
    return _docs(items)


def test_a_correctly_classified_bleed_raster_is_clean():
    docs = _bleed_docs()
    (feat,) = rtl_features.collect(docs)
    assert feat.full_bleed and feat.content_kind == "raster"
    plan = rtl_plan.Plan(document="d", language="ar", rules_family="f",
                         decisions=[_decision("banner", "graphic.decorative_bleed")])
    assert rtl_validate.check_full_bleed_rasters(docs, plan) == []


def test_a_shadowed_bleed_raster_is_a_violation():
    docs = _bleed_docs()
    # Same object, but classified by a style/text rule instead of the bleed
    # rule -- reproduces the master.item-shadows-decorative_bleed defect.
    plan = rtl_plan.Plan(document="d", language="ar", rules_family="f",
                         decisions=[_decision("banner", "master.item")])
    violations = rtl_validate.check_full_bleed_rasters(docs, plan)
    assert any("banner" in v for v in violations)


def test_default_keep_is_also_an_acceptable_bleed_classification():
    docs = _bleed_docs()
    plan = rtl_plan.Plan(document="d", language="ar", rules_family="f",
                         decisions=[_decision("banner", "default.keep")])
    assert rtl_validate.check_full_bleed_rasters(docs, plan) == []
