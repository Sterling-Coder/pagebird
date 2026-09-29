"""RTL layout for the IDML path: text direction, and selectively adapted geometry.

`idml.rtl.apply_rtl` -- the one call the pipeline makes for an RTL target --
runs `idml.rtl_plan.build_plan` and `apply_plan` as part of its own work now,
so most assertions below are still "stays exactly where it was": every rule
in `idml.rtl_rules` except one closing case protects an object's position.
The one exception is `language == "ar"` on `curriculum-associates-rcm`, the
default family every fixture here uses -- there, an object no rule
recognises mirrors instead. Tests that assert "nothing moves" therefore use
`language="he"` (a real RTL target with no reference corpus, and so no
mirrored default) to isolate the text-direction behaviour from the geometry
engine's; tests that specifically exercise the mirrored default use
`language="ar"` and are named accordingly. The engine itself is tested on
its own terms in `tests/test_idml_rtl_plan.py`, `tests/test_idml_rtl_executor.py`,
`tests/test_idml_rtl_rules.py`; the whole-page mirror in `idml.rtl_legacy`
still exists, unused, kept only for calibration reference --
`tests/test_idml_rtl_legacy.py`.
"""

import gc
import glob
import os

import pytest
from lxml import etree

from pagebirdy.idml import rtl
from pagebirdy.idml.package import IdmlPackage

# A facing-page spread: two 612x783 pages meeting at x=0, so the spread runs
# -612..612 and its mirror axis is 0. Items are children of <Spread>, each
# placing its own path geometry through ItemTransform.
SPREAD = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="2" ItemTransform="1 0 0 1 0 0">
    <Page Self="pL" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 -612 -391.5"/>
    <Page Self="pR" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"/>
    {items}
  </Spread>
</idPkg:Spread>
"""

# A lone page occupying 0..612 — the first page of a facing-pages document.
SINGLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"/>
    {items}
  </Spread>
</idPkg:Spread>
"""


def _rect(self_id, x0, y0, x1, y1, transform="1 0 0 1 0 0"):
    """A frame whose path is written in its own space and placed by transform."""
    return f"""
    <Rectangle Self="{self_id}" ItemTransform="{transform}">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="{x0} {y0}"/>
        <PathPointType Anchor="{x0} {y1}"/>
        <PathPointType Anchor="{x1} {y1}"/>
        <PathPointType Anchor="{x1} {y0}"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </Rectangle>"""


def _spread(items, template=SPREAD):
    return etree.fromstring(template.format(items=items).encode()).find("Spread")


def _item(spread, self_id):
    return spread.find(f".//*[@Self='{self_id}']")


def _bounds(spread, self_id):
    return rtl.item_bounds(_item(spread, self_id))


# ---- axis ------------------------------------------------------------------


def test_page_extents_are_read_per_page():
    assert rtl.page_extents(_spread("")) == [(-612.0, 0.0), (0.0, 612.0)]


def test_lone_page_extent():
    assert rtl.page_extents(_spread("", SINGLE)) == [(0.0, 612.0)]


def test_extents_are_derived_from_page_bounds_not_a_fixed_page_size():
    wide = SINGLE.replace('GeometricBounds="0 0 783 612"',
                          'GeometricBounds="0 0 400 1000"')
    assert rtl.page_extents(_spread("", wide)) == [(0.0, 1000.0)]


def test_item_reflects_about_the_centre_of_the_page_it_sits_on():
    extents = [(-612.0, 0.0), (0.0, 612.0)]
    # A box on the left page mirrors about -306, not about the spread centre.
    assert rtl.mirror_axis_for((-567, 0, -400, 10), extents, 0.0) == -306.0
    assert rtl.mirror_axis_for((45, 0, 200, 10), extents, 0.0) == 306.0


def test_an_item_spanning_both_pages_reflects_about_the_spread_centre():
    # A banner across the gutter belongs to no single page; mirroring it inside
    # one would throw it off the spread.
    extents = [(-612.0, 0.0), (0.0, 612.0)]
    assert rtl.mirror_axis_for((-500, 0, 500, 10), extents, 0.0) == 0.0


def test_a_pasteboard_item_is_left_where_it_was():
    extents = [(-612.0, 0.0), (0.0, 612.0)]
    assert rtl.mirror_axis_for((700, 0, 800, 10), extents, 0.0) is None


def test_a_frame_flush_to_the_spine_belongs_to_the_page_it_covers():
    # The transform arithmetic leaves a frame aligned to the spine at -0.0 or
    # -1e-13. Against a bare "> 0" that reads as overlapping the facing page,
    # which handed these items the spread centre and dropped them on the wrong
    # page — six of them in one real file.
    extents = [(-612.0, 0.0), (0.0, 612.0)]
    for left_edge in (-0.0, -1e-13, 0.0):
        assert rtl.mirror_axis_for((left_edge, 0, 625.5, 10), extents, 0.0) == 306.0


# ---- groups ----------------------------------------------------------------

GROUP = """
    <Group Self="g" ItemTransform="1 0 0 1 100 0">
      {children}
    </Group>"""


def _group(children, transform="1 0 0 1 100 0"):
    return GROUP.replace('ItemTransform="1 0 0 1 100 0"',
                         f'ItemTransform="{transform}"').format(children=children)


def test_group_bounds_come_from_children_when_it_has_no_path_of_its_own():
    spread = _spread(_group(_rect("a", 0, 0, 40, 40) + _rect("b", 100, 10, 160, 90)))
    assert _bounds(spread, "g") == pytest.approx((100, 0, 260, 90))


# ---- text direction --------------------------------------------------------

STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <StoryPreference StoryDirection="LeftToRightDirection"/>
    <ParagraphStyleRange Self="pLeft" Justification="LeftAlign"/>
    <ParagraphStyleRange Self="pRight" Justification="RightAlign"/>
    <ParagraphStyleRange Self="pCentre" Justification="CenterAlign"/>
    <ParagraphStyleRange Self="pBind" Justification="AwayFromBindingSide"/>
    <ParagraphStyleRange Self="pNone"/>
  </Story>
</idPkg:Story>
"""

PREFS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Preferences xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <DocumentPreference PageBinding="LeftToRight" FacingPages="true"/>
  <StoryPreference StoryDirection="LeftToRightDirection"/>
</idPkg:Preferences>
"""


def _story():
    return etree.fromstring(STORY.encode())


def _para(story, self_id):
    return story.find(f".//ParagraphStyleRange[@Self='{self_id}']")


def test_story_direction_becomes_right_to_left():
    story = _story()
    rtl.set_text_direction({"Stories/S.xml": story})
    assert story.find(".//StoryPreference").get("StoryDirection") == "RightToLeftDirection"


def test_every_paragraph_gets_right_to_left_direction():
    story = _story()
    rtl.set_text_direction({"Stories/S.xml": story})
    for para in story.iter("ParagraphStyleRange"):
        assert para.get("ParagraphDirection") == "RightToLeftDirection"


def test_absolute_alignment_flips():
    story = _story()
    rtl.set_text_direction({"Stories/S.xml": story})
    assert _para(story, "pLeft").get("Justification") == "RightAlign"
    assert _para(story, "pRight").get("Justification") == "LeftAlign"


def test_centred_and_binding_relative_alignment_are_left_alone():
    # AwayFromBindingSide already follows the binding, so InDesign re-resolves
    # it when PageBinding flips — flipping it here would mirror it twice.
    story = _story()
    rtl.set_text_direction({"Stories/S.xml": story})
    assert _para(story, "pCentre").get("Justification") == "CenterAlign"
    assert _para(story, "pBind").get("Justification") == "AwayFromBindingSide"
    assert _para(story, "pNone").get("Justification") is None


def test_vertical_justification_is_not_confused_with_alignment():
    story = etree.fromstring(
        b'<Story><ParagraphStyleRange Self="p" VerticalJustification="TopAlign"/></Story>')
    rtl.set_text_direction({"Stories/S.xml": story})
    assert _para(story, "p").get("VerticalJustification") == "TopAlign"


# ---- alignment inside a rotated frame --------------------------------------
#
# `Justification` is measured along the frame's *own* x-axis, not the page's.
# For an upright frame those are the same line, so flipping Left<->Right is
# the reading-direction adaptation it looks like. For a frame turned 90 the
# local x-axis runs down the page, so the same flip is not a direction change
# at all -- it slides the text from one end of the column to the other along
# the page's *vertical* axis, moving an object whose rule said KEEP_POSITION.
# The fixtures below build one rotated and one upright frame from the same
# document so the two can only differ by that.

ROT_SPREAD = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"/>
    <TextFrame Self="fRot" ParentStory="sRot" ItemTransform="0 1 -1 0 557 -247"/>
    <TextFrame Self="fUp" ParentStory="sUp" ItemTransform="1 0 0 1 54 -25"/>
    {extra}
  </Spread>
</idPkg:Spread>
"""

ROT_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="{sid}">
    <StoryPreference StoryDirection="LeftToRightDirection"/>
    <ParagraphStyleRange Self="p" {attrs}/>
  </Story>
</idPkg:Story>
"""

ROT_PREFS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Preferences xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <DocumentPreference PageBinding="LeftToRight" FacingPages="true"/>
  <TextDefault Justification="LeftAlign" ParagraphDirection="LeftToRightDirection"/>
</idPkg:Preferences>
"""


def _rotated_docs(rot_attrs="", up_attrs="", extra=""):
    """One rotated and one upright text frame, a story each, plus a
    `TextDefault` both paragraphs inherit from when they declare nothing."""
    docs = {
        "Spreads/S.xml": etree.fromstring(
            ROT_SPREAD.format(extra=extra).encode()),
        "Stories/Story_sRot.xml": etree.fromstring(
            ROT_STORY.format(sid="sRot", attrs=rot_attrs).encode()),
        "Stories/Story_sUp.xml": etree.fromstring(
            ROT_STORY.format(sid="sUp", attrs=up_attrs).encode()),
    }
    prefs = etree.fromstring(ROT_PREFS.encode())
    docs["Resources/Preferences.xml"] = prefs
    return docs, prefs


def _psr(docs, sid):
    return docs[f"Stories/Story_{sid}.xml"].find(".//ParagraphStyleRange")


def test_a_rotated_frame_keeps_the_alignment_it_inherited():
    """The real corpus case. The vertical lesson title declares no
    `Justification` of its own, so it inherits the document default -- which
    this pass flips for everyone else's benefit. Inherited by a frame turned
    90, that flip walks the title from the top of its side margin to the
    bottom, with its `ItemTransform` never changing (which is why comparing
    geometry alone reports nothing moved). The effective value has to be
    pinned where the source had it."""
    docs, prefs = _rotated_docs()
    rtl.set_text_direction(docs, prefs)
    assert prefs.find(".//TextDefault").get("Justification") == "RightAlign"
    assert _psr(docs, "sRot").get("Justification") == "LeftAlign"


def test_an_upright_frame_still_follows_the_flipped_default():
    """The other half of the same fixture: nothing about the ordinary case
    changes. An upright frame inheriting the default still reads from the
    right, so the pin above must not be handed out to every story."""
    docs, prefs = _rotated_docs()
    rtl.set_text_direction(docs, prefs)
    assert _psr(docs, "sUp").get("Justification") in (None, "RightAlign")
    # It must not be pinned back to the source's left.
    assert _psr(docs, "sUp").get("Justification") != "LeftAlign"


def test_an_explicit_alignment_in_a_rotated_frame_is_not_flipped():
    docs, prefs = _rotated_docs(rot_attrs='Justification="LeftAlign"',
                                up_attrs='Justification="LeftAlign"')
    rtl.set_text_direction(docs, prefs)
    assert _psr(docs, "sRot").get("Justification") == "LeftAlign"
    assert _psr(docs, "sUp").get("Justification") == "RightAlign"


def test_a_rotated_frame_still_gets_every_text_direction_change():
    """Position and text are independent. Holding the alignment must not cost
    the title its Arabic reading direction, digits or composer."""
    docs, prefs = _rotated_docs()
    rtl.set_text_direction(docs, prefs)
    para = _psr(docs, "sRot")
    assert para.get("ParagraphDirection") == "RightToLeftDirection"
    assert para.get("DigitsType") == "DefaultDigits"
    assert para.get("Composer") == "HL Composer Optyca"
    story = docs["Stories/Story_sRot.xml"].find(".//StoryPreference")
    assert story.get("StoryDirection") == "RightToLeftDirection"


def test_a_rotated_frame_keeps_its_indents_on_the_same_side():
    """`LeftIndent`/`RightIndent` are measured along the same local x-axis as
    `Justification`, so swapping them in a turned frame moves the text up or
    down the page for exactly the same reason."""
    docs, prefs = _rotated_docs(rot_attrs='LeftIndent="18"',
                                up_attrs='LeftIndent="18"')
    rtl.set_text_direction(docs, prefs)
    assert _psr(docs, "sRot").get("LeftIndent") == "18"
    assert _psr(docs, "sRot").get("RightIndent") is None
    assert _psr(docs, "sUp").get("RightIndent") == "18"


def test_a_frame_turned_by_its_group_counts_as_rotated():
    """Rotation can live on an ancestor. A frame with an identity transform of
    its own inside a turned <Group> is just as rotated on the page, so the
    test has to be the composed transform, not the frame's own."""
    extra = ('<Group Self="g" ItemTransform="0 1 -1 0 300 -100">'
             '<TextFrame Self="fNested" ParentStory="sNest"'
             ' ItemTransform="1 0 0 1 0 0"/></Group>')
    docs, prefs = _rotated_docs(extra=extra)
    docs["Stories/Story_sNest.xml"] = etree.fromstring(
        ROT_STORY.format(sid="sNest", attrs="").encode())
    rtl.set_text_direction(docs, prefs)
    assert _psr(docs, "sNest").get("Justification") == "LeftAlign"


def test_a_frame_turned_a_half_turn_still_flips():
    """180 degrees leaves the local x-axis lying along the page's own, just
    pointing the other way -- the text still runs across the page, so the
    flip is still the reading-direction change it is for an upright frame.
    Only a frame whose x-axis has left the horizontal is held."""
    extra = ('<TextFrame Self="fHalf" ParentStory="sHalf"'
             ' ItemTransform="-1 0 0 -1 400 -100"/>')
    docs, prefs = _rotated_docs(extra=extra)
    docs["Stories/Story_sHalf.xml"] = etree.fromstring(
        ROT_STORY.format(sid="sHalf", attrs='Justification="LeftAlign"').encode())
    rtl.set_text_direction(docs, prefs)
    assert _psr(docs, "sHalf").get("Justification") == "RightAlign"


def test_one_style_serves_a_turned_and_an_upright_frame_correctly():
    """A paragraph style is shared, and flipping it is right for its upright
    users. The turned frame cannot be served by editing that style either
    way, which is why its own value is made explicit instead."""
    styles = etree.fromstring(
        b'<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">'
        b'<RootParagraphStyleGroup>'
        b'<ParagraphStyle Self="ps/shared" Name="shared" Justification="LeftAlign"/>'
        b'</RootParagraphStyleGroup></idPkg:Styles>')
    docs, prefs = _rotated_docs(rot_attrs='AppliedParagraphStyle="ps/shared"',
                                up_attrs='AppliedParagraphStyle="ps/shared"')
    docs["Resources/Styles.xml"] = styles
    rtl.set_text_direction(docs, prefs)

    assert styles.find(".//ParagraphStyle").get("Justification") == "RightAlign"
    # The upright frame follows the flipped style and declares nothing itself.
    assert _psr(docs, "sUp").get("Justification") is None
    # The turned one says outright where it already was.
    assert _psr(docs, "sRot").get("Justification") == "LeftAlign"


def test_alignment_still_flips_when_no_spread_is_given():
    """Callers that hand in stories alone (most of this file) have no way to
    know a frame's orientation, so nothing is held and the old behaviour
    stands."""
    story = _story()
    rtl.set_text_direction({"Stories/S.xml": story})
    assert _para(story, "pLeft").get("Justification") == "RightAlign"


def test_page_binding_is_left_untouched():
    """Flipping `PageBinding` is what swaps which side of a spread each page
    renders on -- a reviewer comparing page numbers against the English
    source does not want page 85 sliding to the left of page 84."""
    prefs = etree.fromstring(PREFS.encode())
    rtl.set_text_direction({}, prefs)
    assert prefs.find(".//DocumentPreference").get("PageBinding") == "LeftToRight"


def test_text_direction_moves_no_geometry():
    root = etree.fromstring(SPREAD.format(items=_rect("a", 40, 0, 240, 50)).encode())
    before = _item(root, "a").get("ItemTransform")
    rtl.set_text_direction({"Spreads/S.xml": root})
    assert _item(root, "a").get("ItemTransform") == before


def test_a_source_already_bound_right_to_left_is_recognised():
    prefs = etree.fromstring(PREFS.replace("LeftToRight", "RightToLeft").encode())
    assert rtl.is_rtl_bound(prefs)


def test_a_left_to_right_source_is_not_reported_as_rtl():
    assert rtl.is_rtl_bound(etree.fromstring(PREFS.encode())) is False
    assert rtl.is_rtl_bound(None) is False


# ---- real documents --------------------------------------------------------

# Smallest first: a parsed IdmlPackage costs roughly 30x the file on the heap,
# and holding several at once exhausts the interpreter. The fixture below keeps
# at most one alive.
_SAMPLES = sorted(glob.glob(os.path.join(
    os.path.dirname(__file__), "..", "uploads", "*.idml")), key=os.path.getsize)


@pytest.fixture
def sample():
    """A freshly parsed sample package, released before the next test.

    The package holds every zip entry plus a parsed tree per story and spread —
    around 30MB for the smallest sample. Dropping the reference is not enough:
    the buffers must be cleared and collected here, or the peak carries into
    later tests and pushes the image-heavy OCR suite into a MemoryError on this
    interpreter.
    """
    pkg = IdmlPackage(_SAMPLES[0])
    yield pkg
    for buffer in (pkg._entries, pkg._docs, pkg._stories, pkg._node_index):
        buffer.clear()
    del pkg
    gc.collect()


def test_a_bleed_overhanging_the_spine_still_belongs_to_its_own_page():
    """The failure `validate_rtl_idml` found in a real book.

    A full-bleed backdrop is drawn larger than its page in every direction, so
    on the spine side it laps a fraction of a point onto the facing page.
    Counted as a genuine overlap, that sliver made the backdrop look like a
    gutter-spanning banner, and reflecting a banner about the *spread* centre
    carried the whole left-page backdrop onto the right page.
    """
    extents = [(-612.0, 0.0), (0.0, 612.0)]
    assert rtl.mirror_axis_for((-625.38, 0, 0.62, 10), extents, 0.0) == -306.0


def test_a_banner_that_really_spans_the_gutter_still_does():
    """The other side of the same judgement: a real banner covers a large share
    of both pages, not a sliver of one."""
    extents = [(-612.0, 0.0), (0.0, 612.0)]
    assert rtl.mirror_axis_for((-500, 0, 500, 10), extents, 0.0) == 0.0


def _nest(outer: str, inner: str) -> str:
    """Put one page item inside another, the way a frame holds a child frame."""
    head, _, tail = outer.rpartition("</Rectangle>")
    return head + inner + "</Rectangle>" + tail


def test_reflecting_an_outline_ignores_a_nested_item_geometry():
    """An outline is reflected about its own centre, not its children's.

    A frame holding a child frame carries two path geometries. Reflecting
    every `PathPointType` under the item takes the axis from the union of
    both, which shifts the item's own outline by half the difference -- the
    one thing the reflection promises never to do -- and rewrites the child's
    path in the parent's space on top of it.
    """
    spread = _spread(_nest(_rect("outer", 0, 0, 100, 40),
                           _rect("inner", -200, 0, -150, 40)))
    outer, inner = _item(spread, "outer"), _item(spread, "inner")
    before, before_inner = rtl.item_bounds(outer), rtl.item_bounds(inner)

    assert rtl.reflect_path(outer)
    assert rtl.item_bounds(outer) == pytest.approx(before), "the outline moved"
    assert rtl.item_bounds(inner) == pytest.approx(before_inner),         "the nested item's own path was rewritten in its parent's space"


def test_a_wide_frame_overhanging_the_spine_keeps_its_own_page():
    """The failure in RCM08 U01 L01: problem 4 of page 12 printed on page 13.

    The frame is drawn 47.5pt past the spine -- 7.6% of its own 623pt width,
    but 4x the old page-relative floor of 12pt. Judged against the page it
    read as a gutter-spanning banner, so it mirrored about the *spread*
    centre and 92% of it landed on the facing page.
    """
    extents = [(-612.0, 0.0), (0.0, 612.0)]
    assert rtl.pages_of((-576.0, 246.8, 47.5, 282.8), extents) == [0]
    assert rtl.mirror_axis_for((-576.0, 246.8, 47.5, 282.8), extents, 0.0) == -306.0


def test_an_item_mostly_on_the_pasteboard_belongs_to_the_page_it_touches():
    # No page clears the share floor, but the item is not pasteboard furniture
    # either: it still prints. It belongs to the page it overlaps most.
    assert rtl.pages_of((-500.0, 0, 50.0, 10), [(0.0, 612.0)]) == [0]
    assert rtl.pages_of((-660.0, 0, -602.0, 10),
                        [(-612.0, 0.0), (0.0, 612.0)]) == [0]


def test_the_page_an_item_is_on_is_the_one_it_covers_most():
    """A mirrored bleed touches both pages; it is *on* the one it covers
    64.5pt of, not the one it laps 13.5pt over. `idml.validate` asks this
    before and after the mirror to tell a bleed from content that moved."""
    extents = [(-612.0, 0.0), (0.0, 612.0)]
    assert rtl.pages_of((-13.5, 0, 64.5, 10), extents) == [0, 1]
    assert rtl.dominant_page((-13.5, 0, 64.5, 10), extents) == 1
    assert rtl.dominant_page((-576.0, 0, 47.5, 10), extents) == 0
    assert rtl.dominant_page((700, 0, 800, 10), extents) is None


def test_a_small_item_astride_the_spine_belongs_to_both_pages():
    """The sliver test scales with the item, not just the page: 5pt each side
    is half of a 10pt icon, and an icon on the spine stays on the spine."""
    extents = [(-612.0, 0.0), (0.0, 612.0)]
    assert rtl.mirror_axis_for((-5, 0, 5, 10), extents, 0.0) == 0.0


@pytest.mark.skipif(not _SAMPLES, reason="no sample IDML available")
def test_lazy_document_leaves_untouched_entries_byte_identical(sample, tmp_path):
    """An LTR job parses no extra entries, so nothing it never touched is
    re-serialised."""
    import zipfile

    pkg = sample
    out = str(tmp_path / "copy.idml")
    pkg.save(out)

    with zipfile.ZipFile(_SAMPLES[0]) as a, zipfile.ZipFile(out) as b:
        assert a.read("Resources/Preferences.xml") == b.read("Resources/Preferences.xml")


# ---- lazy entry access -----------------------------------------------------

# An IDML carries far more than stories and spreads. `Resources/Preferences.xml`
# holds `PageBinding` and the document's default story direction;
# `Resources/Styles.xml` holds the paragraph styles every frame inherits from.
# Neither is parsed on ingest, because an LTR job never touches them and
# re-serialising an entry we did not change is a needless diff. The RTL stage
# asks for them by name.

FIXTURE_PREFS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Preferences xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <DocumentPreference PageBinding="LeftToRight" FacingPages="true"/>
  <StoryPreference StoryDirection="LeftToRightDirection"/>
</idPkg:Preferences>
"""

FIXTURE_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <RootParagraphStyleGroup Self="root">
    <ParagraphStyle Self="ParagraphStyle/Body" Name="Body" Justification="LeftAlign"/>
  </RootParagraphStyleGroup>
</idPkg:Styles>
"""

FIXTURE_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <StoryPreference StoryDirection="LeftToRightDirection"/>
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body" Justification="LeftAlign">
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Understanding Ratios</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""

# One page 0..612 wide, so the mirror axis is 306. Three items exercise the
# cases a naive mirror breaks: an upright frame, a frame rotated 90 degrees,
# and a group whose children are placed relative to the group.
FIXTURE_ITEMS = (
    _rect("plain", 40, 60, 240, 160)
    + _rect("rotated", 0, 0, 100, 40, transform="0 1 -1 0 500 200")
    + """
    <Group Self="grp" ItemTransform="1 0 0 1 400 500">
      {kid1}
      {kid2}
    </Group>""".format(kid1=_rect("kid1", 0, 0, 60, 30),
                       kid2=_rect("kid2", 80, 0, 140, 30))
)

FIXTURE_SPREAD = SINGLE.format(items=FIXTURE_ITEMS)

PAGE_AXIS = 306.0  # the fixture page runs 0..612


def _make_idml(path, prefs=FIXTURE_PREFS, story=FIXTURE_STORY):
    import zipfile

    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr("Resources/Preferences.xml", prefs)
        z.writestr("Resources/Styles.xml", FIXTURE_STYLES)
        z.writestr("Stories/Story_u10.xml", story)
        z.writestr("Spreads/Spread_u1.xml", FIXTURE_SPREAD)


def _fixture_pkg(tmp_path, prefs=FIXTURE_PREFS, story=FIXTURE_STORY):
    src = str(tmp_path / "in.idml")
    _make_idml(src, prefs, story)
    return IdmlPackage(src)


def _spread_of(idml_path):
    import zipfile

    with zipfile.ZipFile(idml_path) as z:
        return etree.fromstring(z.read("Spreads/Spread_u1.xml")).find("Spread")


def test_ingest_does_not_parse_resources(tmp_path):
    pkg = _fixture_pkg(tmp_path)
    assert "Resources/Preferences.xml" not in pkg.documents


def test_document_parses_an_entry_on_demand(tmp_path):
    pkg = _fixture_pkg(tmp_path)
    prefs = pkg.document("Resources/Preferences.xml")
    assert prefs.find(".//DocumentPreference").get("PageBinding") == "LeftToRight"


def test_document_returns_the_same_element_on_repeat_access(tmp_path):
    """Two callers must edit one tree, or the second save loses the first's
    changes."""
    pkg = _fixture_pkg(tmp_path)
    assert pkg.document("Resources/Preferences.xml") is pkg.document(
        "Resources/Preferences.xml")


def test_document_returns_none_for_an_entry_the_package_does_not_have(tmp_path):
    pkg = _fixture_pkg(tmp_path)
    assert pkg.document("Resources/Nonexistent.xml") is None


def test_a_document_touched_through_the_accessor_is_written_back(tmp_path):
    import zipfile

    pkg = _fixture_pkg(tmp_path)
    pkg.document("Resources/Preferences.xml").find(
        ".//DocumentPreference").set("PageBinding", "RightToLeft")
    out = str(tmp_path / "out.idml")
    pkg.save(out)

    with zipfile.ZipFile(out) as z:
        prefs = etree.fromstring(z.read("Resources/Preferences.xml"))
    assert prefs.find(".//DocumentPreference").get("PageBinding") == "RightToLeft"


# ---- apply_rtl -------------------------------------------------------------


def test_apply_rtl_mirrors_geometry_in_every_rtl_language_without_rebinding(tmp_path):
    """Hebrew mirrors exactly as Arabic does -- a half-mirrored page overlaps
    itself in any language -- and neither turns `PageBinding` round."""
    pkg = _fixture_pkg(tmp_path)
    spread = pkg.documents["Spreads/Spread_u1.xml"].find("Spread")
    before = {el.get("Self"): el.get("ItemTransform")
              for el in spread if rtl._is_page_item(el)}

    report = rtl.apply_rtl(pkg, document="fixture.idml", language="he")

    assert {el.get("Self"): el.get("ItemTransform")
            for el in spread if rtl._is_page_item(el)} != before
    assert report["rtl_text_direction_set"] > 0
    assert report["rtl_items_repositioned"] > 0

    prefs = pkg.document("Resources/Preferences.xml")
    assert prefs.find(".//DocumentPreference").get("PageBinding") == "LeftToRight"


def test_apply_rtl_mirrors_unclassified_geometry_for_arabic(tmp_path):
    """The one language/family combination with a calibrated reference
    corpus: an object no rule in `idml.rtl_rules` recognises mirrors about
    its page axis instead of staying put."""
    pkg = _fixture_pkg(tmp_path)
    spread = pkg.documents["Spreads/Spread_u1.xml"].find("Spread")
    before = {el.get("Self"): el.get("ItemTransform")
              for el in spread if rtl._is_page_item(el)}

    report = rtl.apply_rtl(pkg, document="fixture.idml", language="ar")

    after = {el.get("Self"): el.get("ItemTransform")
             for el in spread if rtl._is_page_item(el)}
    assert after != before
    assert report["rtl_items_repositioned"] > 0


def test_apply_rtl_sets_direction_on_stories(tmp_path):
    pkg = _fixture_pkg(tmp_path)
    rtl.apply_rtl(pkg, document="fixture.idml", language="he")
    story = pkg.documents["Stories/Story_u10.xml"]
    assert story.find(".//StoryPreference").get(
        "StoryDirection") == "RightToLeftDirection"
    para = story.find(".//ParagraphStyleRange")
    assert para.get("ParagraphDirection") == "RightToLeftDirection"
    assert para.get("Justification") == "RightAlign"


def test_apply_rtl_flips_the_shared_paragraph_styles(tmp_path):
    """A frame that never overrides its style inherits alignment from
    `Resources/Styles.xml`. Leaving that file LTR leaves most of the book
    left-aligned however many story runs were flipped."""
    pkg = _fixture_pkg(tmp_path)
    rtl.apply_rtl(pkg, document="fixture.idml", language="he")
    style = pkg.document("Resources/Styles.xml").find(".//ParagraphStyle")
    assert style.get("ParagraphDirection") == "RightToLeftDirection"
    assert style.get("Justification") == "RightAlign"


def test_apply_rtl_moves_no_geometry_on_a_source_already_bound_right_to_left(tmp_path):
    """A source already laid out right to left is not mirrored back to where
    English would have had it -- in any language, Arabic included."""
    pkg = _fixture_pkg(
        tmp_path, prefs=FIXTURE_PREFS.replace("LeftToRight", "RightToLeft"))
    spread = pkg.documents["Spreads/Spread_u1.xml"].find("Spread")
    before = {el.get("Self"): el.get("ItemTransform")
              for el in spread if rtl._is_page_item(el)}

    report = rtl.apply_rtl(pkg, document="fixture.idml", language="ar")

    assert {el.get("Self"): el.get("ItemTransform")
            for el in spread if rtl._is_page_item(el)} == before
    assert report["rtl_items_repositioned"] == 0


def test_apply_rtl_still_sets_text_direction_on_an_rtl_bound_source(tmp_path):
    pkg = _fixture_pkg(
        tmp_path, prefs=FIXTURE_PREFS.replace("LeftToRight", "RightToLeft"))
    rtl.apply_rtl(pkg, document="fixture.idml", language="he")
    story = pkg.documents["Stories/Story_u10.xml"]
    assert story.find(".//StoryPreference").get(
        "StoryDirection") == "RightToLeftDirection"


# A problem-number badge inline-anchored at the top-left of the paragraph it
# introduces -- the correct corner for a sentence that opens left-to-right.
BADGE_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <StoryPreference StoryDirection="LeftToRightDirection"/>
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body" Justification="LeftAlign">
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Understanding Ratios</Content>
        <AnchoredObjectSetting Self="badge1" AnchoredPosition="InlinePosition"
                               AnchorPoint="TopLeftAnchor" HorizontalAlignment="LeftAlign"
                               AnchorXoffset="6"/>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


def test_apply_rtl_mirrors_an_inline_badges_own_anchor(tmp_path):
    """A number badge anchored `TopLeftAnchor`/`LeftAlign` -- the corner where
    its sentence opened left-to-right -- has to move to the corner where that
    same sentence now opens right-to-left, or it prints trailing the line
    it was meant to introduce."""
    pkg = _fixture_pkg(tmp_path, story=BADGE_STORY)
    report = rtl.apply_rtl(pkg, document="fixture.idml", language="he")

    badge = pkg.documents["Stories/Story_u10.xml"].find(".//AnchoredObjectSetting")
    assert badge.get("AnchorPoint") == "TopRightAnchor"
    assert badge.get("HorizontalAlignment") == "RightAlign"
    assert badge.get("AnchorXoffset") == "6"   # measured outward from the side
    assert report["rtl_anchors_mirrored"] == 2


def test_apply_rtl_anchor_mirror_never_touches_frame_geometry(tmp_path):
    """The badge's own text-relative anchor moves; the pass that moves it
    writes no page item's position."""
    pkg = _fixture_pkg(tmp_path, story=BADGE_STORY)
    spread = pkg.documents["Spreads/Spread_u1.xml"].find("Spread")
    before = {el.get("Self"): el.get("ItemTransform")
              for el in spread if rtl._is_page_item(el)}

    assert rtl.mirror_anchored_object_settings(pkg.documents) > 0

    assert {el.get("Self"): el.get("ItemTransform")
            for el in spread if rtl._is_page_item(el)} == before


BLEED_URI = "file:/out/links_ar/bleed.ar.png"
BLEED_RASTER_ITEMS = f"""
    <Rectangle Self="bleed" ItemTransform="1 0 0 1 0 0">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="-6 100"/><PathPointType Anchor="-6 300"/>
        <PathPointType Anchor="618 300"/><PathPointType Anchor="618 100"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
      <Image Self="im" ItemTransform="1 0 0 1 0 0">
        <Link Self="lnk" LinkResourceURI="{BLEED_URI}"/>
      </Image>
    </Rectangle>"""


def _make_bleed_raster_idml(path):
    import zipfile

    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr("Resources/Preferences.xml", FIXTURE_PREFS)
        z.writestr("Resources/Styles.xml", FIXTURE_STYLES)
        z.writestr("Stories/Story_u10.xml", FIXTURE_STORY)
        z.writestr("Spreads/Spread_u1.xml", SINGLE.format(items=BLEED_RASTER_ITEMS))


def test_apply_rtl_threads_keep_upright_to_protect_a_translated_artwork_link(tmp_path):
    """`keep_upright` has to survive the trip from the pipeline's call into
    `apply_rtl`, through to `build_plan`'s rule table, or it does nothing.

    Left unprotected, this full-bleed raster is exactly what
    `graphic.decorative_bleed` mirrors for Arabic: `reflect_graphic` composes
    a mirror onto every child that carries its own `ItemTransform`, which
    here is the placed `<Image>` -- its `a` goes from `1` to `-1`. Passing
    the link's URI through `keep_upright` folds it into the rule table's
    `never_flip_links`, so `graphic.decorative_bleed`'s own guard declines
    the frame and it falls to a KEEP_ORIENTATION rule instead: the picture's
    translated type is never turned round a second time."""
    src = str(tmp_path / "in.idml")
    _make_bleed_raster_idml(src)
    pkg = IdmlPackage(src)

    rtl.apply_rtl(pkg, document="fixture.idml", language="ar",
                  keep_upright=(BLEED_URI,))

    spread = pkg.documents["Spreads/Spread_u1.xml"].find("Spread")
    image = _item(spread, "im")
    a, b, c, d = rtl.parse_transform(image.get("ItemTransform"))[:4]
    assert (a, b, c, d) == (1.0, 0.0, 0.0, 1.0)


def test_preferences_is_not_visited_twice(tmp_path):
    """Preferences is handed in explicitly *and* lives under `Resources/`.
    Visiting it from the loop as well double-counts, and means the loop is
    re-deciding what the explicit pass already decided."""
    src = str(tmp_path / "in.idml")
    _make_idml(src)

    prefs = IdmlPackage(src).document("Resources/Preferences.xml")
    direct = rtl.set_text_direction({}, prefs)

    other = IdmlPackage(src).document("Resources/Preferences.xml")
    both = rtl.set_text_direction({"Resources/Preferences.xml": other}, other)
    assert both == direct


# ---- apply_rtl end-to-end: sub-part alignment through the geometry engine --

# These fixtures need one Story/TextFrame pair per sub-part member instead of
# the single-story shape `_make_idml`/`_fixture_pkg` assume, so they build
# their own small package directly.

SUBPART_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="{self_id}">
    <StoryPreference StoryDirection="LeftToRightDirection"/>
    <ParagraphStyleRange Justification="LeftAlign">
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/bold">
        <Content>{marker}.</Content>
      </CharacterStyleRange>
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">
        <Content>\tbody text for {marker}</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


def _subpart_frame(self_id, story_id, x0, y0, x1, y1):
    return f"""
    <TextFrame Self="{self_id}" ParentStory="{story_id}" ItemTransform="1 0 0 1 0 0"
              PreviousTextFrame="n" NextTextFrame="n">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="{x0} {y0}"/><PathPointType Anchor="{x0} {y1}"/>
        <PathPointType Anchor="{x1} {y1}"/><PathPointType Anchor="{x1} {y0}"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
      <TextFramePreference TextColumnCount="1"/>
    </TextFrame>"""


def _make_subpart_idml(path, rows):
    """`rows`: list of (marker, story_id, x0, y0, x1, y1) -- deliberately
    varied widths (x1), the exact shape `rtl_subparts.py`'s own docstring
    describes: one shared left edge (x0=0 for every row), a different right
    edge per row because each frame is only as wide as its own line needed."""
    import zipfile

    items = "".join(_subpart_frame(f"tf_{sid}", sid, x0, y0, x1, y1)
                    for (_m, sid, x0, y0, x1, y1) in rows)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr("Resources/Preferences.xml", FIXTURE_PREFS)
        z.writestr("Resources/Styles.xml", FIXTURE_STYLES)
        for marker, sid, x0, y0, x1, y1 in rows:
            z.writestr(f"Stories/Story_{sid}.xml",
                      SUBPART_STORY.format(self_id=sid, marker=marker))
        z.writestr("Spreads/Spread_u1.xml", SINGLE.format(items=items))


def _subpart_pkg(tmp_path, rows):
    src = str(tmp_path / "subparts.idml")
    _make_subpart_idml(src, rows)
    return IdmlPackage(src)


def _resolved_right_edge(pkg, sid, x1=None):
    """Where the label's right-aligned text starts: the frame's right edge *as
    it is in the output* -- the frames mirror now -- less its right indent."""
    from pagebirdy.idml.styles import StyleIndex

    spread_tree = next(tree for name, tree in pkg.documents.items() if name.startswith("Spreads/"))
    frame_el = next(el for el in spread_tree.iter() if rtl._is(el, "TextFrame") and el.get("Self") in (sid, f"tf_{sid}"))
    bounds = rtl.item_bounds(frame_el)
    story = pkg.documents[f"Stories/Story_{sid}.xml"]
    psr = story.find(".//{*}ParagraphStyleRange")
    index = StyleIndex(pkg.documents.get("Resources/Styles.xml"))
    right_indent = float(index.effective(psr, None, "RightIndent") or 0.0)
    frame = pkg.documents["Spreads/Spread_u1.xml"].find(f".//*[@Self='tf_{sid}']")
    return rtl.item_bounds(frame)[2] - right_indent


def test_apply_rtl_corrects_inconsistent_abcd_indentation_end_to_end():
    """The specific defect observed: sibling sub-part frames sharing one
    English left edge but different original widths must still share one
    correct RTL anchor after the *full* apply_rtl -- not
    normalize_subpart_indentation exercised alone -- with the AR-gated
    geometry engine active alongside it."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path

        rows = [
            ("a", "a", 0, 0, 100, 20),
            ("b", "b", 0, 40, 220, 60),
            ("c", "c", 0, 80, 65, 100),
            ("d", "d", 0, 120, 150, 140),
        ]
        pkg = _subpart_pkg(Path(tmp), rows)

        rtl.apply_rtl(pkg, document="subparts.idml", language="ar")

        # Frames that shared a left edge in English share a right edge once
        # mirrored about one axis, so the labels already line up; whether
        # rtl_subparts had anything left to correct is not the point.
        edges = [_resolved_right_edge(pkg, sid) for (_m, sid, *_rest) in rows]
        assert max(edges) - min(edges) < 1e-6, edges


def test_apply_rtl_aligns_numbered_points_end_to_end():
    """Same guarantee, for numbered points, through the full pipeline call."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path

        rows = [
            ("1", "n1", 0, 0, 90, 20),
            ("2", "n2", 0, 40, 210, 60),
            ("3", "n3", 0, 80, 130, 100),
        ]
        pkg = _subpart_pkg(Path(tmp), rows)

        rtl.apply_rtl(pkg, document="numbers.idml", language="ar")

        edges = [_resolved_right_edge(pkg, sid) for (_m, sid, *_rest) in rows]
        assert max(edges) - min(edges) < 1e-6, edges


# ---- pipeline wiring -------------------------------------------------------


@pytest.fixture
def offline(monkeypatch):
    """No engine keys — the identity engine, so the pipeline runs offline."""
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY",
              "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)


def _translate(tmp_path, lang):
    from pagebirdy.pipeline import translate_idml

    src = str(tmp_path / "in.idml")
    _make_idml(src)
    return translate_idml(src, out_dir=str(tmp_path / "out"),
                          review_db=None,
                          with_graphics=False, target_lang=lang)


def test_translate_idml_mirrors_an_undirected_frame_in_hebrew(tmp_path, offline):
    """Reflected about its page's axis, measured from the page itself."""
    report = _translate(tmp_path, "he")
    assert report["rtl_text_direction_set"] > 0

    src_spread = _spread_of(str(tmp_path / "in.idml"))
    src = rtl.item_bounds(src_spread.find(".//*[@Self='plain']"))
    out = rtl.item_bounds(_spread_of(report["output"]).find(".//*[@Self='plain']"))
    (px0, px1), = [e for e in rtl.page_extents(src_spread) if e[0] <= src[0] <= e[1]]
    assert out[0] == pytest.approx(px0 + px1 - src[2])
    assert out[2] == pytest.approx(px0 + px1 - src[0])
    assert (out[1], out[3]) == pytest.approx((src[1], src[3]))


def test_translate_idml_mirrors_an_undirected_frame_for_arabic(tmp_path, offline):
    """The pipeline's Arabic output moves `plain`: no rule in `idml.rtl_rules`
    recognises it, and Arabic on this calibrated family is the one case
    where an unrecognised object mirrors instead of staying put."""
    report = _translate(tmp_path, "ar")
    src_box = rtl.item_bounds(
        _spread_of(str(tmp_path / "in.idml")).find(".//*[@Self='plain']"))
    out_box = rtl.item_bounds(_spread_of(report["output"]).find(".//*[@Self='plain']"))
    assert out_box != src_box
    # A reflection preserves size; only which side of the page it's on changes.
    assert out_box[2] - out_box[0] == pytest.approx(src_box[2] - src_box[0])
    assert out_box[3] - out_box[1] == pytest.approx(src_box[3] - src_box[1])


def test_hebrew_output_changes_nothing_but_horizontal_position(tmp_path, offline):
    report = _translate(tmp_path, "he")
    src = _spread_of(str(tmp_path / "in.idml"))
    out = _spread_of(report["output"])

    for el in src:
        if not rtl._is_page_item(el):
            continue
        self_id = el.get("Self")
        before = rtl.parse_transform(el.get("ItemTransform"))
        after = rtl.parse_transform(
            out.find(".//*[@Self='%s']" % self_id).get("ItemTransform"))
        assert after[:4] == before[:4] and after[5] == before[5], self_id


def test_arabic_output_never_touches_a_b_c_d_even_when_position_changes(tmp_path, offline):
    """`RTL_REPOSITION` reflects `tx`; `a b c d` -- rotation and scale -- are
    never touched, whether or not the object also moved."""
    report = _translate(tmp_path, "ar")
    src, out = _spread_of(str(tmp_path / "in.idml")), _spread_of(report["output"])
    for el in src:
        if not rtl._is_page_item(el):
            continue
        self_id = el.get("Self")
        before = rtl.parse_transform(el.get("ItemTransform"))
        after = rtl.parse_transform(out.find(".//*[@Self='%s']" % self_id).get("ItemTransform"))
        assert after[:4] == before[:4], "%s: a/b/c/d changed" % self_id


def test_hebrew_output_mirrors_a_group_the_same_way_as_arabic(tmp_path, offline):
    report = _translate(tmp_path, "he")
    out = _spread_of(report["output"])
    assert _bounds(out, "kid1")[0] > _bounds(out, "kid2")[0]


def test_arabic_output_mirrors_an_undirected_group_inside_and_out(tmp_path, offline):
    """A group's children land exactly where reflecting each one about the
    page axis puts it: the group crosses the page and its children swap
    sides within it. Each child keeps its own size and `a b c d`."""
    report = _translate(tmp_path, "ar")
    src, out = _spread_of(str(tmp_path / "in.idml")), _spread_of(report["output"])

    assert _bounds(src, "kid1")[0] < _bounds(src, "kid2")[0]
    assert _bounds(out, "kid1")[0] > _bounds(out, "kid2")[0]
    def on_page(spread, kid):
        grp = spread.find(".//*[@Self='grp']")
        return rtl.item_bounds(spread.find(".//*[@Self='%s']" % kid),
                               rtl.parse_transform(grp.get("ItemTransform")))

    pages = rtl.page_extents(src)
    for kid in ("kid1", "kid2"):
        before, after = on_page(src, kid), on_page(out, kid)
        (px0, px1), = [e for e in pages if e[0] <= before[0] <= e[1]]
        assert after[0] == pytest.approx(px0 + px1 - before[2]), kid
        assert after[2] == pytest.approx(px0 + px1 - before[0]), kid
        assert (rtl.parse_transform(out.find(".//*[@Self='%s']" % kid).get("ItemTransform"))[:4]
                == rtl.parse_transform(src.find(".//*[@Self='%s']" % kid).get("ItemTransform"))[:4])


def test_arabic_output_turns_text_direction_without_rebinding_pages(tmp_path, offline):
    """Story direction turns right-to-left; `PageBinding` -- which page
    renders on which side of a spread -- does not move."""
    import zipfile

    report = _translate(tmp_path, "ar")
    with zipfile.ZipFile(report["output"]) as z:
        prefs = etree.fromstring(z.read("Resources/Preferences.xml"))
        story = etree.fromstring(z.read("Stories/Story_u10.xml"))
    assert prefs.find(".//DocumentPreference").get("PageBinding") == "LeftToRight"
    assert story.find(".//StoryPreference").get(
        "StoryDirection") == "RightToLeftDirection"


def test_translate_idml_leaves_the_layout_alone_for_spanish(tmp_path, offline):
    """The LTR path must be untouched by all of this."""
    import zipfile

    report = _translate(tmp_path, "es")
    assert "rtl_text_direction_set" not in report

    src, out = _spread_of(str(tmp_path / "in.idml")), _spread_of(report["output"])
    for el in src:
        if not rtl._is_page_item(el):
            continue
        assert (out.find(".//*[@Self='%s']" % el.get("Self")).get("ItemTransform")
                == el.get("ItemTransform"))

    with zipfile.ZipFile(report["output"]) as z:
        prefs = etree.fromstring(z.read("Resources/Preferences.xml"))
        story = etree.fromstring(z.read("Stories/Story_u10.xml"))
    assert prefs.find(".//DocumentPreference").get("PageBinding") == "LeftToRight"
    assert story.find(".//StoryPreference").get(
        "StoryDirection") == "LeftToRightDirection"
    assert story.find(".//ParagraphStyleRange").get("Justification") == "LeftAlign"


def test_arabic_output_is_a_valid_idml_package(tmp_path, offline):
    import zipfile

    report = _translate(tmp_path, "ar")
    with zipfile.ZipFile(report["output"]) as z:
        assert z.testzip() is None
        names = z.namelist()
        assert names[0] == "mimetype"
        assert z.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        for name in names:
            if name.endswith(".xml"):
                etree.fromstring(z.read(name))


# ---- content axis ------------------------------------------------------------


def test_a_page_with_no_side_furniture_mirrors_about_its_own_centre():
    pages = [(0.0, -391.5, 612.0, 391.5)]
    assert rtl.content_axes(pages, []) == [306.0]


def test_a_fixed_strip_down_one_side_narrows_the_content_area():
    """Content mirrors within what the strip leaves free, so its clearance
    from the strip becomes its clearance from the opposite edge."""
    pages = [(0.0, -391.5, 612.0, 391.5)]
    strip = (500.0, -405.0, 625.0, 405.0)
    (axis,) = rtl.content_axes(pages, [strip])
    assert axis == pytest.approx(250.0)
    # The same strip on the left edge moves the axis the other way.
    left = (-13.0, -405.0, 112.0, 405.0)
    (axis_left,) = rtl.content_axes(pages, [left])
    assert axis_left == pytest.approx(362.0)


def test_furniture_that_does_not_run_down_the_page_leaves_the_axis_alone():
    pages = [(0.0, -391.5, 612.0, 391.5)]
    corner_badge = (500.0, -350.0, 612.0, -250.0)
    assert rtl.content_axes(pages, [corner_badge]) == [306.0]


def test_a_background_spanning_the_page_still_mirrors_about_the_page_centre():
    """Reflected about a narrowed axis it would shift and bare one edge."""
    extents = [(0.0, 612.0)]
    axes = [250.0]
    assert rtl.mirror_axis_for((-9.0, 0, 621.0, 10), extents, 306.0, axes) == 306.0
    assert rtl.mirror_axis_for((54.0, 0, 486.0, 10), extents, 306.0, axes) == 250.0


def test_a_picture_inside_its_frame_moves_exactly_once(tmp_path):
    """The frame mirrors; the picture inside rides with it. A move of the
    picture's own on top would slide it inside the frame and crop it."""
    from pagebirdy.idml import rtl_plan

    items = """
    <Rectangle Self="frame" ItemTransform="1 0 0 1 0 0">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="400 0"/><PathPointType Anchor="400 100"/>
        <PathPointType Anchor="580 100"/><PathPointType Anchor="580 0"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
      <Image Self="pic" ItemTransform="1 0 0 1 390 -10">
        <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
          <PathPointType Anchor="0 0"/><PathPointType Anchor="0 120"/>
          <PathPointType Anchor="200 120"/><PathPointType Anchor="200 0"/>
        </PathPointArray></GeometryPathType></PathGeometry></Properties>
      </Image>
    </Rectangle>"""
    docs = {"Spreads/S.xml": etree.fromstring(SINGLE.format(items=items).encode())}
    spread = docs["Spreads/S.xml"].find("Spread")
    pic_before = _item(spread, "pic").get("ItemTransform")

    plan = rtl_plan.build_plan(docs, document="d", language="ar")
    assert plan.by_object()["pic"].rule == "nested.carried"
    rtl.apply_plan(docs, plan)

    assert _bounds(spread, "frame") == pytest.approx((32.0, 0.0, 212.0, 100.0))
    assert _item(spread, "pic").get("ItemTransform") == pic_before
