"""What the RTL classifier is allowed to know about a page item."""

import pytest
from lxml import etree

from pagebirdy.idml import rtl_features

SINGLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"
          AppliedMaster="MasterSpread/A"/>
    {items}
  </Spread>
</idPkg:Spread>
"""


def _rect(self_id, x0, y0, x1, y1, transform="1 0 0 1 0 0", extra=""):
    return f"""
    <Rectangle Self="{self_id}" ItemTransform="{transform}" {extra}>
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="{x0} {y0}"/>
        <PathPointType Anchor="{x0} {y1}"/>
        <PathPointType Anchor="{x1} {y1}"/>
        <PathPointType Anchor="{x1} {y0}"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </Rectangle>"""


def _docs(items, name="Spreads/S.xml"):
    return {name: etree.fromstring(SINGLE.format(items=items).encode())}


def test_collect_reports_normalised_x_band_on_its_page():
    # A 100pt frame at x=50 on a 612pt page: band is 50/612 .. 150/612.
    docs = _docs(_rect("a", 50, 0, 150, 40, transform="1 0 0 1 0 0"))
    (feat,) = rtl_features.collect(docs)
    assert feat.self_id == "a"
    assert feat.page_index == 0
    assert feat.x_band[0] == pytest.approx(50 / 612, abs=1e-4)
    assert feat.x_band[1] == pytest.approx(150 / 612, abs=1e-4)
    assert feat.full_bleed is False


def test_collect_marks_a_full_bleed_item():
    docs = _docs(_rect("bleed", -6, 0, 618, 100))
    (feat,) = rtl_features.collect(docs)
    assert feat.full_bleed is True


def test_collect_marks_master_items_and_keeps_document_order():
    docs = _docs(_rect("a", 10, 0, 20, 10) + _rect("b", 30, 0, 40, 10),
                 name="MasterSpreads/M.xml")
    feats = rtl_features.collect(docs)
    assert [f.self_id for f in feats] == ["a", "b"]
    assert [f.z_index for f in feats] == [0, 1]
    assert all(f.is_master_item for f in feats)


def test_collect_records_rotation_without_treating_it_as_shear():
    # 90 degrees: a=0 b=1 c=-1 d=0.
    docs = _docs(_rect("v", 0, 0, 10, 60, transform="0 1 -1 0 500 0"))
    (feat,) = rtl_features.collect(docs)
    assert feat.rotated is True
    assert feat.sheared is False


def test_collect_reads_paragraph_styles_through_parent_story():
    story = etree.fromstring(b"""
      <idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
        <Story Self="st1">
          <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/_Family Letter%3aFL caret">
            <CharacterStyleRange><Content>ONE WAY</Content></CharacterStyleRange>
          </ParagraphStyleRange>
        </Story>
      </idPkg:Story>""")
    docs = _docs("""<TextFrame Self="t" ParentStory="st1" ItemTransform="1 0 0 1 0 0">
      <Properties><PathGeometry><GeometryPathType><PathPointArray>
        <PathPointType Anchor="0 0"/><PathPointType Anchor="0 10"/>
        <PathPointType Anchor="80 10"/><PathPointType Anchor="80 0"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </TextFrame>""")
    docs["Stories/S.xml"] = story
    (feat,) = rtl_features.collect(docs)
    # The %3a escape is decoded so rules can match on a readable name.
    assert "_Family Letter:FL caret" in feat.paragraph_styles
    assert feat.content_kind == "text"
    assert feat.script_mix == "latin"


def test_collect_z_index_increases_across_two_spread_documents():
    # A per-spread counter would restart at 0 for "B" and collide with "A"'s
    # values; a later stage sorts every component in the book by z_index, so
    # a collision there inverts cross-spread stacking order.
    docs = {
        "Spreads/A.xml": etree.fromstring(SINGLE.format(
            items=_rect("a1", 0, 0, 10, 10) + _rect("a2", 20, 0, 30, 10)
        ).encode()),
        "Spreads/B.xml": etree.fromstring(SINGLE.format(
            items=_rect("b1", 0, 0, 10, 10) + _rect("b2", 20, 0, 30, 10)
        ).encode()),
    }
    feats = rtl_features.collect(docs)
    assert [f.self_id for f in feats] == ["a1", "a2", "b1", "b2"]
    assert [f.z_index for f in feats] == [0, 1, 2, 3]


def test_collect_orders_documents_by_designmap_spine_not_filename():
    # designmap.xml lists "Z" before "A" -- the opposite of alphabetical --
    # which is the order collect() must honour; filename sort would give
    # exactly the wrong answer here on purpose, to catch a regression.
    designmap = etree.fromstring(b"""
      <Document xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" Self="d">
        <idPkg:Spread src="Spreads/Z.xml" />
        <idPkg:Spread src="Spreads/A.xml" />
      </Document>""")
    docs = {
        "Spreads/A.xml": etree.fromstring(SINGLE.format(
            items=_rect("a", 0, 0, 10, 10)).encode()),
        "Spreads/Z.xml": etree.fromstring(SINGLE.format(
            items=_rect("z", 0, 0, 10, 10)).encode()),
        "designmap.xml": designmap,
    }
    feats = rtl_features.collect(docs)
    assert [f.self_id for f in feats] == ["z", "a"]


def test_collect_marks_an_anchored_object_with_no_fabricated_geometry():
    # A page item nested inside a story's CharacterStyleRange -- rather than
    # under a Spread -- is an inline anchor. It carries an ItemTransform just
    # like a spread-placed item, but that transform is relative to the text
    # it's anchored in, not to spread space, so collect() must not measure it
    # as if it had spread geometry.
    story = etree.fromstring(b"""
      <idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
        <Story Self="st2">
          <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
            <CharacterStyleRange>
              <Content>before </Content>
              <Rectangle Self="anchor1" ItemTransform="1 0 0 1 -50 12"
                         AppliedObjectStyle="ObjectStyle/$ID/[None]">
                <Properties><PathGeometry><GeometryPathType><PathPointArray>
                  <PathPointType Anchor="0 0"/><PathPointType Anchor="0 5"/>
                  <PathPointType Anchor="20 5"/><PathPointType Anchor="20 0"/>
                </PathPointArray></GeometryPathType></PathGeometry></Properties>
              </Rectangle>
            </CharacterStyleRange>
          </ParagraphStyleRange>
        </Story>
      </idPkg:Story>""")
    docs = _docs("""<TextFrame Self="frame1" ParentStory="st2" ItemTransform="1 0 0 1 0 0">
      <Properties><PathGeometry><GeometryPathType><PathPointArray>
        <PathPointType Anchor="0 0"/><PathPointType Anchor="0 10"/>
        <PathPointType Anchor="80 10"/><PathPointType Anchor="80 0"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </TextFrame>""")
    docs["Stories/S2.xml"] = story
    feats = rtl_features.collect(docs)
    (anchor,) = [f for f in feats if f.self_id == "anchor1"]
    assert anchor.anchored is True
    assert anchor.bounds is None
    assert anchor.page_index is None
    assert anchor.x_band is None
    # Positioned by text flow: it belongs to the frame flowing its story.
    assert anchor.parent_id == "frame1"


def test_collect_does_not_leak_story_text_onto_a_storyless_item():
    # Matching the "{*}Story" wildcard would match both the real <Story> and
    # the namespaced <idPkg:Story> wrapper every Stories/*.xml is rooted in,
    # folding this story's text and styles into index[None]. A page item with
    # no ParentStory looks itself up with `.get(None, ...)`, so a polluted
    # None entry would hand a shape or image a story's styles and script it
    # never had -- exactly what a rule keyed on paragraph_styles would act on.
    story = etree.fromstring(b"""
      <idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
        <Story Self="st3">
          <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/_Master Page Styles:STEM %23">
            <CharacterStyleRange><Content>NOT MINE</Content></CharacterStyleRange>
          </ParagraphStyleRange>
        </Story>
      </idPkg:Story>""")
    # A Rectangle with no ParentStory at all -- a shape, not a text frame.
    docs = _docs(_rect("shape", 0, 0, 20, 20))
    docs["Stories/S3.xml"] = story
    (feat,) = rtl_features.collect(docs)
    assert feat.self_id == "shape"
    assert feat.paragraph_styles == frozenset()
    assert feat.script_mix == "none"


def test_collect_scopes_an_anchored_objects_paragraph_style_to_its_own_paragraph():
    # Two paragraphs in one story, with different styles; the anchor sits in
    # the second only. A rule table downstream treats certain style names as
    # evidence an object is directional and must be recomposed for RTL -- so
    # handing the anchor the *union* of both paragraphs' styles (the way a
    # text frame, which owns its whole story, correctly does) would flag it
    # as directional for sharing a story with a direction line it is nowhere
    # near, over-transforming an object that should stay put.
    story = etree.fromstring(b"""
      <idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
        <Story Self="st4">
          <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Direction line (Lesson)">
            <CharacterStyleRange><Content>Turn the page.</Content></CharacterStyleRange>
          </ParagraphStyleRange>
          <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Connect it graphic">
            <CharacterStyleRange>
              <Content>caption </Content>
              <Rectangle Self="anchor2" ItemTransform="1 0 0 1 -30 8">
                <Properties><PathGeometry><GeometryPathType><PathPointArray>
                  <PathPointType Anchor="0 0"/><PathPointType Anchor="0 5"/>
                  <PathPointType Anchor="15 5"/><PathPointType Anchor="15 0"/>
                </PathPointArray></GeometryPathType></PathGeometry></Properties>
              </Rectangle>
            </CharacterStyleRange>
          </ParagraphStyleRange>
        </Story>
      </idPkg:Story>""")
    docs = _docs("""<TextFrame Self="frame2" ParentStory="st4" ItemTransform="1 0 0 1 0 0">
      <Properties><PathGeometry><GeometryPathType><PathPointArray>
        <PathPointType Anchor="0 0"/><PathPointType Anchor="0 10"/>
        <PathPointType Anchor="80 10"/><PathPointType Anchor="80 0"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </TextFrame>""")
    docs["Stories/S4.xml"] = story
    feats = rtl_features.collect(docs)
    (anchor,) = [f for f in feats if f.self_id == "anchor2"]
    assert anchor.paragraph_styles == frozenset({"Connect it graphic"})
    assert "Direction line (Lesson)" not in anchor.paragraph_styles


def test_collect_marks_a_frame_whose_story_holds_a_table():
    # A table's Row/Cell structure lives inside the flowing frame's own
    # story, nested under a CharacterStyleRange like any other flowed
    # content -- it carries no ItemTransform of its own, so it never
    # appears by walking the TextFrame element the way a placed image does.
    # The frame that flows the story is what a rule table classifies, and
    # it must read "table", not "text", so table.default can ever fire.
    story = etree.fromstring(b"""
      <idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">
        <Story Self="st5">
          <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/graphic centered">
            <CharacterStyleRange>
              <Table Self="tbl1" HeaderRowCount="0" FooterRowCount="0"
                     BodyRowCount="2" ColumnCount="2">
                <Row Self="tbl1Row0" />
              </Table>
            </CharacterStyleRange>
          </ParagraphStyleRange>
        </Story>
      </idPkg:Story>""")
    docs = _docs("""<TextFrame Self="tframe" ParentStory="st5" ItemTransform="1 0 0 1 0 0">
      <Properties><PathGeometry><GeometryPathType><PathPointArray>
        <PathPointType Anchor="0 0"/><PathPointType Anchor="0 10"/>
        <PathPointType Anchor="80 10"/><PathPointType Anchor="80 0"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </TextFrame>""")
    docs["Stories/S5.xml"] = story
    (feat,) = rtl_features.collect(docs)
    assert feat.content_kind == "table"
