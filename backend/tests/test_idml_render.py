import zipfile

import fitz

from babel.idml.render import render_idml_to_pdf

AR_TEXT = "الصفحة 12 من 25"


def _is_shaped(text):
    """Arabic Presentation Forms A/B — present only if the run was shaped."""
    return any(0xFB50 <= ord(c) <= 0xFEFF for c in text)


SPREAD = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="us1">
    <Page Self="up1" GeometricBounds="0 0 100 300" ItemTransform="1 0 0 1 0 0"/>
    <TextFrame Self="uf1" ParentStory="ust1" ItemTransform="1 0 0 1 0 0">
      <Properties>
        <PathGeometry>
          <GeometryPathType>
            <PathPointArray>
              <PathPointType Anchor="10 10"/>
              <PathPointType Anchor="290 10"/>
              <PathPointType Anchor="290 90"/>
              <PathPointType Anchor="10 90"/>
            </PathPointArray>
          </GeometryPathType>
        </PathGeometry>
      </Properties>
    </TextFrame>
  </Spread>
</idPkg:Spread>
"""

STORY = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="ust1">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange>
        <Content>{AR_TEXT}</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


def _make_idml(path, story_xml=STORY):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr("Spreads/Spread_us1.xml", SPREAD)
        z.writestr("Stories/Story_ust1.xml", story_xml)


def test_rtl_draft_render_shapes_arabic(tmp_path):
    """`insert_textbox` (the old approach) does not reorder or shape RTL
    text at all — it only right-*aligns* the raw logical-order codepoints,
    which for Arabic renders as a garbled, unjoined mirror of the real
    text. `insert_htmlbox` goes through MuPDF's real text-layout engine."""
    src = str(tmp_path / "in.idml")
    _make_idml(src)

    out = str(tmp_path / "out.pdf")
    render_idml_to_pdf(src, out, target_lang="ar")

    doc = fitz.open(out)
    text = "".join(p.get_text() for p in doc)
    doc.close()
    assert _is_shaped(text), f"unshaped output: {text!r}"


def test_ltr_draft_render_still_works(tmp_path):
    story = STORY.replace(AR_TEXT, "Write the missing digits")
    src = str(tmp_path / "in.idml")
    _make_idml(src, story)

    out = str(tmp_path / "out.pdf")
    render_idml_to_pdf(src, out, target_lang="es")

    doc = fitz.open(out)
    text = "".join(p.get_text() for p in doc)
    doc.close()
    # insert_htmlbox's layout engine renders space runs as U+00A0 — a
    # cosmetic extraction detail (draws identically to a normal space),
    # not the thing this test is checking.
    assert "Write the missing digits" in text.replace("\xa0", " ")
