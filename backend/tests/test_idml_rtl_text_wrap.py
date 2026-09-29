"""A mirrored object's text wrap keeps type out of it on the side type now meets.

RCM07 L03 page 48, measured in InDesign 2026: the Arabic body text ran into the
gamepad photo and the Game Time graphic beside it, though its frame kept the
English width. Two defects in the wrap offsets, not in the text frame:

1. The gamepad's wrap reached 12pt *into* its frame on the left (`Left=-12`),
   where the photograph has white margin. The mirror carried that inset to the
   right, but the photograph inside is not turned round -- its margin is still
   on the left -- so type was let 12pt into the picture itself.
2. The Game Time graphic moves as part of the gamepad's cluster, so its own
   decision reads `KEEP_POSITION`. Its 18pt gap was gated on that decision and
   stayed on the left, facing the page margin, while the text met its bare
   right edge.
"""

from dataclasses import replace

import glob
import os

import pytest
from lxml import etree

from pagebirdy.idml import rtl, rtl_plan, rtl_validate
from pagebirdy.idml.package import IdmlPackage

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


def _picture(self_id, x0, y0, x1, y1, left, right, content="Image"):
    return f"""<Rectangle Self="{self_id}" ItemTransform="1 0 0 1 0 0">
        {_path(x0, y0, x1, y1)}
        <TextWrapPreference TextWrapSide="LargestArea" TextWrapMode="BoundingBoxTextWrap">
          <Properties><TextWrapOffset Top="0" Left="{left}" Bottom="0" Right="{right}"/></Properties>
        </TextWrapPreference>
        <{content} Self="{self_id}_c" ItemTransform="1 0 0 1 {x0} {y0}"/>
      </Rectangle>"""


def _docs(items):
    return {"Spreads/S.xml": etree.fromstring(SPREAD.format(items=items).encode())}


def _offset(docs, self_id):
    off = docs["Spreads/S.xml"].find(f".//*[@Self='{self_id}']/{{*}}TextWrapPreference//{{*}}TextWrapOffset")
    return float(off.get("Left")), float(off.get("Right"))


def _mirror_all(plan):
    plan.decisions = [replace(d, action=rtl_plan.RTL_MIRROR,
                              new_orientation=d.orientation)
                      for d in plan.decisions]
    return plan


# ---- a picture kept as drawn keeps its inset on its own side ---------------


def test_a_picture_that_is_not_turned_round_keeps_its_inset_where_its_margin_is():
    docs = _docs(_picture("pad", 380, -320, 530, -220, left=-12, right=0))
    plan = _mirror_all(rtl_plan.build_plan(docs, document="d", language="ar"))

    rtl.mirror_item_properties(docs, plan, anchors=False)

    assert _offset(docs, "pad") == (-12, 0)


def test_the_gap_crosses_to_the_mirrored_side_and_the_inset_stays():
    docs = _docs(_picture("pad", 380, -320, 530, -220, left=18, right=-5))
    plan = _mirror_all(rtl_plan.build_plan(docs, document="d", language="ar"))

    rtl.mirror_item_properties(docs, plan, anchors=False)

    # Left: no gap arrives from the right, and the left had no inset.
    # Right: the 18pt gap arrives, less the 5pt of margin the picture has there.
    assert _offset(docs, "pad") == (0, 13)


def test_a_picture_that_is_turned_round_takes_its_inset_with_it():
    docs = _docs(_picture("pad", 380, -320, 530, -220, left=-12, right=0))
    plan = rtl_plan.build_plan(docs, document="d", language="ar")
    plan.decisions = [replace(d, action=rtl_plan.RTL_MIRROR,
                              new_orientation=rtl_plan.MIRROR_GRAPHIC)
                      for d in plan.decisions]

    rtl.mirror_item_properties(docs, plan, anchors=False)

    assert _offset(docs, "pad") == (0, -12)


# ---- a cluster member moves with its cluster --------------------------------


def test_a_cluster_member_takes_its_wrap_gap_along_with_the_clusters_move():
    docs = _docs(_picture("pad", 380, -320, 530, -220, left=-12, right=0)
                 + _picture("game", 375, -220, 541, -123, left=18, right=0,
                            content="PDF"))
    plan = rtl_plan.build_plan(docs, document="d", language="ar")
    by = plan.by_object()
    plan.decisions = [
        replace(by["pad"], action=rtl_plan.RTL_MIRROR, component="cluster:pad",
                component_kind="cluster", new_orientation=by["pad"].orientation),
        replace(by["game"], action=rtl_plan.KEEP_POSITION, component="cluster:pad",
                component_kind="cluster", position_bound=True,
                new_orientation=by["game"].orientation),
    ]

    rtl.mirror_item_properties(docs, plan, anchors=False)

    assert _offset(docs, "game") == (0, 18)


def test_a_cluster_member_whose_cluster_stays_keeps_its_wrap():
    docs = _docs(_picture("pad", 380, -320, 530, -220, left=-12, right=0)
                 + _picture("game", 375, -220, 541, -123, left=18, right=0,
                            content="PDF"))
    plan = rtl_plan.build_plan(docs, document="d", language="ar")
    by = plan.by_object()
    plan.decisions = [
        replace(by["pad"], action=rtl_plan.KEEP_POSITION, component="cluster:pad",
                component_kind="cluster"),
        replace(by["game"], action=rtl_plan.KEEP_POSITION, component="cluster:pad",
                component_kind="cluster", position_bound=True),
    ]

    rtl.mirror_item_properties(docs, plan, anchors=False)

    assert _offset(docs, "game") == (18, 0)
    assert _offset(docs, "pad") == (-12, 0)


# ---- the validator states the guarantee in geometry --------------------------


def test_the_validator_reports_a_picture_that_lets_text_in_on_its_new_side():
    source = _docs(_picture("pad", 380, -320, 530, -220, left=-12, right=0))
    output = _docs(_picture("pad", 82, -320, 232, -220, left=0, right=-12))

    (msg,) = rtl_validate.wrap_clearance_losses(source, output)
    assert "'pad'" in msg


def test_the_validator_accepts_the_corrected_wrap():
    source = _docs(_picture("pad", 380, -320, 530, -220, left=-12, right=18))
    output = _docs(_picture("pad", 82, -320, 232, -220, left=6, right=0))

    assert rtl_validate.wrap_clearance_losses(source, output) == []


# ---- the real books ----------------------------------------------------------

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = ["RCM07_NA_SW_U01_L03", "RCM08_NA_SW_U01_L01", "RCM08_NA_SW_U01_L02",
         "RCM08_NA_SW_U02_L04", "RCM08_NA_SW_U02_L05", "RCM08_NA_SW_U02_L07",
         "RCM08_NA_SW_U03_L09", "RCM08_NA_SW_U03_L10", "RCM08_NA_SW_U03_L12",
         "RCM08_NA_SW_U03_L13", "iRCM01_NA_SW_U01_L01"]


def _source(book):
    hits = sorted(h for h in glob.glob(os.path.join(HERE, "uploads", f"{book}-*.idml"))
                  if ".ar" not in os.path.basename(h))
    return hits[0] if hits else None


@pytest.mark.parametrize("book", BOOKS)
def test_no_mirrored_object_lets_text_closer_than_the_source_did(book):
    path = _source(book)
    if path is None:
        pytest.skip(f"{book} not in uploads/")

    before = dict(IdmlPackage(path).documents)
    target = IdmlPackage(path)
    rtl.apply_rtl(target, document=book, language="ar")

    assert rtl_validate.wrap_clearance_losses(before, target.documents) == []
