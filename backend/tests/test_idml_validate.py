"""The before/after check on a converted IDML.

Every guarantee the RTL stage makes is invisible until someone opens the result
in InDesign. This is the thing that opens it instead: it re-reads both packages
and asks, object by object, whether what had to move moved and what had to
survive survived.

The synthetic fixtures exercise each check in isolation by *breaking* it; the
end-to-end tests run the real pipeline on a real textbook.
"""

import gc
import glob
import os
import shutil
import zipfile

import pytest
from lxml import etree

from pagebirdy.idml.package import IdmlPackage
from pagebirdy.idml.validate import _same_page, format_report, validate_rtl_idml
from pagebirdy.translate.engine import Engine
from pagebirdy.translate.translator import Translator

ARABIC = "الرياضيات"

SPREAD = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"/>
    <TextFrame Self="tf1" ParentStory="u10" ItemTransform="1 0 0 1 100 -300">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="0 0"/><PathPointType Anchor="0 50"/>
        <PathPointType Anchor="200 50"/><PathPointType Anchor="200 0"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
    </TextFrame>
    <Rectangle Self="r1" ItemTransform="1 0 0 1 400 -100">
      <Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>
        <PathPointType Anchor="0 0"/><PathPointType Anchor="0 60"/>
        <PathPointType Anchor="80 60"/><PathPointType Anchor="80 0"/>
      </PathPointArray></GeometryPathType></PathGeometry></Properties>
      <Image Self="img1"><Link Self="lk1" LinkResourceURI="file:/art/figure.ai"/></Image>
    </Rectangle>
  </Spread>
</idPkg:Spread>
"""

STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <StoryPreference StoryDirection="LeftToRightDirection"/>
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body" Composer="HL Composer">
      <CharacterStyleRange><Content>Understanding Ratios</Content></CharacterStyleRange>
      <CharacterStyleRange><Content>10x + 15y = 150</Content></CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <RootParagraphStyleGroup Self="ups">
    <ParagraphStyle Self="ParagraphStyle/Body" Name="Body" FontStyle="300" Composer="HL Composer">
      <Properties><AppliedFont type="string">Museo Sans</AppliedFont></Properties>
    </ParagraphStyle>
  </RootParagraphStyleGroup>
  <RootTableStyleGroup Self="uts">
    <TableStyle Self="TableStyle/Data" Name="Data"/>
  </RootTableStyleGroup>
</idPkg:Styles>
"""

PREFS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Preferences xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <DocumentPreference PageBinding="LeftToRight" FacingPages="false"/>
  <TextDefault Composer="HL Composer" Justification="LeftAlign"/>
</idPkg:Preferences>
"""

FONTS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Fonts xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <FontFamily Self="fam1" Name="Museo Sans">
    <Font Self="f1" FontFamily="Museo Sans" FontStyleName="300"/>
  </FontFamily>
</idPkg:Fonts>
"""

ENTRIES = {
    "mimetype": "application/vnd.adobe.indesign-idml-package",
    "designmap.xml": "<Document/>",
    "Spreads/Spread_spr.xml": SPREAD,
    "Stories/Story_u10.xml": STORY,
    "Resources/Styles.xml": STYLES,
    "Resources/Preferences.xml": PREFS,
    "Resources/Fonts.xml": FONTS,
}


class MapEngine(Engine):
    name = "fake"

    def __init__(self, mapping):
        self.mapping = mapping

    def translate(self, texts):
        return [self.mapping.get(t, t) for t in texts]


def _make_idml(path, **overrides):
    entries = dict(ENTRIES, **overrides)
    with zipfile.ZipFile(path, "w") as z:
        for name, data in entries.items():
            z.writestr(name, data)
    return path


def _convert(tmp_path, name="out.idml"):
    """Source and a full Arabic conversion of it, the way the pipeline does.

    `apply_rtl` mirrors the page's content, so the output has geometry that
    moved for the validator's per-object accounting to report.
    """
    from pagebirdy.idml import rtl

    src = _make_idml(str(tmp_path / "in.idml"))
    pkg = IdmlPackage(src)
    segs = pkg.segments()
    Translator(MapEngine({"Understanding Ratios": ARABIC}), None, None).run(segs)
    pkg.apply(segs, idml_font="Adobe Arabic", font_styles=("Regular", "Bold"))
    rtl.apply_rtl(pkg, document="in.idml", language="ar",
                  idml_font="Adobe Arabic", font_styles=("Regular", "Bold"))
    out = str(tmp_path / name)
    pkg.save(out)
    return src, out


def _rewrite(path, entry, mutate):
    """Copy a package, replacing one entry with `mutate(tree)`'s result."""
    with zipfile.ZipFile(path) as z:
        entries = {n: z.read(n) for n in z.namelist()}
    tree = etree.fromstring(entries[entry])
    mutate(tree)
    entries[entry] = etree.tostring(tree, xml_declaration=True, encoding="UTF-8")
    broken = path.replace(".idml", ".broken.idml")
    with zipfile.ZipFile(broken, "w") as z:
        for name, data in entries.items():
            z.writestr(name, data)
    return broken


# ---- a clean conversion passes ----------------------------------------------


def test_a_clean_arabic_conversion_reports_no_problems(tmp_path):
    src, out = _convert(tmp_path)
    report = validate_rtl_idml(src, out, "ar")
    assert report["problems"] == []
    assert report["ok"]


def test_the_structure_is_reported_as_unchanged(tmp_path):
    src, out = _convert(tmp_path)
    r = validate_rtl_idml(src, out, "ar")
    assert r["pages_source"] == r["pages_output"] == 1
    assert r["items_source"] == r["items_output"] == 2  # the frame and the rectangle
    assert r["entries_source"] == r["entries_output"]
    assert r["styles_source"] == r["styles_output"]


def test_the_conversion_is_reported_object_by_object(tmp_path):
    src, out = _convert(tmp_path)
    r = validate_rtl_idml(src, out, "ar")
    assert r["items_moved"] >= 1
    # apply_rtl never touches PageBinding -- text direction is carried by
    # StoryDirection/ParagraphDirection instead.
    assert r["page_binding"] == r["page_binding_source"] == "LeftToRight"
    assert r["runs_in_target_script"] == 1
    assert r["runs_pinned_ltr"] == 1          # the equation
    assert r["paragraphs_ltr"] == 0
    assert r["tables_ltr"] == 0               # the table style flipped too
    assert r["paragraphs_latin_composer"] == 0


def test_the_target_face_is_reported_as_registered(tmp_path):
    src, out = _convert(tmp_path)
    r = validate_rtl_idml(src, out, "ar")
    assert r["font_families_added"] == {"Adobe Arabic": ["Regular", "Bold"]}
    assert r["runs_naming_an_undeclared_face_count"] == 0
    assert r["runs_in_unrenderable_font_count"] == 0


def test_the_linked_artwork_is_reported_as_intact(tmp_path):
    src, out = _convert(tmp_path)
    r = validate_rtl_idml(src, out, "ar")
    assert r["links_source"] == r["links_output"] == 1
    assert r["links_lost"] == []


def test_the_report_renders_as_a_table(tmp_path):
    src, out = _convert(tmp_path)
    text = format_report(validate_rtl_idml(src, out, "ar"))
    assert "page binding" in text and "LeftToRight -> LeftToRight" in text
    assert "PROBLEMS: none" in text


# ---- each check catches its own failure -------------------------------------


def test_a_resized_object_is_caught(tmp_path):
    src, out = _convert(tmp_path)

    def widen(tree):
        for point in tree.iter("PathPointType"):
            if point.get("Anchor") == "200 50":
                point.set("Anchor", "300 50")
    r = validate_rtl_idml(src, _rewrite(out, "Spreads/Spread_spr.xml", widen), "ar")
    assert any("resized" in p for p in r["problems"])


def test_a_flipped_object_is_caught(tmp_path):
    """Negating `a` mirrors the item's *content* — the scaleX(-1) trap."""
    src, out = _convert(tmp_path)

    def flip(tree):
        frame = tree.find(".//TextFrame")
        frame.set("ItemTransform", "-1 0 0 1 100 -300")
    r = validate_rtl_idml(src, _rewrite(out, "Spreads/Spread_spr.xml", flip), "ar")
    assert any("matrix was altered" in p for p in r["problems"])


def test_an_object_that_drifted_vertically_is_caught(tmp_path):
    src, out = _convert(tmp_path)

    def drop(tree):
        frame = tree.find(".//TextFrame")
        t = frame.get("ItemTransform").split()
        frame.set("ItemTransform", " ".join(t[:5] + [str(float(t[5]) + 20)]))
    r = validate_rtl_idml(src, _rewrite(out, "Spreads/Spread_spr.xml", drop), "ar")
    assert any("vertically" in p for p in r["problems"])


def test_a_lost_object_is_caught(tmp_path):
    src, out = _convert(tmp_path)

    def delete(tree):
        frame = tree.find(".//TextFrame")
        frame.getparent().remove(frame)
    r = validate_rtl_idml(src, _rewrite(out, "Spreads/Spread_spr.xml", delete), "ar")
    assert any("page items lost" in p for p in r["problems"])


def test_a_lost_link_is_caught(tmp_path):
    src, out = _convert(tmp_path)

    def unlink(tree):
        link = tree.find(".//Link")
        link.getparent().remove(link)
    r = validate_rtl_idml(src, _rewrite(out, "Spreads/Spread_spr.xml", unlink), "ar")
    assert any("linked assets lost" in p for p in r["problems"])


def test_a_lost_style_is_caught(tmp_path):
    src, out = _convert(tmp_path)

    def drop_style(tree):
        style = tree.find(".//ParagraphStyle")
        style.getparent().remove(style)
    r = validate_rtl_idml(src, _rewrite(out, "Resources/Styles.xml", drop_style), "ar")
    assert any("styles lost" in p for p in r["problems"])


def test_a_paragraph_left_reading_left_to_right_is_caught(tmp_path):
    src, out = _convert(tmp_path)

    def unflip(tree):
        tree.find(".//ParagraphStyleRange").set(
            "ParagraphDirection", "LeftToRightDirection")
    r = validate_rtl_idml(src, _rewrite(out, "Stories/Story_u10.xml", unflip), "ar")
    assert any("read left to right" in p for p in r["problems"])


def test_a_paragraph_left_on_the_latin_composer_is_caught(tmp_path):
    src, out = _convert(tmp_path)

    def relatin(tree):
        tree.find(".//ParagraphStyleRange").set("Composer", "HL Composer")
    r = validate_rtl_idml(src, _rewrite(out, "Stories/Story_u10.xml", relatin), "ar")
    assert any("Latin composer" in p for p in r["problems"])


def test_arabic_set_in_a_latin_face_is_caught(tmp_path):
    """The missing-glyph-box check: Arabic in a face that has no Arabic."""
    src, out = _convert(tmp_path)

    def retype(tree):
        for font in tree.iter("AppliedFont"):
            font.text = "Museo Sans"
    r = validate_rtl_idml(src, _rewrite(out, "Stories/Story_u10.xml", retype), "ar")
    assert any("cannot draw it" in p for p in r["problems"])


def test_a_face_the_package_never_declares_is_caught(tmp_path):
    src, out = _convert(tmp_path)

    def unregister(tree):
        for fam in list(tree.iter("FontFamily")):
            if fam.get("Name") == "Adobe Arabic":
                fam.getparent().remove(fam)
    r = validate_rtl_idml(src, _rewrite(out, "Resources/Fonts.xml", unregister), "ar")
    assert any("never declares" in p for p in r["problems"])


def test_a_bleed_lapping_the_gutter_is_not_a_page_change():
    """The sidebar band: 78pt wide, 64.5 on its page and 13.5 of bleed. The
    mirror puts that bleed over the gutter, and it is still the same page's
    band -- reporting it would mean nudging it back, which pushes its inner
    edge over the content mirrored to sit beside it."""
    extents = [(-612.0, 0.0), (0.0, 612.0)]
    assert _same_page((547.5, 0, 625.5, 10), (-13.5, 0, 64.5, 10), extents)


def test_an_item_that_lands_mostly_on_the_facing_page_is_caught():
    """Problem 4 of page 12: a frame 92% on its page, mirrored 92% onto the
    facing one."""
    extents = [(-612.0, 0.0), (0.0, 612.0)]
    assert not _same_page((-576.0, 0, 47.5, 10), (-47.5, 0, 576.0, 10), extents)


def test_a_resized_page_is_caught(tmp_path):
    src, out = _convert(tmp_path)

    def resize(tree):
        tree.find(".//Page").set("GeometricBounds", "0 0 900 612")
    r = validate_rtl_idml(src, _rewrite(out, "Spreads/Spread_spr.xml", resize), "ar")
    assert any("page size changed" in p for p in r["problems"])


# ---- an LTR job is held to the opposite expectations ------------------------


def test_an_untouched_copy_passes_as_an_ltr_job(tmp_path):
    """Spanish must come out with its layout exactly as it went in."""
    src = _make_idml(str(tmp_path / "in.idml"))
    out = str(tmp_path / "out.idml")
    shutil.copy(src, out)
    r = validate_rtl_idml(src, out, "es")
    assert r["problems"] == []


def test_an_ltr_job_that_mirrored_anything_is_caught(tmp_path):
    """The regression guard for the LTR path: geometry must not move.

    An RTL conversion moves its content, so labelling that same output as
    an LTR job has to be caught.
    """
    src, out = _convert(tmp_path)
    r = validate_rtl_idml(src, out, "es")
    assert any("moved in an LTR job" in p for p in r["problems"])


def test_a_rebound_document_is_caught_regardless_of_direction(tmp_path):
    """PageBinding is never supposed to change -- checked unconditionally,
    not only for the direction a job happened to declare."""
    src, out = _convert(tmp_path)

    def rebind(tree):
        tree.find(".//DocumentPreference").set("PageBinding", "RightToLeft")
    r = validate_rtl_idml(src, _rewrite(out, "Resources/Preferences.xml", rebind), "ar")
    assert any("page binding changed" in p for p in r["problems"])


def test_validation_without_a_target_language_checks_structure_only(tmp_path):
    src, out = _convert(tmp_path)
    r = validate_rtl_idml(src, out)
    assert r["target_lang"] is None
    assert r["problems"] == []


# ---- the real books ---------------------------------------------------------

_SAMPLES = sorted(glob.glob(os.path.join(
    os.path.dirname(__file__), "..", "uploads", "*.idml")), key=os.path.getsize)


@pytest.mark.skipif(not _SAMPLES, reason="no sample IDML available")
def test_a_real_textbook_converts_without_breaking_a_guarantee(tmp_path,
                                                               monkeypatch):
    """End to end on a real book: translate, mirror, then check the file back.

    The engine is injected so the check sees a genuinely Arabic document —
    offline the identity engine hands the English back, and every script-aware
    decision in the pipeline would legitimately do nothing.
    """
    from pagebirdy import pipeline
    from pagebirdy.idml.package import IdmlPackage as _Pkg

    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY",
                "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(key, raising=False)

    class Arabic(Engine):
        name = "fake-arabic"

        def translate(self, texts):
            # Keep every placeholder; swap the prose. Anything with no letters
            # in it is content the engine would hand straight back.
            return [ARABIC + t[len(t.rstrip()):] if any(c.isalpha() for c in t)
                    else t for t in texts]

    monkeypatch.setattr(pipeline, "build_engines", lambda **kw: (Arabic(), None))

    report = pipeline.translate_idml(
        _SAMPLES[0], out_dir=str(tmp_path / "out"), tm_path=str(tmp_path / "tm.db"),
        review_db=None, target_lang="ar", with_graphics=False)

    assert report["validated"]
    assert report["validation_problems"] == [], report["validation_problems"]

    detail = validate_rtl_idml(_SAMPLES[0], report["output"], "ar")
    # Text direction and the typographic pass ran, and the page content
    # mirrored within its pages while template furniture stayed.
    # 335 is the real, measured count for this sample book -- not a bound.
    # (339 until the Family Letter page's own strip furniture stopped moving.)
    assert report["rtl_text_direction_set"] > 100
    assert detail["items_moved"] == 335
    assert detail["runs_in_target_script"] > 100
    assert detail["runs_in_unrenderable_font_count"] == 0
    assert detail["items_resized"] == []
    assert detail["items_reshaped"] == []
    assert detail["items_drifted_vertically"] == []
    assert detail["items_changed_page"] == []
    assert detail["links_lost"] == []
    assert detail["styles_lost"] == []

    del report, detail
    gc.collect()


@pytest.mark.skipif(not _SAMPLES, reason="no sample IDML available")
def test_a_real_textbook_translated_to_spanish_keeps_its_layout(tmp_path,
                                                                monkeypatch):
    """No regression on the LTR path: nothing moves, nothing is rebound."""
    from pagebirdy import pipeline

    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY",
                "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(key, raising=False)

    report = pipeline.translate_idml(
        _SAMPLES[0], out_dir=str(tmp_path / "out"), tm_path=str(tmp_path / "tm.db"),
        review_db=None, target_lang="es", with_graphics=False)

    r = validate_rtl_idml(_SAMPLES[0], report["output"], "es")
    assert r["items_moved"] == 0
    assert r["page_binding"] != "RightToLeft"
    assert r["problems"] == []

    del report, r
    gc.collect()
