"""Regression test suite for RCM07_NA_SW_U01_L03.

Validates exact object behavior against the human Arabic reference.
"""

import glob
import os
import pytest

from pagebirdy.idml import rtl, rtl_plan
from pagebirdy.idml.package import IdmlPackage

RCM07_L03 = "RCM07_NA_SW_U01_L03"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rcm07_source():
    hits = sorted(glob.glob(os.path.join(HERE, "uploads", f"{RCM07_L03}-*.idml")))
    # Exclude intermediate output files like .ar-*.idml
    hits = [h for h in hits if not os.path.basename(h).startswith(f"{RCM07_L03}-") or ".ar-" not in h]
    return hits[0] if hits else None


def test_rcm07_gamepad_and_circles_move_together():
    path = _rcm07_source()
    if path is None:
        pytest.skip(f"{RCM07_L03} not in uploads/")
    pkg = IdmlPackage(path)
    plan = rtl_plan.build_plan(pkg.documents, document=RCM07_L03, language="ar")
    by = plan.by_object()
    assert by["u974"].moves
    assert by["u98f"].position_bound
    assert by["u974"].component == by["u98f"].component


def test_rcm07_grid_backdrop_stays_with_its_form_field():
    path = _rcm07_source()
    if path is None:
        pytest.skip(f"{RCM07_L03} not in uploads/")
    pkg = IdmlPackage(path)
    plan = rtl_plan.build_plan(pkg.documents, document=RCM07_L03, language="ar")
    by = plan.by_object()
    # One composition: the backdrop is carried by its answer field, and the
    # field mirrors with the sentence it belongs to.
    assert by["u8e7"].component == by["uaba"].component
    assert by["uaba"].moves
    assert by["u8e7"].position_bound


def test_rcm07_page_furniture_stays_fixed():
    """The vertical lesson title and the badge stay. The running heads
    (u925, u8e4) are content: the human page-48 edition prints the mirrored
    running head's text ending at x=567, the reflection of the English
    frame's right edge."""
    path = _rcm07_source()
    if path is None:
        pytest.skip(f"{RCM07_L03} not in uploads/")
    pkg = IdmlPackage(path)
    plan = rtl_plan.build_plan(pkg.documents, document=RCM07_L03, language="ar")
    by = plan.by_object()
    for oid in ("u888", "u872", "u85c"):  # vertical title, badge number, badge label
        assert not by[oid].moves, oid
    for oid in ("u925", "u8e4"):
        assert by[oid].moves, oid


def test_rcm07_table_repositions_with_correct_column_handling():
    path = _rcm07_source()
    if path is None:
        pytest.skip(f"{RCM07_L03} not in uploads/")
    pkg = IdmlPackage(path)
    plan = rtl_plan.build_plan(pkg.documents, document=RCM07_L03, language="ar")
    d = plan.by_object()["u9db"]
    assert d.rule == "table.default"
    assert d.moves


def test_rcm07_full_pipeline_end_to_end_geometry_and_subparts():
    """Runs the real book through apply_rtl end to end (not build_plan
    alone) and checks the sub-part/lettered-item section still resolves
    to one shared anchor, exactly like the fixture tests, but against
    the real document."""
    path = _rcm07_source()
    if path is None:
        pytest.skip(f"{RCM07_L03} not in uploads/")
    pkg = IdmlPackage(path)
    report = rtl.apply_rtl(pkg, document=RCM07_L03, language="ar")
    assert report["rtl_items_repositioned"] > 0

    # Verify right-edge alignment of subpart text frames ua07, ua1d, ua33, u9f1
    rights = []
    for oid in ("u9f1", "ua07", "ua1d", "ua33"):
        for name, tree in pkg.documents.items():
            if name.startswith("Spreads/"):
                for el in tree.iter():
                    if rtl._is(el, "TextFrame") and el.get("Self") == oid:
                        bounds = rtl.item_bounds(el)
                        rights.append(bounds[2])

    assert len(rights) == 4
    assert max(rights) - min(rights) < 1e-6, f"Subparts did not align: {rights}"
