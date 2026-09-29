"""The paired books, as a regression gate.

Skipped when the corpus is not present, so the suite still runs on a clean
checkout.
"""

import glob
import os

import pytest

from pagebirdy.idml import rtl, rtl_features, rtl_plan, rtl_rules, rtl_validate
from pagebirdy.idml.package import IdmlPackage

BOOKS = ["RCM08_NA_SW_U01_L01", "RCM08_NA_SW_U01_L02", "RCM08_NA_SW_U02_L04",
         "RCM08_NA_SW_U02_L05", "RCM08_NA_SW_U02_L07", "RCM08_NA_SW_U03_L09",
         "RCM08_NA_SW_U03_L10", "RCM08_NA_SW_U03_L12", "RCM08_NA_SW_U03_L13",
         "iRCM01_NA_SW_U01_L01"]

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _source(book):
    hits = sorted(glob.glob(os.path.join(HERE, "uploads", f"{book}-*.idml")))
    return hits[0] if hits else None


@pytest.mark.parametrize("book", BOOKS)
def test_conversion_preserves_every_structural_invariant(book):
    path = _source(book)
    if path is None:
        pytest.skip(f"{book} not in uploads/")

    source = IdmlPackage(path)
    before = {k: v for k, v in source.documents.items()}
    target = IdmlPackage(path)
    plan = rtl_plan.build_plan(target.documents, document=book, language="ar")
    rtl.apply_plan(target.documents, plan)

    assert rtl_validate.check_invariants(before, target.documents) == []


@pytest.mark.parametrize("book", BOOKS)
def test_the_page_template_never_moves(book):
    """The badge, the vertical title and master furniture stay where the
    template put them while the page's content mirrors around them."""
    path = _source(book)
    if path is None:
        pytest.skip(f"{book} not in uploads/")

    pkg = IdmlPackage(path)
    plan = rtl_plan.build_plan(pkg.documents, document=book, language="ar")
    furniture = [d for d in plan.decisions if d.rule in rtl_rules.FURNITURE_RULES]
    assert furniture, f"{book} has no template furniture; check the rules"
    assert [d for d in furniture if d.moves] == []


@pytest.mark.parametrize("book", BOOKS)
def test_mirroring_adds_no_visible_overlap(book):
    """Every piece of a page's content mirrored about the same axis cannot
    land on another; what is left to overlap is only what did not move. The
    known exceptions are listed by object id and each one is explained."""
    path = _source(book)
    if path is None:
        pytest.skip(f"{book} not in uploads/")

    source = IdmlPackage(path)
    before = dict(source.documents)
    hidden = rtl_validate.hidden_layers(source.document("designmap.xml"))
    target = IdmlPackage(path)
    rtl.apply_rtl(target, document=book, language="ar")

    # iRCM01's human edition mirrors its lesson badge together with the badge
    # art on its master page; this pipeline leaves master pages as drawn, so
    # the mirrored "Dear Family" heading lands under the badge that stayed.
    #
    # A photograph bleeding off a right-hand page's outer trim cannot take that
    # bleed over the spine (`rtl.keep_on_page`), so it stops at the spine and
    # shows its bleed's width on the page instead -- moved, never trimmed.
    # Where English set a frame flush against the photo, that width lands on
    # the frame's far end. Both frames hold one short right-aligned line with
    # no text wrap on either side, so the overlap covers empty frame, not type:
    # L05 p98's direction line by 0.8pt, L07 p138's running head by 13.5pt.
    #
    # The Family Letter's badge circle is template furniture and stays; the
    # "Dear Family" frame beside it mirrors about the area the side strip
    # leaves, and its empty right-hand inset runs under the circle's left
    # edge. Rendered in InDesign 2026 with Arabic text (2026-09-15): every
    # line of that frame ends at x 475.5 on L04 p81 and L05 p93, left of the
    # circle's leftmost point at 480.8 -- frame over circle, never type.
    expected = {"iRCM01_NA_SW_U01_L01": [("u4d6", "u502")],
                "RCM08_NA_SW_U02_L04": [("u86b", "u895")],
                "RCM08_NA_SW_U02_L05": [("u864", "u8a7"), ("ue58", "ue8e")],
                "RCM08_NA_SW_U02_L07": [("u914", "u9c0")]}.get(book, [])
    assert rtl_validate.new_overlaps(before, target.documents, hidden) == expected


# Measured 2026-09-13 with page content mirroring (every object that is not
# template furniture mirrors within its page). Roughly half of each book's
# decisions move; the rest are template furniture, anchored objects placed by
# text flow, and items carried by a parent that moves. Accepted only after
# checking the result against every human Arabic reference in `Reference/`:
# across all 22 reference pages, the share of the human edition's text lines
# that fall inside one of our visible content frames rose from 73% (English
# layout, nothing mirrored) to 85%, with no page scoring lower than before.
# Backdrops drawn around an answer field and graphics stacked under one
# another are carried by their component's anchor (`rtl_components`), so they
# count as bound rather than moved here while still crossing the page.
# Re-measured 2026-09-14: each book's count rose by exactly its number of
# inline text boxes (`anchored.text_box`), whose text frame now crosses to the
# other side of its own box -- 2, 6, 6, 6 and 6 in L01, L02, L07, L09 and L10.
# Spread geometry was byte-identical before and after in all 25 sample books.
# Re-measured 2026-09-15: a Family Letter page's own copies of what its master
# sets on the side strip -- badge circle, strip, Math Tools box and labels,
# folio, the "next page" callout (`structure.template_band`) -- stopped moving.
# Every decision that changed is one of those or content that had been bound
# into a cluster with one and now moves on its own; iRCM01 has no strip and is
# unchanged.
_EXPECTED_MOVED_FLIPPED = {
    "RCM08_NA_SW_U01_L01": (264, 1),
    "RCM08_NA_SW_U01_L02": (513, 3),
    "RCM08_NA_SW_U02_L04": (262, 2),
    "RCM08_NA_SW_U02_L05": (367, 3),
    "RCM08_NA_SW_U02_L07": (406, 4),
    "RCM08_NA_SW_U03_L09": (512, 3),
    "RCM08_NA_SW_U03_L10": (401, 2),
    "RCM08_NA_SW_U03_L12": (264, 0),
    "RCM08_NA_SW_U03_L13": (633, 1),
    "iRCM01_NA_SW_U01_L01": (687, 1),
}


@pytest.mark.parametrize("book", BOOKS)
def test_moved_and_flipped_counts_match_recorded_baseline(book):
    """Pinning the exact measured count means any change -- content that
    stops mirroring, or furniture that starts -- fails the gate instead of
    sliding through unnoticed."""
    path = _source(book)
    if path is None:
        pytest.skip(f"{book} not in uploads/")

    pkg = IdmlPackage(path)
    plan = rtl_plan.build_plan(pkg.documents, document=book, language="ar")
    cov = rtl_validate.plan_coverage(plan)
    assert (cov["moved"], cov["flipped"]) == _EXPECTED_MOVED_FLIPPED[book]


@pytest.mark.parametrize("book", BOOKS)
def test_every_full_bleed_raster_resolves_through_the_allowed_rules(book):
    """A full-bleed raster's answer must come from a bleed rule or the
    catch-all, never from a style or text rule -- an earlier defect
    had `master.item` shadow the bleed rule and silently ship an un-mirrored
    header banner. See `rtl_validate.check_full_bleed_rasters`."""
    path = _source(book)
    if path is None:
        pytest.skip(f"{book} not in uploads/")

    pkg = IdmlPackage(path)
    plan = rtl_plan.build_plan(pkg.documents, document=book, language="ar")
    assert rtl_validate.check_full_bleed_rasters(pkg.documents, plan) == []


@pytest.mark.parametrize("book", BOOKS)
def test_no_form_field_is_left_behind_by_its_sentence(book):
    """An answer blank is drawn over the sentence it belongs to; the sentence
    mirrors, so the blank has to go with it rather than stay where English
    left it."""
    path = _source(book)
    if path is None:
        pytest.skip(f"{book} not in uploads/")

    pkg = IdmlPackage(path)
    plan = rtl_plan.build_plan(pkg.documents, document=book, language="ar")
    fields = [d for d in plan.decisions if d.rule == "form.field"]
    assert fields, f"{book} has no form-field-styled objects; check the corpus"
    assert [f for f in fields if not f.moves] == []


@pytest.mark.parametrize("book", BOOKS)
def test_mixed_content_reaching_the_default_mirror_is_a_known_set(book):
    """content_kind == "mixed" is not protected by rules 11/12 (see the
    design spec's 'Risks and open items'), so any object reaching
    default.mirror this way needs individual human review against the
    reference PDF before it's accepted -- pinning the known set means a
    rule change that pushes a NEW one onto this path fails here instead of
    shipping unreviewed."""
    path = _source(book)
    if path is None:
        pytest.skip(f"{book} not in uploads/")

    pkg = IdmlPackage(path)
    plan = rtl_plan.build_plan(pkg.documents, document=book, language="ar")
    features = {f.self_id: f for f in rtl_features.collect(pkg.documents)}
    mixed_mirrored = {d.object for d in plan.decisions
                      if d.rule == "default.mirror"
                      and features.get(d.object) is not None
                      and features[d.object].content_kind == "mixed"}
    expected = {"iRCM01_NA_SW_U01_L01": {"u53d", "u727"}}.get(book, set())
    assert mixed_mirrored == expected, (
        f"{book}: mixed-content objects reaching default.mirror changed "
        f"(was {expected}, now {mixed_mirrored}) -- review each new object "
        "against the human Arabic reference before accepting it")


# These two resolve rotation and alignment from the XML directly rather than
# calling the helpers in `idml.rtl` that the fix added. A regression gate that
# asks the implementation which frames are turned, and what they resolve to,
# would still pass if the implementation were wrong about both.


def _effective_alignment(pkg, para):
    """What InDesign aligns `para` by: its own value, else the nearest style
    up the BasedOn chain declaring one, else the document default."""
    own = para.get("Justification")
    if own:
        return own
    styles = {}
    for name, tree in pkg.documents.items():
        if not name.startswith(("Resources/", "Stories/")):
            continue
        for el in tree.iter():
            if isinstance(el.tag, str) and el.tag.rsplit("}", 1)[-1] == "ParagraphStyle" \
                    and el.get("Self"):
                styles[el.get("Self")] = el
    style, seen = styles.get(para.get("AppliedParagraphStyle")), set()
    while style is not None and id(style) not in seen:
        seen.add(id(style))
        if style.get("Justification"):
            return style.get("Justification")
        based = style.find("./{*}Properties/{*}BasedOn")
        style = styles.get((based.text or "").strip()) if based is not None else None
    for el in pkg.document("Resources/Preferences.xml").iter():
        if isinstance(el.tag, str) and el.tag.rsplit("}", 1)[-1] == "TextDefault":
            return el.get("Justification")
    return None


def _turned_story_ids(pkg):
    """Stories flowed by a frame whose x-axis has left the page's horizontal.

    A transform maps the frame's x-axis to `(a, b)`; a non-zero `b` has swung
    it off the page's horizontal. Composed down the tree, since a group can
    carry the rotation instead of the frame.
    """
    turned = set()

    def walk(node, parent):
        for el in node:
            if not isinstance(el.tag, str) or el.get("ItemTransform") is None:
                continue
            t = rtl.compose(parent, rtl.parse_transform(el.get("ItemTransform")))
            if el.get("ParentStory") and abs(t[1]) > 1e-9:
                turned.add(el.get("ParentStory"))
            walk(el, t)

    for name, tree in pkg.documents.items():
        if not name.startswith(("Spreads/", "MasterSpreads/")):
            continue
        for spread in tree.iter("Spread", "MasterSpread"):
            walk(spread, rtl.IDENTITY)
    return turned


def _turned_paragraphs(pkg):
    """Every paragraph flowed by a frame turned off the page's horizontal."""
    turned = _turned_story_ids(pkg)
    out = []
    for name, tree in pkg.documents.items():
        if not name.startswith("Stories/"):
            continue
        for story in tree.iter("Story"):
            if story.get("Self") in turned:
                out.extend(story.iter("{*}ParagraphStyleRange"))
    return out


@pytest.mark.parametrize("book", BOOKS)
def test_the_vertical_lesson_title_keeps_its_place_in_the_side_margin(book):
    """The vertical title declares no alignment at any level, so it takes the
    document default -- which the RTL pass flips for every ordinary,
    upright paragraph. Its frame is turned 90 degrees, so that flip walks
    the title from the top of the blue side margin to the bottom while its
    `ItemTransform` never changes, which is why comparing geometry alone
    reports nothing moved. Asserted as "the alignment it resolved to before
    is the alignment it resolves to after" -- no coordinate, no page, no
    object id."""
    path = _source(book)
    if path is None:
        pytest.skip(f"{book} not in uploads/")

    pkg = IdmlPackage(path)
    before = [_effective_alignment(pkg, p) for p in _turned_paragraphs(pkg)]
    if not before:
        pytest.skip(f"{book} places no turned text frame")

    rtl.apply_rtl(pkg, document=book, language="ar")

    after = [_effective_alignment(pkg, p) for p in _turned_paragraphs(pkg)]
    assert after == before


@pytest.mark.parametrize("book", BOOKS)
def test_a_turned_title_still_reads_right_to_left(book):
    """Holding the alignment must not cost the title its RTL treatment --
    position and text are independent fields."""
    path = _source(book)
    if path is None:
        pytest.skip(f"{book} not in uploads/")

    pkg = IdmlPackage(path)
    if not _turned_paragraphs(pkg):
        pytest.skip(f"{book} places no turned text frame")

    rtl.apply_rtl(pkg, document=book, language="ar")

    paragraphs = _turned_paragraphs(pkg)
    assert paragraphs
    for para in paragraphs:
        assert para.get("ParagraphDirection") == "RightToLeftDirection"
        assert para.get("Composer", "").endswith("Optyca")


@pytest.mark.parametrize("book", BOOKS)
def test_a_turned_frame_is_never_moved_by_the_geometry_engine_either(book):
    """The other half of "keeps its place": the frame's own transform. The
    rule table already says KEEP_POSITION for these; this pins it."""
    path = _source(book)
    if path is None:
        pytest.skip(f"{book} not in uploads/")

    pkg = IdmlPackage(path)
    turned = _turned_story_ids(pkg)
    if not turned:
        pytest.skip(f"{book} places no turned text frame")

    def transforms():
        found = {}
        for name, tree in pkg.documents.items():
            if not name.startswith(("Spreads/", "MasterSpreads/")):
                continue
            for el in tree.iter():
                if isinstance(el.tag, str) and el.get("ParentStory") in turned:
                    found[el.get("Self")] = el.get("ItemTransform")
        return found

    before = transforms()
    assert before
    rtl.apply_rtl(pkg, document=book, language="ar")
    assert transforms() == before


def _every_book():
    """Every distinct source book in uploads/, not only the paired ten --
    containment is a property of the geometry, not of a reference edition."""
    import re

    books = set()
    for path in glob.glob(os.path.join(HERE, "uploads", "*.idml")):
        name = os.path.basename(path)
        if ".ar" in name or "manually" in name:
            continue
        books.add(re.sub(r"-[0-9a-f]{8}\.idml$", "", name))
    return sorted(books) or ["<no corpus>"]


def _first_source(book):
    hits = sorted(h for h in glob.glob(os.path.join(HERE, "uploads", f"{book}-*.idml"))
                  if ".ar" not in os.path.basename(h))
    return hits[0] if hits else None


@pytest.mark.parametrize("book", _every_book())
def test_no_content_crosses_onto_a_neighbouring_page(book):
    """Content on page N reaches neither page N-1 nor N+1 after the mirror.

    The target keeps its left-to-right binding, so an outer-trim bleed carried
    to the spine side prints on the facing page -- the Understand question
    bar on RCM07 L03 page 49, and every Explore band like it."""
    path = _first_source(book)
    if path is None:
        pytest.skip(f"{book} not in uploads/")

    source = IdmlPackage(path)
    before = dict(source.documents)
    target = IdmlPackage(path)
    rtl.apply_rtl(target, document=book, language="ar")

    assert rtl_validate.page_crossings(before, target.documents) == []


RCM07_L03 = "RCM07_NA_SW_U01_L03"


def test_rcm07_pages_48_and_49_mirror_without_a_single_new_overlap():
    """The real spread reported: the gamepad moved while the Game Time /
    Real Time graphic under it stayed, and on page 49 the cat photo and the
    orange box landed on text that had not moved -- five overlaps the English
    page does not have."""
    path = _source(RCM07_L03)
    if path is None:
        pytest.skip(f"{RCM07_L03} not in uploads/")

    source = IdmlPackage(path)
    before = dict(source.documents)
    hidden = rtl_validate.hidden_layers(source.document("designmap.xml"))
    target = IdmlPackage(path)
    rtl.apply_rtl(target, document=RCM07_L03, language="ar")

    assert rtl_validate.new_overlaps(before, target.documents, hidden) == []

    plan = rtl_plan.build_plan(source.documents, document=RCM07_L03, language="ar")
    by = plan.by_object()
    for oid in ("u974", "u980", "u98d", "u9db", "u951", "u93b"):
        assert by[oid].moves, oid
    # The graphic stacked under the gamepad travels as part of its cluster.
    assert by["u98f"].position_bound and by["u98f"].component == by["u974"].component
    for oid in ("uaba", "uabb", "uac0", "uacc", "uace"):  # answer fields
        assert (by[oid].moves or by[oid].position_bound
                or by[oid].rule == "nested.carried"), oid
    assert not by["u888"].moves and not by["u872"].moves  # title and badge


def test_rcm07_game_time_graphic_stays_under_its_gamepad():
    """Two pieces of one picture, reflected about the same axis, keep their
    arrangement: the gamepad is still centred over the graphic."""
    path = _source(RCM07_L03)
    if path is None:
        pytest.skip(f"{RCM07_L03} not in uploads/")

    pkg = IdmlPackage(path)

    def centres():
        feats = {f.self_id: f for f in rtl_features.collect(pkg.documents)}
        return {oid: (feats[oid].bounds[0] + feats[oid].bounds[2]) / 2
                for oid in ("u974", "u98f")}

    before = centres()
    rtl.apply_rtl(pkg, document=RCM07_L03, language="ar")
    after = centres()
    assert after["u974"] != before["u974"]
    assert after["u974"] - after["u98f"] == pytest.approx(before["u98f"] - before["u974"])


def test_rcm07_body_text_keeps_its_margin_from_the_side_strip():
    """Page 47 carries a fixed blue strip down its right edge. Content
    mirrors within the area the strip leaves, so the body frame's clearance
    from the strip in English becomes its clearance from the opposite edge,
    instead of a reflection about the page centre throwing it into the strip."""
    path = _source(RCM07_L03)
    if path is None:
        pytest.skip(f"{RCM07_L03} not in uploads/")

    src = IdmlPackage(path)
    out = IdmlPackage(path)
    rtl.apply_rtl(out, document=RCM07_L03, language="ar")
    spread_src = src.documents["Spreads/Spread_u83b.xml"].find("Spread")
    spread_out = out.documents["Spreads/Spread_u83b.xml"].find("Spread")
    (px0, _, px1, _), = rtl.page_boxes(spread_src)

    plan = rtl_plan.build_plan(src.documents, document=RCM07_L03, language="ar")
    masters = {m.get("Self"): m for name, tree in src.documents.items()
               if name.startswith("MasterSpreads/") for m in tree.iter("MasterSpread")}
    furniture = rtl._fixed_furniture(spread_src, plan.by_object(), masters)
    (axis,) = rtl.content_axes(rtl.page_boxes(spread_src), furniture)
    strip_edge = 2 * axis - px0  # the free area is symmetric about its own axis
    assert axis < (px0 + px1) / 2

    body_src = rtl.item_bounds(spread_src.find(".//*[@Self='u89e']"))
    body_out = rtl.item_bounds(spread_out.find(".//*[@Self='u89e']"))
    assert body_out[0] - px0 == pytest.approx(strip_edge - body_src[2])
    assert body_out[2] <= strip_edge
