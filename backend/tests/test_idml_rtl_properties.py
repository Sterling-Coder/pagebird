"""Mirror-sensitive properties beyond position and direction.

`test_idml_rtl.py` covers the geometric mirror contract and the two direction
switches. Everything here is a property whose *meaning* is tied to a side of
the page: flipping the binding without flipping these leaves the page half
mirrored — bullets hanging off the wrong edge, a wrap contour repelling text
the old way, an inline icon stranded on its former side.
"""

from lxml import etree

from pagebirdy.idml import rtl, rtl_legacy

# ---- typography -------------------------------------------------------------

RICH_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <StoryPreference StoryDirection="LeftToRightDirection"/>
    <ParagraphStyleRange Self="pJustL" Justification="LeftJustified"/>
    <ParagraphStyleRange Self="pJustR" Justification="RightJustified"/>
    <ParagraphStyleRange Self="pFull" Justification="FullyJustified"/>
    <ParagraphStyleRange Self="pBind" Justification="AwayFromBindingSide"/>
    <ParagraphStyleRange Self="pHang" LeftIndent="24" RightIndent="6" FirstLineIndent="-12"/>
    <ParagraphStyleRange Self="pPara" Composer="HL Composer"/>
    <ParagraphStyleRange Self="pSingle" Composer="HL Single"/>
    <ParagraphStyleRange Self="pReady" Composer="HL Composer Optyca"/>
    <ParagraphStyleRange Self="pPlain"/>
  </Story>
</idPkg:Story>
"""


def _story():
    return etree.fromstring(RICH_STORY.encode())


def _para(story, self_id):
    return story.find(".//ParagraphStyleRange[@Self='%s']" % self_id)


def _run(story):
    rtl.set_text_direction({"Stories/S.xml": story})
    return story


def test_justified_alignment_flips_like_plain_alignment():
    """`LeftJustified` is justified with the last line left: absolute, so it
    mirrors exactly as `LeftAlign` does."""
    story = _run(_story())
    assert _para(story, "pJustL").get("Justification") == "RightJustified"
    assert _para(story, "pJustR").get("Justification") == "LeftJustified"


def test_fully_justified_is_left_alone():
    """Both edges are flush, so no side is named and a mirror changes nothing."""
    story = _run(_story())
    assert _para(story, "pFull").get("Justification") == "FullyJustified"


def test_binding_relative_alignment_is_still_left_alone():
    story = _run(_story())
    assert _para(story, "pBind").get("Justification") == "AwayFromBindingSide"


def test_left_and_right_indent_swap():
    """A bullet's hanging indent measured from the left has to be measured
    from the right, or the bullet and its text stop lining up."""
    story = _run(_story())
    para = _para(story, "pHang")
    assert para.get("LeftIndent") == "6"
    assert para.get("RightIndent") == "24"


def test_first_line_indent_is_not_negated():
    """`FirstLineIndent` is measured from the paragraph's *leading* edge, which
    `ParagraphDirection` has already moved. Flipping it too would mirror it
    twice and turn a hanging indent back into a first-line indent."""
    story = _run(_story())
    assert _para(story, "pHang").get("FirstLineIndent") == "-12"


def test_composer_becomes_world_ready():
    """Arabic shaping and bidi reordering happen only under the World-Ready
    composer; the Latin one sets the run in logical order, which renders as
    shaped-but-reversed text."""
    story = _run(_story())
    assert _para(story, "pPara").get("Composer") == "HL Composer Optyca"
    assert _para(story, "pSingle").get("Composer") == "HL Single Optyca"


def test_a_world_ready_composer_is_left_as_it_is():
    story = _run(_story())
    assert _para(story, "pReady").get("Composer") == "HL Composer Optyca"


def test_a_paragraph_with_no_composer_is_given_the_world_ready_one():
    """Most paragraphs inherit their composer, so silence is how a run reaches
    InDesign with the Latin composer still in force."""
    story = _run(_story())
    assert _para(story, "pPlain").get("Composer") == "HL Composer Optyca"


def test_digits_are_declared_western_explicitly():
    """Both human Arabic references set Western digits throughout — 99 of them,
    no Arabic-Indic. Leaving the attribute unwritten lets another machine's
    default flip the arithmetic to a different numeral set."""
    story = _run(_story())
    assert _para(story, "pPlain").get("DigitsType") == "DefaultDigits"


TABLE_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u11">
    <Table Self="t1" TableDirection="LeftToRightDirection" ColumnCount="2"/>
  </Story>
</idPkg:Story>
"""


def test_table_direction_flips_so_columns_reverse():
    """The reference reverses every table's column order: `Ball` sits to the
    right of `How Many`, not its left."""
    story = etree.fromstring(TABLE_STORY.encode())
    rtl.set_text_direction({"Stories/S.xml": story})
    assert story.find(".//Table").get("TableDirection") == "RightToLeftDirection"


# ---- item properties --------------------------------------------------------

WRAP_SPREAD = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"/>
    <Rectangle Self="rL" ItemTransform="1 0 0 1 0 0">
      <TextWrapPreference TextWrapSide="LeftSide" TextWrapMode="BoundingBoxTextWrap">
        <Properties><TextWrapOffset Top="1" Left="12" Bottom="3" Right="4"/></Properties>
      </TextWrapPreference>
    </Rectangle>
    <Rectangle Self="rBoth" ItemTransform="1 0 0 1 0 0">
      <TextWrapPreference TextWrapSide="BothSides" TextWrapMode="BoundingBoxTextWrap"/>
    </Rectangle>
    <Rectangle Self="rSpine" ItemTransform="1 0 0 1 0 0">
      <TextWrapPreference TextWrapSide="SideTowardsSpine" TextWrapMode="BoundingBoxTextWrap"/>
    </Rectangle>
    <TextFrame Self="tf" ItemTransform="1 0 0 1 0 0">
      <TextFramePreference>
        <Properties><InsetSpacing type="list">
          <ListItem type="unit">1</ListItem><ListItem type="unit">10</ListItem>
          <ListItem type="unit">3</ListItem><ListItem type="unit">4</ListItem>
        </InsetSpacing></Properties>
      </TextFramePreference>
    </TextFrame>
    <TextFrame Self="tfUniform" ItemTransform="1 0 0 1 0 0">
      <TextFramePreference>
        <Properties><InsetSpacing type="unit">9</InsetSpacing></Properties>
      </TextFramePreference>
    </TextFrame>
  </Spread>
</idPkg:Spread>
"""


def _wrap():
    tree = etree.fromstring(WRAP_SPREAD.encode())
    rtl.mirror_item_properties({"Spreads/S.xml": tree})
    return tree


def _by_self(tree, self_id):
    return tree.find(".//*[@Self='%s']" % self_id)


def test_text_wrap_side_flips_when_it_names_a_side():
    wrap = _by_self(_wrap(), "rL").find("TextWrapPreference")
    assert wrap.get("TextWrapSide") == "RightSide"


def test_both_sides_wrap_is_left_alone():
    """`BothSides` is symmetric: there is no side to move it to."""
    wrap = _by_self(_wrap(), "rBoth").find("TextWrapPreference")
    assert wrap.get("TextWrapSide") == "BothSides"


def test_binding_relative_wrap_is_left_alone():
    """`SideTowardsSpine` resolves against `PageBinding`, exactly as
    `AwayFromBindingSide` does, so touching it mirrors that wrap twice."""
    wrap = _by_self(_wrap(), "rSpine").find("TextWrapPreference")
    assert wrap.get("TextWrapSide") == "SideTowardsSpine"


def test_text_wrap_offset_swaps_left_and_right():
    off = _by_self(_wrap(), "rL").find(".//TextWrapOffset")
    assert (off.get("Left"), off.get("Right")) == ("4", "12")


def test_text_wrap_offset_leaves_the_vertical_pair_alone():
    off = _by_self(_wrap(), "rL").find(".//TextWrapOffset")
    assert (off.get("Top"), off.get("Bottom")) == ("1", "3")


def test_inset_spacing_list_swaps_left_and_right():
    """A four-item `InsetSpacing` is `top left bottom right`."""
    items = _by_self(_wrap(), "tf").findall(".//InsetSpacing/ListItem")
    assert [i.text for i in items] == ["1", "4", "3", "10"]


def test_a_uniform_inset_is_left_alone():
    """A scalar inset already applies to all four sides."""
    inset = _by_self(_wrap(), "tfUniform").find(".//InsetSpacing")
    assert inset.text == "9"


ANCHOR_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u12">
    <AnchoredObjectSetting Self="aX" AnchorXoffset="12" AnchorYoffset="-3"
                           HorizontalAlignment="LeftAlign"/>
    <AnchoredObjectSetting Self="aY" AnchorYoffset="-0.2"/>
  </Story>
</idPkg:Story>
"""


def _anchors():
    tree = etree.fromstring(ANCHOR_STORY.encode())
    rtl.mirror_item_properties({"Stories/S.xml": tree})
    return tree


def test_a_side_aligned_x_offset_keeps_its_sign():
    """A side-aligned offset is measured outward from that side (calibrated in
    InDesign 2026), so flipping the side mirrors it; negating it as well would
    move the object to the other side of the edge."""
    assert _by_self(_anchors(), "aX").get("AnchorXoffset") == "12"


def test_a_centre_aligned_x_offset_is_negated():
    """Measured rightwards from the centre, it has to point left instead."""
    tree = etree.fromstring(b'<Story><AnchoredObjectSetting Self="c" AnchorXoffset="5" '
                            b'HorizontalAlignment="CenterAlign"/></Story>')
    rtl.mirror_item_properties({"Stories/S.xml": tree})
    assert _by_self(tree, "c").get("AnchorXoffset") == "-5"


def test_anchored_object_horizontal_alignment_flips():
    assert _by_self(_anchors(), "aX").get("HorizontalAlignment") == "RightAlign"


def test_anchored_object_vertical_offset_is_untouched():
    tree = _anchors()
    assert _by_self(tree, "aX").get("AnchorYoffset") == "-3"
    assert _by_self(tree, "aY").get("AnchorYoffset") == "-0.2"


def test_an_anchor_without_a_horizontal_offset_is_not_given_one():
    """Writing a default where the source was silent changes layout InDesign
    was resolving for itself."""
    assert _by_self(_anchors(), "aY").get("AnchorXoffset") is None


# ---- font registration ------------------------------------------------------

FONTS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Fonts xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <FontFamily Self="di39" Name="Minion Pro">
    <Font Self="di39FontnMinion Pro Regular" FontFamily="Minion Pro" Name="Minion Pro Regular"
          PostScriptName="MinionPro-Regular" Status="Installed" FontStyleName="Regular"/>
  </FontFamily>
</idPkg:Fonts>
"""


def _fonts():
    return etree.fromstring(FONTS.encode())


def test_target_font_family_is_registered():
    """An `AppliedFont` naming a family the package never declares is how the
    output opens in InDesign with a missing-font warning and a substituted
    face — which is what emptied the number-bond labels."""
    tree = _fonts()
    rtl.register_font(tree, "Noto Sans Arabic")
    assert "Noto Sans Arabic" in [f.get("Name") for f in tree.iter("FontFamily")]


def test_registering_a_family_twice_adds_it_once():
    tree = _fonts()
    rtl.register_font(tree, "Noto Sans Arabic")
    rtl.register_font(tree, "Noto Sans Arabic")
    names = [f.get("Name") for f in tree.iter("FontFamily")]
    assert names.count("Noto Sans Arabic") == 1


def test_registering_a_family_the_package_already_has_changes_nothing():
    tree = _fonts()
    before = etree.tostring(tree)
    rtl.register_font(tree, "Minion Pro")
    assert etree.tostring(tree) == before


def test_registered_family_carries_a_usable_face():
    """A `FontFamily` with no `Font` child is not a family InDesign can apply."""
    tree = _fonts()
    rtl.register_font(tree, "Noto Sans Arabic")
    fam = [f for f in tree.iter("FontFamily") if f.get("Name") == "Noto Sans Arabic"][0]
    faces = fam.findall("Font")
    assert faces and faces[0].get("FontFamily") == "Noto Sans Arabic"


def test_registering_nothing_is_a_no_op():
    """An LTR target has no `idml_font`; the entry must not be rewritten."""
    tree = _fonts()
    before = etree.tostring(tree)
    rtl.register_font(tree, None)
    assert etree.tostring(tree) == before


# ---- the document default ---------------------------------------------------
# `TextDefault` is what every paragraph that overrides nothing inherits from.
# Left Latin and left-aligned, it re-imposes both on the majority of the
# document however many paragraph styles were flipped.

DEFAULT_PREFS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Preferences xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <DocumentPreference PageBinding="LeftToRight" FacingPages="true"/>
  <StoryPreference StoryDirection="LeftToRightDirection"/>
  <TextDefault Composer="HL Single" Justification="LeftAlign"
               LeftIndent="18" RightIndent="0"/>
</idPkg:Preferences>
"""


def _defaults():
    prefs = etree.fromstring(DEFAULT_PREFS.encode())
    rtl.set_text_direction({}, prefs)
    return prefs.find(".//TextDefault")


def test_the_document_default_moves_to_the_world_ready_composer():
    assert _defaults().get("Composer") == "HL Single Optyca"


def test_the_document_default_alignment_flips():
    assert _defaults().get("Justification") == "RightAlign"


def test_the_document_default_indents_swap():
    default = _defaults()
    assert (default.get("LeftIndent"), default.get("RightIndent")) == ("0", "18")


def test_the_document_default_runs_right_to_left():
    assert _defaults().get("ParagraphDirection") == "RightToLeftDirection"


def test_the_document_default_declares_its_digits():
    assert _defaults().get("DigitsType") == "DefaultDigits"


# ---- paragraph rules --------------------------------------------------------
# A rule under a heading is indented to start clear of the badge beside it.
# The indent names an edge, so it mirrors with the text; left alone it keeps
# measuring from the old edge and the rule runs straight through the badge.

RULE_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u13">
    <ParagraphStyleRange Self="pBelow" RuleBelowLeftIndent="169"/>
    <ParagraphStyleRange Self="pAbove" RuleAboveLeftIndent="-9" RuleAboveRightIndent="-13"/>
    <ParagraphStyleRange Self="pNone"/>
  </Story>
</idPkg:Story>
"""


def _rules():
    story = etree.fromstring(RULE_STORY.encode())
    rtl.set_text_direction({"Stories/S.xml": story})
    return story


def test_a_one_sided_rule_indent_moves_to_the_other_edge():
    """`LH Investigate` indents its rule 169pt from the left so it starts clear
    of the badge. After the flip the badge is on the right, so the indent has
    to be too."""
    para = _rules().find(".//ParagraphStyleRange[@Self='pBelow']")
    assert para.get("RuleBelowRightIndent") == "169"
    assert para.get("RuleBelowLeftIndent") is None


def test_rule_above_indents_swap_as_a_pair():
    para = _rules().find(".//ParagraphStyleRange[@Self='pAbove']")
    assert para.get("RuleAboveLeftIndent") == "-13"
    assert para.get("RuleAboveRightIndent") == "-9"


def test_a_paragraph_with_no_rule_indent_is_not_given_one():
    para = _rules().find(".//ParagraphStyleRange[@Self='pNone']")
    assert para.get("RuleBelowLeftIndent") is None
    assert para.get("RuleBelowRightIndent") is None


# ---- decorative path geometry -----------------------------------------------
# Moving `tx` reflects an item's *position*; it never reflects the item's own
# shape, because negating the matrix would flip photographs and text with it.
# An asymmetric decorative curve -- the dotted swoosh pointing at the SAY
# callout -- therefore lands on the far side of the page still curving the way
# it always did, and its tip no longer meets the thing it points at.

def _path(points, tag="Polygon", transform="1 0 0 1 0 0", extra="", attrs=""):
    body = "".join(
        '<PathPointType Anchor="%s %s" LeftDirection="%s %s" RightDirection="%s %s"/>'
        % (ax, ay, lx, ly, rx, ry)
        for (ax, ay, lx, ly, rx, ry) in points
    )
    return etree.fromstring(
        ('<%s Self="p1" ItemTransform="%s" %s>'
         '<Properties><PathGeometry><GeometryPathType PathOpen="true">'
         '<PathPointArray>%s</PathPointArray>'
         '</GeometryPathType></PathGeometry></Properties>%s</%s>'
         % (tag, transform, attrs, body, extra, tag)).encode()
    )


# An asymmetric open curve: anchors at x=0, 10 and 40, so its tip is far from
# its tail and a reflection is visible in the anchor order.
SWOOSH = [
    (0, 0, 0, 0, 0, 0),
    (10, 5, 8, 4, 12, 6),
    (40, 0, 35, 2, 40, 0),
]


def test_a_decorative_path_reflects_its_own_geometry():
    el = _path(SWOOSH)
    assert rtl.reflect_path(el) is True
    xs = [float(p.get("Anchor").split()[0])
          for p in el.iter("PathPointType")]
    # reflected about the anchor centre (20): 0->40, 10->30, 40->0
    assert xs == [40.0, 30.0, 0.0]


def test_reflecting_a_path_leaves_its_bounds_where_they_were():
    """The tx mirror is computed from these bounds, so the shape flip must not
    move them or the item lands somewhere else entirely."""
    el = _path(SWOOSH)
    before = rtl.item_bounds(el)
    rtl.reflect_path(el)
    assert rtl.item_bounds(el) == before


def test_reflecting_a_path_leaves_the_vertical_alone():
    el = _path(SWOOSH)
    rtl.reflect_path(el)
    ys = [float(p.get("Anchor").split()[1]) for p in el.iter("PathPointType")]
    assert ys == [0.0, 5.0, 0.0]


def test_reflecting_a_path_keeps_each_handle_in_its_own_role():
    """`LeftDirection`/`RightDirection` name a point's incoming and outgoing
    tangent -- path order, not screen position. A reflection maps a curve's
    control points and leaves those roles alone; exchanging them is what
    *reversing* a path does, and doing it here swaps each point's in and out
    tangent lengths. That is what turned the dotted spiral into an arbitrary
    shape: every point kinked, because a short lead-in became a long one."""
    el = _path(SWOOSH)
    rtl.reflect_path(el)
    mid = list(el.iter("PathPointType"))[1]
    # about the anchor centre 20: Left 8 -> 32, Right 12 -> 28, roles unchanged
    assert mid.get("LeftDirection").split()[0] == "32"
    assert mid.get("RightDirection").split()[0] == "28"


def test_reflecting_a_path_preserves_each_tangent_length():
    """The invariant behind the case above: a reflection is an isometry, so
    the distance from a point to each of its handles cannot change."""
    el = _path(SWOOSH)
    before = [(abs(float(p.get("Anchor").split()[0]) - float(p.get("LeftDirection").split()[0])),
               abs(float(p.get("Anchor").split()[0]) - float(p.get("RightDirection").split()[0])))
              for p in el.iter("PathPointType")]
    rtl.reflect_path(el)
    after = [(abs(float(p.get("Anchor").split()[0]) - float(p.get("LeftDirection").split()[0])),
              abs(float(p.get("Anchor").split()[0]) - float(p.get("RightDirection").split()[0])))
             for p in el.iter("PathPointType")]
    assert after == before


def test_reflecting_a_path_twice_is_the_identity():
    el = _path(SWOOSH)
    before = etree.tostring(el)
    rtl.reflect_path(el)
    rtl.reflect_path(el)
    assert etree.tostring(el) == before


def test_a_text_frame_is_never_reflected():
    """Reflecting a frame's path would mirror the text set inside it."""
    el = _path(SWOOSH, tag="TextFrame", attrs='ParentStory="u1"')
    assert rtl.reflect_path(el) is False


def test_a_frame_holding_a_placed_graphic_is_never_reflected():
    """The `scaleX(-1)` trap: a mirrored photograph or logo reads as a fake."""
    el = _path(SWOOSH, tag="Rectangle",
               extra='<Image Self="i1"><Link LinkResourceURI="file:/a.ai"/></Image>')
    assert rtl.reflect_path(el) is False


def test_a_frame_holding_inline_text_is_never_reflected():
    el = _path(SWOOSH, tag="Rectangle",
               extra='<CharacterStyleRange><Content>SAY</Content></CharacterStyleRange>')
    assert rtl.reflect_path(el) is False


def test_a_rotated_decorative_path_is_left_alone():
    """Reflecting local x is only a true mirror while the item's own axes are
    still parallel to the page's. Under rotation or shear it is not, and
    guessing would distort the artwork rather than mirror it."""
    el = _path(SWOOSH, transform="0 1 -1 0 0 0")
    assert rtl.reflect_path(el) is False


def test_a_group_is_not_reflected_as_a_path():
    """Groups already mirror as one unit; their children are reached on their
    own terms."""
    el = _path(SWOOSH, tag="Group")
    assert rtl.reflect_path(el) is False


def test_mirroring_a_spread_reflects_its_decorative_paths():
    """End to end: the swoosh flips shape *and* moves side, so it still points
    at what it pointed at."""
    spread = etree.fromstring(
        ('<Spread Self="s" ItemTransform="1 0 0 1 0 0">'
         '<Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 0"/>'
         '<Polygon Self="p1x" ItemTransform="1 0 0 1 0 0">'
         '<Properties><PathGeometry><GeometryPathType PathOpen="true"><PathPointArray>'
         '<PathPointType Anchor="0 0" LeftDirection="0 0" RightDirection="0 0"/>'
         '<PathPointType Anchor="40 0" LeftDirection="35 2" RightDirection="40 0"/>'
         '</PathPointArray></GeometryPathType></PathGeometry></Properties>'
         '</Polygon></Spread>').encode()
    )
    rtl_legacy.mirror_spread(spread)
    poly = spread.find(".//Polygon")
    # bounds mirror about the page centre 306: 0..40 -> 572..612
    assert rtl.item_bounds(poly) == (572.0, 0.0, 612.0, 0.0)
    # and the handle that trailed the far anchor now leads it
    far = list(poly.iter("PathPointType"))[0]
    assert far.get("Anchor").split()[0] == "40"


# ---- placed photographs -----------------------------------------------------
# The mirror moves a frame and leaves its content alone -- except for a placed
# photograph, which the human-translated Arabic references turn round with the
# page. The sprinters on the Lesson 12 family letter run rightwards in English
# and leftwards in Arabic; the coordinate planes two pages later keep x running
# rightwards in both.

# An asymmetric silhouette: the frame is cut round a subject leaning one way,
# so a reflection is visible in the anchor order and in the wrap contour.
SILHOUETTE = [(0, 0), (10, 40), (60, 40), (100, 0)]


def _picture(content="Image", link="file:/runners.psd", wrap=True,
             transform="1 0 0 1 0 0", child="1 0 0 1 20 0", extra="",
             tag="Polygon", fitting=""):
    """A clipped picture as InDesign writes one: silhouette, contour, content."""
    def path(points):
        return ('<PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>'
                + "".join('<PathPointType Anchor="%s %s" LeftDirection="%s %s" '
                          'RightDirection="%s %s"/>' % (x, y, x, y, x, y)
                          for x, y in points)
                + "</PathPointArray></GeometryPathType></PathGeometry>")

    contour = ('<TextWrapPreference TextWrapSide="BothSides" TextWrapMode="Contour">'
               "<Properties>" + path(SILHOUETTE) + "</Properties>"
               "</TextWrapPreference>") if wrap else ""
    inner = ('<Rectangle Self="pic" ItemTransform="%s">'
             '<%s Self="img"><Link LinkResourceURI="%s"/></%s>'
             "</Rectangle>" % (child, content, link, content)) if content else ""
    return etree.fromstring(
        ('<%s Self="frame" ItemTransform="%s"><Properties>%s</Properties>'
         "%s%s%s%s</%s>"
         % (tag, transform, path(SILHOUETTE), contour, fitting, inner, extra, tag)
         ).encode())


def _path_xs(el, path="./Properties/PathGeometry"):
    return [float(p.get("Anchor").split()[0])
            for p in el.find(path).iter("PathPointType")]


def test_a_placed_photograph_is_turned_round():
    """The reference flips the picture; leaving it alone faces the subject off
    the page it was composed to look into."""
    el = _picture()
    assert rtl.reflect_graphic(el) is True
    # reflected about the silhouette's own centre (50): 0->100, 10->90, ...
    assert _path_xs(el) == [100.0, 90.0, 40.0, 0.0]


def test_turning_a_photograph_round_reflects_its_wrap_contour():
    """The measure available to the text beside it comes from the contour, not
    the frame. A silhouette cut for a subject facing the other way takes the
    wrong bite out of every line -- and with `BothSides` it opens a gap in the
    middle of the column, so the tail of a heading prints on the far side of
    the picture."""
    el = _picture()
    rtl.reflect_graphic(el)
    assert _path_xs(el, "./TextWrapPreference/Properties/PathGeometry") == \
        [100.0, 90.0, 40.0, 0.0]


def test_turning_a_photograph_round_leaves_the_frames_own_matrix_alone():
    """The `tx` mirror is computed from these bounds and `a b c d` carry the
    frame's size and rotation. Only what the frame *contains* turns round."""
    el = _picture()
    before = rtl.item_bounds(el)
    rtl.reflect_graphic(el)
    assert rtl.parse_transform(el.get("ItemTransform")) == rtl.IDENTITY
    assert rtl.item_bounds(el) == before


def test_the_picture_inside_the_frame_is_turned_round_with_it():
    """The silhouette and the picture must move about the same axis or the
    subject slides out from under its own outline."""
    el = _picture()
    rtl.reflect_graphic(el)
    pic = el.find(".//Rectangle[@Self='pic']")
    # The child sat 20 in from the frame's origin; mirrored about 50 it is
    # drawn backwards from 80.
    assert rtl.parse_transform(pic.get("ItemTransform")) == \
        (-1.0, 0.0, 0.0, 1.0, 80.0, 0.0)


def test_turning_a_photograph_round_twice_is_the_identity():
    el = _picture()
    before = etree.tostring(el)
    rtl.reflect_graphic(el)
    rtl.reflect_graphic(el)
    assert etree.tostring(el) == before


def test_placed_vector_art_is_never_turned_round():
    """A coordinate plane's x-axis and a badge's glyph mean what they mean one
    way round only, and the references leave both exactly as drawn."""
    el = _picture(content="PDF", link="file:/graph.ai")
    assert rtl.reflect_graphic(el) is False
    assert _path_xs(el) == [0.0, 10.0, 60.0, 100.0]


def test_a_frame_mixing_a_photograph_with_vector_art_is_left_alone():
    """Half the frame would come out backwards; the mirror does not guess."""
    el = _picture(extra='<Rectangle Self="v" ItemTransform="1 0 0 1 0 0">'
                        '<PDF Self="p"><Link LinkResourceURI="file:/x.ai"/></PDF>'
                        "</Rectangle>")
    assert rtl.reflect_graphic(el) is False


def test_a_frame_setting_type_is_never_turned_round():
    el = _picture(extra="<CharacterStyleRange><Content>SAY</Content>"
                        "</CharacterStyleRange>")
    assert rtl.reflect_graphic(el) is False


def test_a_rotated_photograph_is_left_alone():
    """Reflecting local x is a true mirror only while the frame's own axes are
    parallel to the page's."""
    assert rtl.reflect_graphic(_picture(transform="0 1 -1 0 0 0")) is False


def test_a_translated_graphic_is_left_upright():
    """The artwork stage burns the translation into the pixels. Turning that
    round prints the Arabic backwards -- the one thing mirroring a picture is
    meant to avoid."""
    el = _picture(link="file:/out/links_ar/figure.ar.png")
    assert rtl.reflect_graphic(
        el, keep_upright=("file:/out/links_ar/figure.ar.png",)) is False
    assert rtl.reflect_graphic(el, keep_upright=("file:/other.png",)) is True


def test_the_frame_fitting_crop_moves_with_the_picture():
    """The crop records how much of the picture each edge hides. The picture
    has swapped ends, so the two horizontal figures have too."""
    el = _picture(fitting='<FrameFittingOption AutoFit="true" LeftCrop="-6" '
                          'TopCrop="-12" RightCrop="1" BottomCrop="-9"/>')
    rtl.reflect_graphic(el)
    fitting = el.find("./FrameFittingOption")
    assert (fitting.get("LeftCrop"), fitting.get("RightCrop")) == ("1", "-6")
    assert (fitting.get("TopCrop"), fitting.get("BottomCrop")) == ("-12", "-9")


def _page_spread():
    return etree.fromstring(
        ('<Spread Self="s" ItemTransform="1 0 0 1 0 0">'
         '<Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 0"/>'
         "</Spread>").encode())


def test_only_the_outermost_frame_of_a_clipped_photograph_turns_round():
    """`Polygon > Rectangle > Image` is how a clipped photo arrives. Reflecting
    the inner frame on its own account as well would undo the outer one."""
    spread = _page_spread()
    spread.append(_picture())
    rtl_legacy.mirror_spread(spread)
    pic = spread.find(".//Rectangle[@Self='pic']")
    assert rtl.parse_transform(pic.get("ItemTransform"))[0] == -1.0


def test_mirroring_a_spread_turns_its_photographs_round():
    """End to end: the picture crosses the page *and* faces the other way."""
    spread = _page_spread()
    spread.append(_picture())
    flipped = []
    rtl_legacy.mirror_spread(spread, flipped=flipped)
    frame = spread.find(".//Polygon")
    # bounds mirror about the page centre 306: 0..100 -> 512..612
    assert rtl.item_bounds(frame)[0] == 512.0
    assert _path_xs(frame) == [100.0, 90.0, 40.0, 0.0]
    assert flipped == ["frame"]


def test_a_photograph_on_the_pasteboard_keeps_its_picture():
    """It never prints and never moves, so nothing about it may change."""
    spread = _page_spread()
    spread.append(_picture(transform="1 0 0 1 900 0"))
    before = etree.tostring(spread.find(".//Polygon"))
    rtl_legacy.mirror_spread(spread)
    assert etree.tostring(spread.find(".//Polygon")) == before


def test_a_decorative_paths_wrap_contour_reflects_with_its_outline():
    """Same fault, same fix, one item class over: an outline that flips and a
    contour that does not leaves the two disagreeing about where the item is."""
    el = _picture(content="", wrap=True)
    assert rtl.reflect_path(el) is True
    assert _path_xs(el, "./TextWrapPreference/Properties/PathGeometry") == \
        [100.0, 90.0, 40.0, 0.0]


# ---- anchor point and paragraph shading -------------------------------------
# `AnchorXoffset` and `HorizontalAlignment` say where the anchor sits; the
# anchor *point* says which corner of the object is put there. Flipping the
# first two and not the third pins the mirrored object by its old corner, which
# slides it sideways by its own width — a figure anchored top-left ends up a
# frame-width away from where the mirror put everything around it.

CORNER_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u14">
    <AnchoredObjectSetting Self="aTL" AnchoredPosition="Anchored" AnchorPoint="TopLeftAnchor"/>
    <AnchoredObjectSetting Self="aBR" AnchoredPosition="Anchored" AnchorPoint="BottomRightAnchor"/>
    <AnchoredObjectSetting Self="aLC" AnchoredPosition="Anchored" AnchorPoint="LeftCenterAnchor"/>
    <AnchoredObjectSetting Self="aTC" AnchoredPosition="Anchored" AnchorPoint="TopCenterAnchor"/>
    <AnchoredObjectSetting Self="aC" AnchoredPosition="Anchored" AnchorPoint="CenterAnchor"/>
    <AnchoredObjectSetting Self="aNone" AnchoredPosition="Anchored"/>
  </Story>
</idPkg:Story>
"""


def _corners():
    tree = etree.fromstring(CORNER_STORY.encode())
    rtl.mirror_item_properties({"Stories/S.xml": tree})
    return tree


def test_anchor_point_flips_to_the_mirrored_corner():
    tree = _corners()
    assert _by_self(tree, "aTL").get("AnchorPoint") == "TopRightAnchor"
    assert _by_self(tree, "aBR").get("AnchorPoint") == "BottomLeftAnchor"
    assert _by_self(tree, "aLC").get("AnchorPoint") == "RightCenterAnchor"


def test_an_anchor_point_naming_no_side_is_left_alone():
    """`TopCenterAnchor` and `CenterAnchor` sit on the vertical centre line, so
    a mirror about that line maps them to themselves."""
    tree = _corners()
    assert _by_self(tree, "aTC").get("AnchorPoint") == "TopCenterAnchor"
    assert _by_self(tree, "aC").get("AnchorPoint") == "CenterAnchor"


def test_an_anchor_without_a_point_is_not_given_one():
    assert _by_self(_corners(), "aNone").get("AnchorPoint") is None


SHADING_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u15">
    <ParagraphStyleRange Self="pShade" ParagraphShadingLeftOffset="18"
                         ParagraphShadingRightOffset="0"
                         ParagraphShadingTopLeftCornerOption="Rounded"
                         ParagraphShadingTopRightCornerOption="None"
                         ParagraphShadingTopLeftCornerRadius="6"
                         ParagraphShadingTopRightCornerRadius="1"/>
    <ParagraphStyleRange Self="pBorder" ParagraphBorderLeftOffset="12"
                         ParagraphBorderRightOffset="3"
                         ParagraphBorderLeftLineWeight="2"
                         ParagraphBorderRightLineWeight="0.5"/>
    <ParagraphStyleRange Self="pPlain"/>
  </Story>
</idPkg:Story>
"""


def _shading():
    story = etree.fromstring(SHADING_STORY.encode())
    rtl.set_text_direction({"Stories/S.xml": story})
    return story


def test_paragraph_shading_offsets_swap():
    """The shading box behind a callout is inset from one text edge. Left
    unswapped it keeps hugging the edge the text just left."""
    para = _shading().find(".//ParagraphStyleRange[@Self='pShade']")
    assert para.get("ParagraphShadingLeftOffset") == "0"
    assert para.get("ParagraphShadingRightOffset") == "18"


def test_paragraph_shading_corners_swap():
    para = _shading().find(".//ParagraphStyleRange[@Self='pShade']")
    assert para.get("ParagraphShadingTopLeftCornerOption") == "None"
    assert para.get("ParagraphShadingTopRightCornerOption") == "Rounded"
    assert para.get("ParagraphShadingTopLeftCornerRadius") == "1"
    assert para.get("ParagraphShadingTopRightCornerRadius") == "6"


def test_paragraph_border_offsets_and_weights_swap():
    para = _shading().find(".//ParagraphStyleRange[@Self='pBorder']")
    assert para.get("ParagraphBorderLeftOffset") == "3"
    assert para.get("ParagraphBorderRightOffset") == "12"
    assert para.get("ParagraphBorderLeftLineWeight") == "0.5"
    assert para.get("ParagraphBorderRightLineWeight") == "2"


def test_a_paragraph_with_no_shading_is_not_given_any():
    para = _shading().find(".//ParagraphStyleRange[@Self='pPlain']")
    assert para.get("ParagraphShadingLeftOffset") is None
    assert para.get("ParagraphBorderRightOffset") is None


# ---- object styles ----------------------------------------------------------
# The same reasoning that pulls `Resources/Styles.xml` into the text-direction
# pass applies to the item properties: most frames override nothing, so a wrap
# side, a frame inset or an anchor left pointing the old way in the object
# style quietly re-imposes itself on the bulk of the document however many
# frames were mirrored inline.

OBJECT_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <RootObjectStyleGroup Self="ros">
    <ObjectStyle Self="os1" Name="Callout">
      <TextWrapPreference TextWrapSide="LeftSide" TextWrapMode="BoundingBoxTextWrap">
        <TextWrapOffset Top="0" Left="18" Bottom="0" Right="0"/>
      </TextWrapPreference>
      <TextFramePreference>
        <Properties><InsetSpacing type="list">
          <ListItem type="unit">3</ListItem>
          <ListItem type="unit">18</ListItem>
          <ListItem type="unit">3</ListItem>
          <ListItem type="unit">0</ListItem>
        </InsetSpacing></Properties>
      </TextFramePreference>
      <AnchoredObjectSetting AnchoredPosition="Anchored" AnchorPoint="TopLeftAnchor"
                             HorizontalAlignment="LeftAlign" AnchorXoffset="9"/>
    </ObjectStyle>
  </RootObjectStyleGroup>
</idPkg:Styles>
"""

DOC_DEFAULT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Preferences xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <DocumentPreference PageBinding="LeftToRight"/>
  <AnchoredObjectDefault AnchorContent="Unassigned">
    <AnchoredObjectSetting AnchoredPosition="Anchored" AnchorPoint="BottomRightAnchor"
                           HorizontalAlignment="LeftAlign"/>
  </AnchoredObjectDefault>
</idPkg:Preferences>
"""


def _resources():
    styles = etree.fromstring(OBJECT_STYLES.encode())
    prefs = etree.fromstring(DOC_DEFAULT.encode())
    rtl.mirror_item_properties(
        {"Resources/Styles.xml": styles, "Resources/Preferences.xml": prefs}
    )
    return styles, prefs


def test_object_style_wrap_side_is_mirrored():
    styles, _ = _resources()
    assert styles.find(".//TextWrapPreference").get("TextWrapSide") == "RightSide"


def test_object_style_wrap_offset_is_mirrored():
    styles, _ = _resources()
    offset = styles.find(".//TextWrapOffset")
    assert offset.get("Left") == "0"
    assert offset.get("Right") == "18"


def test_object_style_frame_inset_is_mirrored():
    styles, _ = _resources()
    items = styles.find(".//InsetSpacing")
    assert [c.text for c in items] == ["3", "0", "3", "18"]


def test_object_style_anchor_is_mirrored():
    styles, _ = _resources()
    anchor = styles.find(".//AnchoredObjectSetting")
    assert anchor.get("HorizontalAlignment") == "RightAlign"
    assert anchor.get("AnchorPoint") == "TopRightAnchor"
    assert anchor.get("AnchorXoffset") == "9"


def test_the_document_anchored_object_default_is_mirrored():
    """What every anchored object that overrides nothing inherits."""
    _, prefs = _resources()
    anchor = prefs.find(".//AnchoredObjectSetting")
    assert anchor.get("HorizontalAlignment") == "RightAlign"
    assert anchor.get("AnchorPoint") == "BottomLeftAnchor"


# ---- directional bullets ----------------------------------------------------
# A direction line is set with a rightwards arrowhead pointing into the text.
# RTL moves the bullet to the other side of the line but cannot turn the glyph
# round, so the arrow ends up pointing away from the sentence it introduces.

BULLET_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <RootParagraphStyleGroup Self="rps">
    <ParagraphStyle Self="ParagraphStyle/Arrow" Name="Arrow">
      <Properties>
        <BulletChar BulletCharacterType="UnicodeOnly" BulletCharacterValue="8594"/>
      </Properties>
    </ParagraphStyle>
    <ParagraphStyle Self="ParagraphStyle/Dingbat" Name="Dingbat">
      <Properties>
        <BulletChar BulletCharacterType="UnicodeOnly" BulletCharacterValue="10148"/>
        <BulletsFont type="string">ITC Zapf Dingbats Std</BulletsFont>
        <BulletsFontStyle type="string">Medium</BulletsFontStyle>
        <BulletsCharacterStyle type="object">CharacterStyle/blue</BulletsCharacterStyle>
      </Properties>
    </ParagraphStyle>
    <ParagraphStyle Self="ParagraphStyle/Derived" Name="Derived">
      <Properties>
        <BasedOn type="object">ParagraphStyle/Dingbat</BasedOn>
        <BulletsCharacterStyle type="object">CharacterStyle/orange</BulletsCharacterStyle>
      </Properties>
    </ParagraphStyle>
    <ParagraphStyle Self="ParagraphStyle/Shared" Name="Shared">
      <Properties>
        <BulletChar BulletCharacterType="UnicodeOnly" BulletCharacterValue="10148"/>
        <BulletsFont type="string">ITC Zapf Dingbats Std</BulletsFont>
        <BulletsCharacterStyle type="object">CharacterStyle/inline</BulletsCharacterStyle>
      </Properties>
    </ParagraphStyle>
    <ParagraphStyle Self="ParagraphStyle/Round" Name="Round">
      <Properties>
        <BulletChar BulletCharacterType="UnicodeOnly" BulletCharacterValue="8226"/>
        <BulletsFont type="string">Wingdings</BulletsFont>
      </Properties>
    </ParagraphStyle>
    <ParagraphStyle Self="ParagraphStyle/Glyph" Name="Glyph">
      <Properties>
        <BulletChar BulletCharacterType="GlyphWithFont" BulletCharacterValue="10148"/>
      </Properties>
    </ParagraphStyle>
  </RootParagraphStyleGroup>
  <RootCharacterStyleGroup Self="rcs">
    <CharacterStyle Self="CharacterStyle/blue" Name="blue" FontStyle="Medium" PointSize="14">
      <Properties><AppliedFont type="string">ITC Zapf Dingbats Std</AppliedFont></Properties>
    </CharacterStyle>
    <CharacterStyle Self="CharacterStyle/orange" Name="orange" FontStyle="Medium" PointSize="14">
      <Properties><AppliedFont type="string">ITC Zapf Dingbats Std</AppliedFont></Properties>
    </CharacterStyle>
    <CharacterStyle Self="CharacterStyle/inline" Name="inline" FontStyle="Medium">
      <Properties><AppliedFont type="string">ITC Zapf Dingbats Std</AppliedFont></Properties>
    </CharacterStyle>
  </RootCharacterStyleGroup>
</idPkg:Styles>
"""

# `CharacterStyle/inline` sets type a reader can see, not just bullet furniture.
BULLET_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Shared">
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/inline">
        <Content>3</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""

BULLET_FONTS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Fonts xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <FontFamily Self="f1" Name="Myriad Pro"/>
</idPkg:Fonts>
"""


def _bullets(fonts=None):
    styles = etree.fromstring(BULLET_STYLES.encode())
    rtl.set_text_direction({"Resources/Styles.xml": styles,
                            "Stories/Story_u10.xml": etree.fromstring(BULLET_STORY.encode())},
                           fonts=fonts)
    return styles


def _style(styles, self_id):
    return styles.find(".//CharacterStyle[@Self='%s']" % self_id)


def _bullet(styles, name):
    return styles.find(".//ParagraphStyle[@Name='%s']//BulletChar" % name)


def test_an_arrow_bullet_turns_to_face_the_text():
    """→ has ← in its own block, so the glyph swaps and the font is untouched."""
    styles = _bullets()
    assert _bullet(styles, "Arrow").get("BulletCharacterValue") == "8592"


def test_a_mirrored_arrow_keeps_its_bullet_font():
    styles = _bullets()
    style = styles.find(".//ParagraphStyle[@Name='Arrow']")
    assert style.find(".//BulletsFont") is None


def test_a_dingbat_arrow_turns_round_by_changing_face():
    """ITC Zapf Dingbats has no leftwards arrowhead — every arrow in the face
    points right — so turning one round means leaving the face behind. The
    human-translated reference books do the same thing, drawing the flipped
    arrowhead as artwork rather than setting it."""
    styles = _bullets()
    assert _bullet(styles, "Dingbat").get("BulletCharacterValue") == "9668"  # ◄
    style = styles.find(".//ParagraphStyle[@Name='Dingbat']")
    assert style.find(".//BulletsFont").text == "Arial"
    assert style.find(".//BulletsFontStyle").text == "Regular"


def test_the_bullets_character_style_moves_face_with_the_bullet():
    """The character style carries the bullet's colour and its font. Left
    naming the dingbat face it would draw the new codepoint from a font that
    has no such glyph — a missing-glyph box in place of the arrow."""
    styles = _bullets()
    blue = _style(styles, "CharacterStyle/blue")
    assert blue.find(".//AppliedFont").text == "Arial"
    assert blue.get("FontStyle") == "Regular"


def test_a_bullet_style_that_also_sets_type_leaves_the_bullet_alone():
    """That character style is applied to a run as well, so retargeting its
    font would restyle text a reader can see. The bullet keeps the arrow and
    the face the source gave it."""
    styles = _bullets()
    assert _bullet(styles, "Shared").get("BulletCharacterValue") == "10148"
    shared = styles.find(".//ParagraphStyle[@Name='Shared']")
    assert shared.find(".//BulletsFont").text == "ITC Zapf Dingbats Std"
    assert _style(styles, "CharacterStyle/inline").find(".//AppliedFont").text         == "ITC Zapf Dingbats Std"


def test_a_substituted_bullet_declares_the_face_it_names():
    """Naming a family the package never declares is how a face silently gets
    substituted on open; `register_font` is what makes the swap resolve."""
    fonts = etree.fromstring(BULLET_FONTS.encode())
    _bullets(fonts=fonts)
    assert [f.get("Name") for f in fonts.iter("FontFamily")] == ["Myriad Pro", "Arial"]


def test_no_font_is_declared_when_no_bullet_needed_one():
    fonts = etree.fromstring(BULLET_FONTS.encode())
    styles = etree.fromstring(
        BULLET_STYLES.replace('BulletCharacterValue="10148"',
                              'BulletCharacterValue="8226"').encode())
    rtl.set_text_direction({"Resources/Styles.xml": styles}, fonts=fonts)
    assert [f.get("Name") for f in fonts.iter("FontFamily")] == ["Myriad Pro"]


def test_a_bullet_that_names_no_direction_is_left_alone():
    styles = _bullets()
    style = styles.find(".//ParagraphStyle[@Name='Round']")
    assert _bullet(styles, "Round").get("BulletCharacterValue") == "8226"
    assert style.find(".//BulletsFont").text == "Wingdings"


def test_a_glyph_id_bullet_is_never_remapped():
    """`GlyphWithFont` stores a glyph index, not a codepoint. Reading it as one
    swaps an unrelated glyph for another unrelated glyph."""
    styles = _bullets()
    assert _bullet(styles, "Glyph").get("BulletCharacterValue") == "10148"


def test_a_style_inheriting_a_substituted_bullet_moves_its_face_too():
    """The orange box on the Lesson 12 family letter.

    `Derived` declares no bullet of its own -- it is `BasedOn` `Dingbat` and
    inherits the arrow -- but overrides `BulletsCharacterStyle` to name a face
    of its own. Substituting the bullet only on the style that *declares* it
    left that face set in ITC Zapf Dingbats, which has no glyph at U+25C4, so
    the derived style printed a missing-glyph box in its own colour exactly
    where the arrow had been.
    """
    styles = _bullets()
    orange = _style(styles, "CharacterStyle/orange")
    assert orange.find(".//AppliedFont").text == "Arial"
    assert orange.get("FontStyle") == "Regular"


def test_a_bullet_is_left_alone_when_one_of_its_faces_cannot_follow():
    """Half a substitution is the missing-glyph box again, in whichever style
    could not move. If any face that draws this bullet also sets type a reader
    can see, the whole family keeps the arrow and the font the source gave it.
    """
    styles = etree.fromstring(BULLET_STYLES.replace(
        "CharacterStyle/orange", "CharacterStyle/inline").encode())
    rtl.set_text_direction(
        {"Resources/Styles.xml": styles,
         "Stories/Story_u10.xml": etree.fromstring(BULLET_STORY.encode())})
    assert _bullet(styles, "Dingbat").get("BulletCharacterValue") == "10148"
    assert _style(styles, "CharacterStyle/blue").find(".//AppliedFont").text         == "ITC Zapf Dingbats Std"
