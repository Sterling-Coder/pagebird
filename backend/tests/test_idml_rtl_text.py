"""RTL text handling: the font a run is retyped in, and what stays left-to-right.

Two failures a mirrored page cannot show you. A run whose face was swapped for
one it did not need changes font halfway through a fraction; a run left to bidi
that should have been pinned prints `10x + 15y = 150` with its operators
migrated to the far end of the line.
"""

import zipfile

from lxml import etree

from pagebirdy.idml import rtl
from pagebirdy.idml.package import IdmlPackage
from pagebirdy.translate.engine import Engine
from pagebirdy.translate.translator import Translator

ARABIC = "الرياضيات"

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <RootParagraphStyleGroup Self="ups">
    <ParagraphStyle Self="ParagraphStyle/Head" Name="Head" FontStyle="900">
      <Properties><AppliedFont type="string">Museo Sans</AppliedFont></Properties>
    </ParagraphStyle>
    <ParagraphStyle Self="ParagraphStyle/Body" Name="Body" FontStyle="300">
      <Properties><AppliedFont type="string">Museo Sans</AppliedFont></Properties>
    </ParagraphStyle>
  </RootParagraphStyleGroup>
</idPkg:Styles>
"""

STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Head">
      <CharacterStyleRange><Content>Understanding Ratios</Content></CharacterStyleRange>
    </ParagraphStyleRange>
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange><Content>Solve it</Content></CharacterStyleRange>
      <CharacterStyleRange><Content>10x + 15y = 150</Content></CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


class MapEngine(Engine):
    name = "fake"

    def __init__(self, mapping):
        self.mapping = mapping

    def translate(self, texts):
        return [self.mapping.get(t, t) for t in texts]


def _make_idml(path, story=STORY):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr("Stories/Story_u10.xml", story)
        z.writestr("Resources/Styles.xml", STYLES)


def _translated(tmp_path, mapping, styles=("Regular", "Bold")):
    src = str(tmp_path / "in.idml")
    _make_idml(src)
    pkg = IdmlPackage(src)
    segs = pkg.segments()
    Translator(MapEngine(mapping), None, None).run(segs)
    pkg.apply(segs, idml_font="Adobe Arabic", font_styles=styles)
    return pkg


def _story_of(pkg):
    return pkg.documents["Stories/Story_u10.xml"]


def _run_holding(pkg, needle):
    for csr in _story_of(pkg).iter("CharacterStyleRange"):
        if any(needle in (c.text or "") for c in csr.iter("Content")):
            return csr
    raise AssertionError(f"no run holding {needle!r}")


def _font_of(csr):
    font = csr.find("./Properties/AppliedFont")
    return font.text if font is not None else None


# ---- which runs get the target face -----------------------------------------


def test_a_run_written_in_the_target_script_gets_the_target_face(tmp_path):
    pkg = _translated(tmp_path, {"Understanding Ratios": ARABIC})
    assert _font_of(_run_holding(pkg, ARABIC)) == "Adobe Arabic"


def test_an_equation_that_came_back_unchanged_keeps_its_own_face(tmp_path):
    """The engine hands `10x + 15y = 150` straight back. Retyping it in an
    Arabic face changes font halfway through the expression for no gain."""
    pkg = _translated(tmp_path, {"Understanding Ratios": ARABIC})
    assert _font_of(_run_holding(pkg, "15y")) is None


def test_an_untranslated_latin_run_keeps_its_own_face(tmp_path):
    pkg = _translated(tmp_path, {"Understanding Ratios": ARABIC})
    assert _font_of(_run_holding(pkg, "Solve it")) is None


# ---- the weight travels with the family -------------------------------------


def test_an_inherited_bold_weight_survives_the_substitution(tmp_path):
    """`Head` is `Museo Sans 900`. Naming `900` at an Arabic family that has no
    `900` is a missing-style substitution, and the heading opens regular."""
    pkg = _translated(tmp_path, {"Understanding Ratios": ARABIC})
    assert _run_holding(pkg, ARABIC).get("FontStyle") == "Bold"


def test_an_inherited_light_weight_maps_to_regular(tmp_path):
    pkg = _translated(tmp_path, {"Solve it": ARABIC})
    assert _run_holding(pkg, ARABIC).get("FontStyle") == "Regular"


def test_the_faces_actually_named_are_recorded_for_registration(tmp_path):
    """`Fonts.xml` has to declare exactly what the stories name, or the run
    lands on a face the package never described."""
    pkg = _translated(tmp_path, {"Understanding Ratios": ARABIC, "Solve it": ARABIC})
    assert pkg.font_styles_used == {"Bold", "Regular"}


def test_a_family_with_no_bold_is_never_asked_for_one(tmp_path):
    pkg = _translated(tmp_path, {"Understanding Ratios": ARABIC},
                      styles=("Regular",))
    assert _run_holding(pkg, ARABIC).get("FontStyle") == "Regular"
    assert pkg.font_styles_used == {"Regular"}


# ---- registering the faces that were named ----------------------------------

FONTS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Fonts xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <FontFamily Self="fam1" Name="Minion Pro"><Font Self="f1" FontFamily="Minion Pro"/></FontFamily>
</idPkg:Fonts>
"""


def _fonts():
    return etree.fromstring(FONTS.encode())


def test_every_style_the_stories_name_is_declared():
    tree = _fonts()
    rtl.register_font(tree, "Adobe Arabic", ("Regular", "Bold"))
    fam = [f for f in tree.iter("FontFamily") if f.get("Name") == "Adobe Arabic"][0]
    assert [f.get("FontStyleName") for f in fam.findall("Font")] == ["Regular", "Bold"]


def test_each_declared_face_carries_its_own_postscript_name():
    """Two faces sharing one PostScript name is one face, and the bold is lost."""
    tree = _fonts()
    rtl.register_font(tree, "Adobe Arabic", ("Regular", "Bold"))
    fam = [f for f in tree.iter("FontFamily") if f.get("Name") == "Adobe Arabic"][0]
    names = [f.get("PostScriptName") for f in fam.findall("Font")]
    assert names == ["AdobeArabic-Regular", "AdobeArabic-Bold"]
    assert len(set(f.get("Self") for f in fam.findall("Font"))) == 2


def test_registering_with_no_styles_still_declares_a_regular():
    tree = _fonts()
    rtl.register_font(tree, "Adobe Arabic", ())
    fam = [f for f in tree.iter("FontFamily") if f.get("Name") == "Adobe Arabic"][0]
    assert [f.get("FontStyleName") for f in fam.findall("Font")] == ["Regular"]


# ---- keeping left-to-right content left-to-right ----------------------------

MIXED = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange><Content>{ARABIC}</Content></CharacterStyleRange>
      <CharacterStyleRange><Content>10x + 15y = 150</Content></CharacterStyleRange>
      <CharacterStyleRange><Content>https://example.org/a</Content></CharacterStyleRange>
      <CharacterStyleRange><Content> / </Content></CharacterStyleRange>
      <CharacterStyleRange><Content>{ARABIC} 42</Content></CharacterStyleRange>
      <CharacterStyleRange CharacterDirection="RightToLeftDirection">
        <Content>2024</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


def _pinned():
    tree = etree.fromstring(MIXED.encode())
    pinned = rtl.preserve_ltr_content({"Stories/Story_u10.xml": tree})
    return tree, pinned


def _direction(tree, needle):
    """The direction of the run holding `needle`.

    An exact match wins over a substring one, so asking about the `/` run does
    not answer about the URL that also contains a slash.
    """
    found = None
    for csr in tree.iter("CharacterStyleRange"):
        text = "".join(c.text or "" for c in csr.iter("Content"))
        if text.strip() == needle.strip():
            return csr.get("CharacterDirection")
        if found is None and needle in text:
            found = csr
    if found is None:
        raise AssertionError(f"no run holding {needle!r}")
    return found.get("CharacterDirection")


def test_an_equation_is_pinned_left_to_right():
    """The `+` and `=` are neutrals. Resolved against an Arabic paragraph they
    migrate; resolved inside a left-to-right run they stay put."""
    tree, _ = _pinned()
    assert _direction(tree, "15y") == "LeftToRightDirection"


def test_a_url_is_pinned_left_to_right():
    tree, _ = _pinned()
    assert _direction(tree, "example.org") == "LeftToRightDirection"


def test_an_arabic_run_is_left_to_inherit_the_paragraph():
    tree, _ = _pinned()
    assert _direction(tree, ARABIC) is None


def test_a_run_mixing_arabic_and_digits_is_left_to_bidi():
    """Pinning a run with Arabic in it is the mirror image of the bug."""
    tree, _ = _pinned()
    assert _direction(tree, "42") is None


def test_a_run_of_pure_punctuation_is_left_alone():
    """A fraction bar takes its direction from the line it sits in."""
    tree, _ = _pinned()
    assert _direction(tree, "/") is None


def test_a_direction_the_source_declared_is_never_overridden():
    tree, _ = _pinned()
    assert _direction(tree, "2024") == "RightToLeftDirection"


def test_the_count_reports_only_the_runs_pinned():
    _, pinned = _pinned()
    assert pinned == 2  # the equation and the URL


def test_pinning_is_idempotent():
    tree = etree.fromstring(MIXED.encode())
    docs = {"Stories/Story_u10.xml": tree}
    rtl.preserve_ltr_content(docs)
    assert rtl.preserve_ltr_content(docs) == 0


def test_pinning_reads_the_text_around_a_line_break():
    """InDesign parks prose in each child's tail; reading only `.text` would
    judge a run's direction from a fraction of it."""
    story = etree.fromstring(
        '<Story><ParagraphStyleRange><CharacterStyleRange><Content>'
        f'<Br/>{ARABIC}</Content></CharacterStyleRange>'
        '</ParagraphStyleRange></Story>'.encode())
    assert rtl.preserve_ltr_content({"Stories/s.xml": story}) == 0


# ---- table direction reaches the styles too ---------------------------------

TABLE_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <RootTableStyleGroup Self="uts">
    <TableStyle Self="TableStyle/Data" Name="Data"/>
  </RootTableStyleGroup>
</idPkg:Styles>
"""


def test_a_table_style_orders_its_columns_right_to_left():
    """A table that overrides nothing gets its direction from its style, the
    same way a paragraph does."""
    tree = etree.fromstring(TABLE_STYLES.encode())
    rtl.set_text_direction({"Resources/Styles.xml": tree})
    style = tree.find(".//TableStyle")
    assert style.get("TableDirection") == "RightToLeftDirection"
