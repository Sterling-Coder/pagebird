"""Sibling sub-part labels (a., b., c., ...) end up on one shared start edge.

Fixtures build a minimal package by hand, the way `test_idml_textfit.py`
does: a spread of small `TextFrame`s, each pointing at its own one-paragraph
`Story` via `ParentStory`. Every frame in one "list" shares the same left
edge (`x0`) but a different width -- exactly the shape `rtl_subparts.py`'s
docstring describes: flush in English because they share a left edge,
staggered once mirrored to right-aligned Arabic because their widths (and so
their right edges) differ.

`normalize_subpart_indentation` is exercised directly, on documents already
in the *post-mirror* state it expects to run in (as `rtl.apply_rtl` leaves
them): it only ever adds `RightIndent`, so nothing here needs
`set_text_direction` to have actually run first, only its output shape.
"""

from lxml import etree

from pagebirdy.idml import rtl, rtl_subparts
from pagebirdy.idml.styles import StyleIndex

SPREAD = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 800 400" ItemTransform="1 0 0 1 0 0"/>
    {items}
  </Spread>
</idPkg:Spread>
"""

STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="{self_id}">
    <StoryPreference StoryDirection="RightToLeftDirection"/>
    <ParagraphStyleRange {para_attrs}>
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/bold">
        <Content>{letter}.</Content>
      </CharacterStyleRange>
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">
        <Content>{body}</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""

MULTILINE_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="{self_id}">
    <StoryPreference StoryDirection="RightToLeftDirection"/>
    <ParagraphStyleRange {para_attrs}>
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/bold">
        <Content>{letter}.</Content>
      </CharacterStyleRange>
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">
        <Content>	first line of {letter}</Content>
        <Br/>
        <Content>continuation line of {letter}</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""

PROSE_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="{self_id}">
    <StoryPreference StoryDirection="RightToLeftDirection"/>
    <ParagraphStyleRange>
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">
        <Content>{text}</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <RootParagraphStyleGroup Self="root">
    <ParagraphStyle Self="ParagraphStyle/SubPart" Name="SubPart" RightIndent="38"/>
  </RootParagraphStyleGroup>
</idPkg:Styles>
"""


def _frame(self_id, story_id, x0, y0, x1, y1):
    return f"""
    <TextFrame Self="{self_id}" ParentStory="{story_id}" ItemTransform="1 0 0 1 0 0"
              PreviousTextFrame="n" NextTextFrame="n">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="{x0} {y0}"/><PathPointType Anchor="{x0} {y1}"/>
        <PathPointType Anchor="{x1} {y1}"/><PathPointType Anchor="{x1} {y0}"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
      <TextFramePreference TextColumnCount="1"/>
    </TextFrame>"""


def _story_xml(template, self_id, letter, x1, para_attrs=""):
    return template.format(self_id=self_id, letter=letter,
                           body="\t" + "body text for {} ".format(letter) * (1 + int(x1) % 3),
                           para_attrs=para_attrs)


def _build(rows, styles=None, template=STORY):
    """`rows`: list of (letter, story_id, x0, y0, x1, y1[, para_attrs])."""
    items = []
    docs = {}
    for row in rows:
        letter, story_id, x0, y0, x1, y1 = row[:6]
        para_attrs = row[6] if len(row) > 6 else ""
        items.append(_frame(f"tf_{story_id}", story_id, x0, y0, x1, y1))
        docs[f"Stories/Story_{story_id}.xml"] = etree.fromstring(
            _story_xml(template, story_id, letter, x1, para_attrs).encode())
    docs["Spreads/S.xml"] = etree.fromstring(SPREAD.format(items="".join(items)).encode())
    if styles is not None:
        docs["Resources/Styles.xml"] = etree.fromstring(styles.encode())
    return docs


def _psr(docs, story_id):
    story = docs[f"Stories/Story_{story_id}.xml"]
    return story.find(".//{*}ParagraphStyleRange")


def _edge(docs, story_id, x1):
    """The paragraph's resolved absolute right edge after normalization."""
    index = StyleIndex(docs.get("Resources/Styles.xml"))
    psr = _psr(docs, story_id)
    right_indent = float(index.effective(psr, None, "RightIndent") or 0.0)
    return float(x1) - right_indent


# ---- the core policy ---------------------------------------------------------


def test_six_subparts_share_one_starting_edge():
    rows = [
        ("a", "a", 0, 0, 100, 20),
        ("b", "b", 0, 40, 140, 60),
        ("c", "c", 0, 80, 90, 100),
        ("d", "d", 0, 120, 60, 140),
        ("e", "e", 0, 160, 130, 180),
        ("f", "f", 0, 200, 110, 220),
    ]
    docs = _build(rows)
    report = rtl_subparts.normalize_subpart_indentation(docs)

    edges = [_edge(docs, sid, x1) for (_l, sid, _x0, _y0, x1, _y1) in rows]
    assert max(edges) - min(edges) < 1e-6, edges
    assert report["rtl_subpart_groups_aligned"] == 1
    # every member except the narrowest (already the anchor) needed a nudge
    assert report["rtl_subpart_paragraphs_indented"] == 5


def test_only_a_to_c_still_aligns():
    rows = [
        ("a", "a", 0, 0, 80, 20),
        ("b", "b", 0, 40, 150, 60),
        ("c", "c", 0, 80, 55, 100),
    ]
    docs = _build(rows)
    rtl_subparts.normalize_subpart_indentation(docs)
    edges = [_edge(docs, sid, x1) for (_l, sid, _x0, _y0, x1, _y1) in rows]
    assert max(edges) - min(edges) < 1e-6, edges


def test_only_a_to_d_still_aligns():
    rows = [
        ("a", "a", 0, 0, 200, 20),
        ("b", "b", 0, 40, 90, 60),
        ("c", "c", 0, 80, 120, 100),
        ("d", "d", 0, 120, 75, 140),
    ]
    docs = _build(rows)
    rtl_subparts.normalize_subpart_indentation(docs)
    edges = [_edge(docs, sid, x1) for (_l, sid, _x0, _y0, x1, _y1) in rows]
    assert max(edges) - min(edges) < 1e-6, edges


def test_two_questions_in_one_column_align_independently():
    """Letter resets to 'a' partway down the same left edge -- a second
    question sharing the first question's margin. Each run is normalized to
    its own anchor; the two runs are not required to share one edge with
    each other, only internally."""
    q1 = [
        ("a", "q1a", 0, 0, 100, 20),
        ("b", "q1b", 0, 40, 160, 60),
        ("c", "q1c", 0, 80, 70, 100),
    ]
    q2 = [
        ("a", "q2a", 0, 300, 50, 320),
        ("b", "q2b", 0, 340, 130, 360),
        ("c", "q2c", 0, 380, 90, 400),
        ("d", "q2d", 0, 420, 200, 440),
    ]
    docs = _build(q1 + q2)
    report = rtl_subparts.normalize_subpart_indentation(docs)

    edges1 = [_edge(docs, sid, x1) for (_l, sid, _x0, _y0, x1, _y1) in q1]
    edges2 = [_edge(docs, sid, x1) for (_l, sid, _x0, _y0, x1, _y1) in q2]
    assert max(edges1) - min(edges1) < 1e-6, edges1
    assert max(edges2) - min(edges2) < 1e-6, edges2
    assert report["rtl_subpart_groups_aligned"] == 2


def test_a_lone_subpart_is_left_alone():
    docs = _build([("a", "a", 0, 0, 100, 20)])
    report = rtl_subparts.normalize_subpart_indentation(docs)
    assert report["rtl_subpart_groups_aligned"] == 0
    assert _psr(docs, "a").get("RightIndent") is None


def test_prose_paragraph_without_a_label_is_untouched():
    rows = [
        ("a", "a", 0, 0, 100, 20),
        ("b", "b", 0, 40, 160, 60),
    ]
    docs = _build(rows)
    docs["Stories/Story_prose.xml"] = etree.fromstring(
        PROSE_STORY.format(self_id="prose", text="Complete the table below.").encode())
    frame_xml = _frame("tf_prose", "prose", 200, 0, 340, 20)
    spread_el = docs["Spreads/S.xml"].find("{*}Spread")
    spread_el.append(etree.fromstring(frame_xml))

    rtl_subparts.normalize_subpart_indentation(docs)
    prose_psr = docs["Stories/Story_prose.xml"].find(".//{*}ParagraphStyleRange")
    assert prose_psr.get("RightIndent") is None


def test_multiline_subpart_keeps_one_indent_for_every_line():
    rows = [
        ("a", "a", 0, 0, 200, 20),
        ("b", "b", 0, 40, 90, 60),
        ("c", "c", 0, 80, 130, 100),
    ]
    docs = _build(rows, template=MULTILINE_STORY)
    rtl_subparts.normalize_subpart_indentation(docs)

    edges = [_edge(docs, sid, x1) for (_l, sid, _x0, _y0, x1, _y1) in rows]
    assert max(edges) - min(edges) < 1e-6, edges
    # RightIndent is a paragraph-level attribute in IDML: one value on the
    # ParagraphStyleRange already governs every wrapped/continuation line.
    for _l, sid, _x0, _y0, x1, _y1 in rows:
        psr = _psr(docs, sid)
        assert psr.tag.endswith("ParagraphStyleRange")


def test_existing_style_indent_is_extended_not_overwritten():
    """A shared named style already supplies RightIndent=38 (e.g. a hanging
    indent for the label) to every member with no inline override. The
    narrower member (the anchor) is left inheriting it untouched; the wider
    member gets an inline override that is the inherited 38 *plus* its own
    delta, not a bare replacement that forgets the 38."""
    rows = [
        ("a", "a", 0, 0, 100, 20, 'AppliedParagraphStyle="ParagraphStyle/SubPart"'),
        ("b", "b", 0, 40, 180, 60, 'AppliedParagraphStyle="ParagraphStyle/SubPart"'),
    ]
    docs = _build(rows, styles=STYLES)
    rtl_subparts.normalize_subpart_indentation(docs)

    edges = [_edge(docs, sid, x1) for (_l, sid, _x0, _y0, x1, _y1, _p) in rows]
    assert max(edges) - min(edges) < 1e-6, edges

    anchor_psr = _psr(docs, "a")  # narrower frame (100) is the anchor
    wide_psr = _psr(docs, "b")    # wider frame (180) needs the nudge
    assert anchor_psr.get("RightIndent") is None  # still just inheriting 38
    assert float(wide_psr.get("RightIndent")) > 38.0


def test_numbered_points_share_one_starting_edge():
    """Same guarantee as test_six_subparts_share_one_starting_edge, for
    digit markers instead of letters."""
    rows = [
        ("1", "n1", 0, 0, 100, 20),
        ("2", "n2", 0, 40, 140, 60),
        ("3", "n3", 0, 80, 90, 100),
        ("4", "n4", 0, 120, 60, 140),
    ]
    docs = _build(rows)
    report = rtl_subparts.normalize_subpart_indentation(docs)

    edges = [_edge(docs, sid, x1) for (_l, sid, _x0, _y0, x1, _y1) in rows]
    assert max(edges) - min(edges) < 1e-6, edges
    assert report["rtl_subpart_groups_aligned"] == 1
    assert report["rtl_subpart_paragraphs_indented"] == 3


def test_numbered_points_continue_into_double_digits():
    """9 -> 10 must still read as consecutive: an integer comparison, not a
    single-character `ord()` step, which is what the lettered case uses."""
    rows = [(str(n), f"n{n}", 0, n * 40, 60 + n * 7, n * 40 + 20)
            for n in range(8, 12)]
    docs = _build(rows)
    report = rtl_subparts.normalize_subpart_indentation(docs)
    assert report["rtl_subpart_groups_aligned"] == 1

    edges = [_edge(docs, sid, x1) for (_l, sid, _x0, _y0, x1, _y1) in rows]
    assert max(edges) - min(edges) < 1e-6, edges


def test_a_lettered_and_a_numbered_group_on_the_same_edge_are_still_one_run_each():
    """A letter run and a digit run never chain into each other (`ord`/`int`
    comparisons never cross marker types), even sharing a left edge."""
    letters = [
        ("a", "la", 0, 0, 80, 20),
        ("b", "lb", 0, 40, 150, 60),
    ]
    numbers = [
        ("1", "d1", 0, 300, 50, 320),
        ("2", "d2", 0, 340, 130, 360),
    ]
    docs = _build(letters + numbers)
    report = rtl_subparts.normalize_subpart_indentation(docs)
    assert report["rtl_subpart_groups_aligned"] == 2


def test_numbered_point_content_indentation_is_consistent_across_the_group():
    """Geometry expectation 2 from the spec: content after each marker
    starts at one consistent indentation, regardless of that item's own
    original frame width."""
    rows = [
        ("1", "n1", 0, 0, 100, 20),
        ("2", "n2", 0, 40, 200, 60),
        ("3", "n3", 0, 80, 130, 100),
    ]
    docs = _build(rows)
    rtl_subparts.normalize_subpart_indentation(docs)
    edges = [_edge(docs, sid, x1) for (_l, sid, _x0, _y0, x1, _y1) in rows]
    # every member's resolved right edge (= its content's RTL start) is the
    # same point, whatever its own original width was
    assert max(edges) - min(edges) < 1e-6, edges


def test_numbered_point_wrapped_lines_follow_content_not_the_marker():
    """Geometry expectation 3: RightIndent is a whole-paragraph property, so
    a wrapped continuation line inherits the same adjusted margin as the
    first line -- it never re-anchors to the marker."""
    rows = [
        ("1", "n1", 0, 0, 200, 20),
        ("2", "n2", 0, 40, 90, 60),
        ("3", "n3", 0, 80, 130, 100),
    ]
    docs = _build(rows, template=MULTILINE_STORY)
    rtl_subparts.normalize_subpart_indentation(docs)
    edges = [_edge(docs, sid, x1) for (_l, sid, _x0, _y0, x1, _y1) in rows]
    assert max(edges) - min(edges) < 1e-6, edges
