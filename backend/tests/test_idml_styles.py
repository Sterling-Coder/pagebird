"""A run's *effective* font and weight, resolved through the styles.

A `<CharacterStyleRange>` rarely names its own face. Reading the inline
attribute alone answered "no font" for almost every run in the sample books,
which left the math guard unable to see two thirds of the math and the font
substitution unable to see any weight at all.
"""

import zipfile

from lxml import etree

from pagebirdy.idml.package import IdmlPackage
from pagebirdy.idml.styles import (StyleIndex, is_bold, is_italic, ranges_of,
                               target_font_style)

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <RootCharacterStyleGroup Self="ucs">
    <CharacterStyle Self="CharacterStyle/$ID/[No character style]" Name="$ID/[No character style]"/>
    <CharacterStyle Self="CharacterStyle/MathPi 6" Name="MathPi 6">
      <Properties>
        <BasedOn type="string">$ID/[No character style]</BasedOn>
        <AppliedFont type="string">Mathematical Pi LT Std</AppliedFont>
      </Properties>
    </CharacterStyle>
    <CharacterStyle Self="CharacterStyle/MathPi 6 small" Name="MathPi 6 small">
      <Properties><BasedOn type="string">CharacterStyle/MathPi 6</BasedOn></Properties>
    </CharacterStyle>
    <CharacterStyle Self="CharacterStyle/lead-in" Name="lead-in" FontStyle="Semibold Italic"/>
  </RootCharacterStyleGroup>
  <RootParagraphStyleGroup Self="ups">
    <ParagraphStyle Self="ParagraphStyle/Body" Name="Body" FontStyle="300">
      <Properties><AppliedFont type="string">Museo Sans</AppliedFont></Properties>
    </ParagraphStyle>
    <ParagraphStyle Self="ParagraphStyle/Head" Name="Head" FontStyle="900">
      <Properties><BasedOn type="string">ParagraphStyle/Body</BasedOn></Properties>
    </ParagraphStyle>
  </RootParagraphStyleGroup>
</idPkg:Styles>
"""

PREFS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Preferences xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <DocumentPreference PageBinding="LeftToRight"/>
  <TextDefault FontStyle="Regular">
    <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
  </TextDefault>
</idPkg:Preferences>
"""

# Four runs, each getting its face from a different level of the cascade.
STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Head">
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/MathPi 6">
        <Content>/</Content>
      </CharacterStyleRange>
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/MathPi 6 small">
        <Content>+</Content>
      </CharacterStyleRange>
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">
        <Content>Understanding Ratios</Content>
      </CharacterStyleRange>
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/lead-in">
        <Properties><AppliedFont type="string">Myriad Pro</AppliedFont></Properties>
        <Content>Try It</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


def _make_idml(path, story=STORY, styles=STYLES, prefs=PREFS):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr("Stories/Story_u10.xml", story)
        if styles:
            z.writestr("Resources/Styles.xml", styles)
        if prefs:
            z.writestr("Resources/Preferences.xml", prefs)


def _index():
    return StyleIndex(etree.fromstring(STYLES.encode()),
                      etree.fromstring(PREFS.encode()).find(".//TextDefault"))


def _run(text):
    story = etree.fromstring(STORY.encode())
    for content in story.iter("Content"):
        if (content.text or "") == text:
            return ranges_of(content)
    raise AssertionError(f"no run holding {text!r}")


def _font(text):
    psr, csr = _run(text)
    return _index().effective(psr, csr, "AppliedFont")


def _style(text):
    psr, csr = _run(text)
    return _index().effective(psr, csr, "FontStyle")


# ---- resolving the face -----------------------------------------------------


def test_a_face_from_the_character_style_is_found():
    assert _font("/") == "Mathematical Pi LT Std"


def test_a_face_inherited_through_based_on_is_found():
    """`MathPi 6 small` declares no font of its own and is based on one that
    does. Stopping at the style itself is what left these runs unprotected."""
    assert _font("+") == "Mathematical Pi LT Std"


def test_a_face_from_the_paragraph_style_is_found():
    assert _font("Understanding Ratios") == "Museo Sans"


def test_an_inline_face_beats_every_style():
    assert _font("Try It") == "Myriad Pro"


def test_a_package_with_no_styles_resolves_to_nothing_rather_than_raising():
    empty = StyleIndex()
    psr, csr = _run("Understanding Ratios")
    assert empty.effective(psr, csr, "AppliedFont") is None


def test_the_document_default_is_the_last_resort():
    story = etree.fromstring(
        b'<Story><ParagraphStyleRange><CharacterStyleRange>'
        b'<Content>x</Content></CharacterStyleRange></ParagraphStyleRange></Story>')
    psr, csr = ranges_of(story.find(".//Content"))
    assert _index().effective(psr, csr, "AppliedFont") == "Minion Pro"


# ---- resolving the weight ---------------------------------------------------


def test_a_weight_from_the_character_style_is_found():
    assert _style("Try It") == "Semibold Italic"


def test_a_weight_inherited_through_based_on_is_found():
    """`Head` is based on `Body` but declares `900` itself."""
    assert _style("Understanding Ratios") == "900"


# ---- the guard the resolution exists for ------------------------------------


def test_reading_the_styles_does_not_schedule_them_for_rewriting(tmp_path):
    """An LTR job must come out byte-identical where it changed nothing.

    Resolving an inherited font reads `Resources/Styles.xml`; if that claimed
    the entry for writeback, every job would re-serialise it.
    """
    src = str(tmp_path / "in.idml")
    _make_idml(src)

    pkg = IdmlPackage(src)
    pkg.segments()
    assert "Resources/Styles.xml" not in pkg.documents

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(out) as b:
        assert a.read("Resources/Styles.xml") == b.read("Resources/Styles.xml")


def test_a_reader_sees_an_entry_another_stage_is_editing(tmp_path):
    """`read_document` must never hand back a stale copy of a live tree."""
    src = str(tmp_path / "in.idml")
    _make_idml(src)

    pkg = IdmlPackage(src)
    editable = pkg.document("Resources/Styles.xml")
    assert pkg.read_document("Resources/Styles.xml") is editable


# ---- mapping a weight onto the target family --------------------------------


def test_numeric_weights_are_read_on_the_hundreds_axis():
    assert is_bold("900") and is_bold("700") and is_bold("600")
    assert not is_bold("500") and not is_bold("300")


def test_a_single_digit_style_name_is_not_a_weight():
    """`Mathematical Pi LT Std` calls its only face "3"."""
    assert not is_bold("3")


def test_named_weights_are_recognised():
    for name in ("Bold", "Black", "Heavy", "Semibold", "ExtraBold", "Bold Italic"):
        assert is_bold(name), name


def test_slant_is_recognised():
    assert is_italic("Semibold Italic") and is_italic("Oblique")
    assert not is_italic("Semibold")


def test_a_bold_weight_maps_to_the_target_family_s_bold():
    assert target_font_style("900", ("Regular", "Bold")) == "Bold"


def test_a_regular_weight_maps_to_regular():
    assert target_font_style("300", ("Regular", "Bold")) == "Regular"


def test_a_weight_the_family_does_not_ship_degrades_rather_than_being_invented():
    """Arabic families ship no italic. Naming one gives the missing-style
    substitution the whole exercise exists to avoid."""
    assert target_font_style("Semibold Italic", ("Regular", "Bold")) == "Bold"
    assert target_font_style("Italic", ("Regular", "Bold")) == "Regular"


def test_a_family_shipping_italics_gets_them():
    faces = ("Regular", "Bold", "Italic", "Bold Italic")
    assert target_font_style("Semibold Italic", faces) == "Bold Italic"
    assert target_font_style("Italic", faces) == "Italic"


def test_a_run_that_declares_no_weight_is_regular():
    assert target_font_style(None, ("Regular", "Bold")) == "Regular"
