import re
import zipfile

import pytest
from lxml import etree

from pagebirdy.idml.package import IdmlPackage
from pagebirdy.translate.engine import Engine
from pagebirdy.translate.translator import Translator

STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Understanding Ratios</Content>
      </CharacterStyleRange>
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Divide 3 by 4</Content>
      </CharacterStyleRange>
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">MathematicalPi LT Std</AppliedFont></Properties>
        <Content>&#189;</Content>
      </CharacterStyleRange>
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


def _make_idml(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr("Stories/Story_u10.xml", STORY)


def test_idml_roundtrip_translates_prose_preserves_math(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml(src)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    ids = {s.id: s for s in segs}
    assert len(segs) == 3

    # numeric run is value-visible; math run is opaque
    prose = next(s for s in segs if "Understanding" in s.source)
    numeric = next(s for s in segs if s.source.startswith("Divide"))
    math = next(s for s in segs if s.has_math_font)
    assert "⟦=3⟧" in numeric.source and "⟦=4⟧" in numeric.source
    assert not prose.has_math_font
    assert math.source == "⟦m0⟧"

    eng = MapEngine({
        "Understanding Ratios": "Comprender las razones",
        "Divide ⟦=3⟧ by ⟦=4⟧": "Divide ⟦=3⟧ entre ⟦=4⟧",
    })
    Translator(eng, None).run(segs)

    applied = pkg.apply(segs)
    assert applied == 2  # prose + numeric; math run left untouched

    out = str(tmp_path / "out.idml")
    pkg.save(out)

    with zipfile.ZipFile(out) as z:
        # mimetype must be first and stored uncompressed
        first = z.infolist()[0]
        assert first.filename == "mimetype"
        assert first.compress_type == zipfile.ZIP_STORED
        story = z.read("Stories/Story_u10.xml").decode("utf-8")

    assert "Comprender las razones" in story
    assert "Divide 3 entre 4" in story  # numeric token restored to digits
    assert "Understanding Ratios" not in story
    assert "½" in story  # ½ math run untouched


def test_idml_reopen_is_stable(tmp_path):
    # Saving an untranslated package must not corrupt it (re-extractable).
    src = str(tmp_path / "in.idml")
    _make_idml(src)
    pkg = IdmlPackage(src)
    out = str(tmp_path / "copy.idml")
    pkg.save(out)
    assert len(IdmlPackage(out).segments()) == 3


STORY_NO_PROPERTIES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u20">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange>
        <Content>Essentials</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


STORY_WITH_PREFERENCE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u30" AppliedTOCStyle="n">
    <StoryPreference OpticalMarginAlignment="false" OpticalMarginSize="12"
        FrameType="TextFrameType" StoryOrientation="Horizontal"
        StoryDirection="LeftToRightDirection"/>
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Understanding Ratios</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


def _make_idml_from(path, story_xml, story_name="Stories/Story_u10.xml"):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr(story_name, story_xml)


def test_apply_overrides_applied_font_when_idml_font_given(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml(src)  # uses module-level STORY: Minion Pro runs + a math run

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    eng = MapEngine({
        "Understanding Ratios": "理解比率",
        "Divide ⟦=3⟧ by ⟦=4⟧": "用 ⟦=3⟧ 除以 ⟦=4⟧",
    })
    Translator(eng, None).run(segs)

    applied = pkg.apply(segs, idml_font="Noto Sans SC")
    assert applied == 2  # prose + numeric; math run untouched, same as before

    out = str(tmp_path / "out.idml")
    pkg.save(out)

    with zipfile.ZipFile(out) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    # Both translated runs now carry the override font.
    assert story.count("<AppliedFont type=\"string\">Noto Sans SC</AppliedFont>") == 2
    # The math run's original font is untouched.
    assert "MathematicalPi LT Std" in story


def test_apply_leaves_applied_font_untouched_when_idml_font_none(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml(src)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    eng = MapEngine({"Understanding Ratios": "Comprender las razones"})
    Translator(eng, None).run(segs)

    pkg.apply(segs)  # default idml_font=None — today's behavior
    out = str(tmp_path / "out.idml")
    pkg.save(out)

    with zipfile.ZipFile(out) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert "<AppliedFont type=\"string\">Minion Pro</AppliedFont>" in story


def test_translate_idml_passes_idml_font_for_chinese(tmp_path, monkeypatch):
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY", "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    from pagebirdy.pipeline import translate_idml

    # The target face goes only onto runs whose translation has letters a Latin
    # font cannot carry, so the engine has to actually return Chinese.
    eng = MapEngine({"Understanding Ratios": "理解比率"})
    monkeypatch.setattr("pagebirdy.pipeline.build_engines", lambda **_kw: (eng, None))

    src = str(tmp_path / "in.idml")
    _make_idml(src)  # module-level STORY fixture: Minion Pro prose + numeric + math runs

    report = translate_idml(src, out_dir=str(tmp_path / "out"),
                             review_db=None,
                             target_lang="zh")

    with zipfile.ZipFile(report["output"]) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert "<AppliedFont type=\"string\">Noto Sans SC</AppliedFont>" in story
    # Math run's original font is untouched regardless of target language.
    assert "MathematicalPi LT Std" in story


def test_translate_idml_leaves_applied_font_alone_for_spanish(tmp_path, monkeypatch):
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY", "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    from pagebirdy.pipeline import translate_idml

    src = str(tmp_path / "in.idml")
    _make_idml(src)

    report = translate_idml(src, out_dir=str(tmp_path / "out"),
                             review_db=None,
                             target_lang="es")

    with zipfile.ZipFile(report["output"]) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert "<AppliedFont type=\"string\">Minion Pro</AppliedFont>" in story


def test_translate_idml_logs_stage_progress(tmp_path, monkeypatch, caplog):
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY", "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    import logging

    from pagebirdy.pipeline import translate_idml

    src = str(tmp_path / "in.idml")
    _make_idml(src)

    with caplog.at_level(logging.INFO, logger="pagebirdy.pipeline"):
        report = translate_idml(src, out_dir=str(tmp_path / "out"),
                                 review_db=None,
                                 target_lang="es")

    messages = [r.message for r in caplog.records]
    assert any("in.idml" in m and "es" in m for m in messages)  # start
    assert any("3 run" in m for m in messages)  # ingest: 3 runs in STORY fixture
    assert any("translat" in m.lower() for m in messages)  # translate stage
    assert any(report["output"] in m for m in messages)  # save/output stage




def test_apply_creates_properties_and_applied_font_when_missing(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_from(src, STORY_NO_PROPERTIES)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    assert len(segs) == 1
    eng = MapEngine({"Essentials": "必备品"})
    Translator(eng, None).run(segs)

    applied = pkg.apply(segs, idml_font="Noto Sans SC")
    assert applied == 1

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert "<AppliedFont type=\"string\">Noto Sans SC</AppliedFont>" in story
    assert "必备品" in story


def _path_geometry(x1: float, y1: float, x2: float, y2: float) -> str:
    """The `<PathPointType Anchor>` block a real IDML item carries — the
    item's own outline in ITS OWN local coordinates, which mirroring
    transforms to find the item's spread-space center."""
    pts = ((x1, y1), (x1, y2), (x2, y2), (x2, y1))
    anchors = "".join(f'<PathPointType Anchor="{x} {y}" '
                      f'LeftDirection="{x} {y}" RightDirection="{x} {y}"/>'
                      for x, y in pts)
    return ("<Properties><PathGeometry><GeometryPathType PathOpen=\"false\">"
            f"<PathPointArray>{anchors}</PathPointArray>"
            "</GeometryPathType></PathGeometry></Properties>")


SPREAD_SIMPLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="us1">
    <Page Self="up1" GeometricBounds="0 0 100 300" ItemTransform="1 0 0 1 0 0"/>
    <TextFrame Self="uf1" ParentStory="u10" ItemTransform="1 0 0 1 20 20">GEOM_F</TextFrame>
  </Spread>
</idPkg:Spread>
""".replace("GEOM_F", _path_geometry(-20, -10, 20, 10))


def _make_idml_with_spread(path, spread_xml=SPREAD_SIMPLE, story_xml=STORY,
                           master_spread_xml=None):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr("Spreads/Spread_us1.xml", spread_xml)
        if master_spread_xml is not None:
            z.writestr("MasterSpreads/MasterSpread_us1.xml", master_spread_xml)
        z.writestr("Stories/Story_u10.xml", story_xml)


def test_spread_survives_save_roundtrip_untouched(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_with_spread(src)

    pkg = IdmlPackage(src)
    out = str(tmp_path / "out.idml")
    pkg.save(out)

    with zipfile.ZipFile(out) as z:
        spread = z.read("Spreads/Spread_us1.xml").decode("utf-8")
    assert 'ItemTransform="1 0 0 1 20 20"' in spread
    assert 'GeometricBounds="0 0 100 300"' in spread


def test_spread_with_embedded_image_over_10mb_text_node_parses(tmp_path):
    # InDesign stores embedded images as base64 in one <Contents> text node;
    # past libxml2's 10 MB default cap this raised "Text node too long, try
    # XML_PARSE_HUGE" in production.
    big = "A" * (11 * 1024 * 1024)
    spread = SPREAD_SIMPLE.replace(
        "</Spread>",
        f'<Rectangle Self="ur1"><Image Self="ui1"><Properties>'
        f"<Contents><![CDATA[{big}]]></Contents></Properties></Image></Rectangle>"
        "</Spread>")
    src = str(tmp_path / "in.idml")
    _make_idml_with_spread(src, spread_xml=spread)

    pkg = IdmlPackage(src)
    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        assert big in z.read("Spreads/Spread_us1.xml").decode("utf-8")


# ---- linked-graphic relinking (regression: the Spread/MasterSpread trees are
# the sole save-time source of truth, so a byte-level patch is discarded) -----

SPREAD_WITH_LINK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="us1">
    <Page Self="up1" GeometricBounds="0 0 100 300" ItemTransform="1 0 0 1 0 0"/>
    <Rectangle Self="ur9" ItemTransform="1 0 0 1 20 20">
      <EPS Self="ue9" ItemTransform="1 0 0 1 0 0">
        <Link Self="ul9" LinkResourceURI="file:/Links/say.ai"/>
      </EPS>
    </Rectangle>
  </Spread>
</idPkg:Spread>
"""

MASTER_SPREAD_WITH_LINK = (SPREAD_WITH_LINK.replace("Spread", "MasterSpread")
                           .replace('Self="us1"', 'Self="um1"')
                           .replace("file:/Links/say.ai", "file:/Links/go.ai"))


def test_relink_rewrites_spread_and_master_spread_links_through_save(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_with_spread(src, spread_xml=SPREAD_WITH_LINK,
                           master_spread_xml=MASTER_SPREAD_WITH_LINK)

    pkg = IdmlPackage(src)
    count = pkg.relink({"file:/Links/say.ai": "file:/out/say_ar.ai",
                        "file:/Links/go.ai": "file:/out/go_ar.ai"})
    assert count == 2

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        spread = z.read("Spreads/Spread_us1.xml").decode("utf-8")
        master = z.read("MasterSpreads/MasterSpread_us1.xml").decode("utf-8")
    assert 'LinkResourceURI="file:/out/say_ar.ai"' in spread
    assert "file:/Links/say.ai" not in spread
    assert 'LinkResourceURI="file:/out/go_ar.ai"' in master
    assert "file:/Links/go.ai" not in master


def test_relink_rewrites_inline_story_links(tmp_path):
    story = STORY.replace(
        "<Content>Understanding Ratios</Content>",
        "<Content>Understanding Ratios</Content>"
        '<Rectangle Self="ur1"><EPS Self="ue1">'
        '<Link Self="ul1" LinkResourceURI="file:/Links/say.ai"/></EPS></Rectangle>',
    )
    src = str(tmp_path / "in.idml")
    _make_idml_with_spread(src, spread_xml=SPREAD_SIMPLE, story_xml=story)

    pkg = IdmlPackage(src)
    assert pkg.relink({"file:/Links/say.ai": "file:/out/say_ar.ai"}) == 1

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        story_out = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert 'LinkResourceURI="file:/out/say_ar.ai"' in story_out
    assert "file:/Links/say.ai" not in story_out


def test_relink_counts_a_graphic_placed_twice_once(tmp_path):
    """`graphics_translated` in the QA report counts DISTINCT graphics — the
    same word-art is commonly placed on several spreads."""
    src = str(tmp_path / "in.idml")
    _make_idml_with_spread(
        src, spread_xml=SPREAD_WITH_LINK,
        master_spread_xml=SPREAD_WITH_LINK.replace("Spread", "MasterSpread"))

    pkg = IdmlPackage(src)
    assert pkg.relink({"file:/Links/say.ai": "file:/out/say_ar.ai"}) == 1


# ---- equation assemblies (hand-built fractions) -----------------------------

ASSEMBLY_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body" PointSize="12">
      <CharacterStyleRange PointSize="12">
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>The ratio is </Content>
      </CharacterStyleRange>
      <CharacterStyleRange PointSize="12">
        <Properties><AppliedFont type="string">MathematicalPi LT Std</AppliedFont></Properties>
        <Content>2</Content>
      </CharacterStyleRange>
      <CharacterStyleRange PointSize="12" BaselineShift="5.2625" HorizontalScale="90">
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont><Leading type="unit">14</Leading></Properties>
        <Content>5.4</Content>
      </CharacterStyleRange>
      <CharacterStyleRange PointSize="12" Tracking="-1000" HorizontalScale="260">
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content> </Content>
      </CharacterStyleRange>
      <CharacterStyleRange PointSize="12" BaselineShift="-6.1867" HorizontalScale="88">
        <Properties><AppliedFont type="string">MathematicalPi LT Std</AppliedFont></Properties>
        <Content>.....</Content>
      </CharacterStyleRange>
      <CharacterStyleRange PointSize="8" BaselineShift="-6.0068" Position="Superscript" UnderlineOffset="2" UnderlineWeight="0.5">
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont><Leading type="enumeration">Auto</Leading></Properties>
        <Content>1,000</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body" PointSize="12">
      <CharacterStyleRange PointSize="12">
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Plain prose with </Content>
      </CharacterStyleRange>
      <CharacterStyleRange PointSize="12">
        <Properties><AppliedFont type="string">MathematicalPi LT Std</AppliedFont></Properties>
        <Content>&#189;</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


def _assembly_pkg(tmp_path, delta=3.0):
    src = str(tmp_path / "in.idml")
    _make_idml_from(src, ASSEMBLY_STORY)
    pkg = IdmlPackage(src)
    segs = pkg.segments()
    for s in segs:
        if not s.has_math_font:
            s.target = s.source
            s.status = "translated"
    pkg.apply(segs, size_delta=delta)
    return pkg, segs


def _runs(pkg):
    tree = pkg._stories["Stories/Story_u10.xml"]
    paras = [p for p in tree.iter() if p.tag == "ParagraphStyleRange"]
    return [[r for r in p if r.tag == "CharacterStyleRange"] for p in paras]


def test_assembly_paragraph_scales_every_run_by_one_ratio(tmp_path):
    pkg, _ = _assembly_pkg(tmp_path, delta=3.0)
    assembly, _prose = _runs(pkg)
    ratio = 9.0 / 12.0
    # Every run — prose, math glyph, spacer, rule, superscript — same ratio.
    sizes = [float(r.get("PointSize")) for r in assembly]
    assert sizes == pytest.approx([12 * ratio] * 5 + [8 * ratio])
    # Absolute-point attributes follow the ratio.
    # Written to 4 decimals, the precision InDesign itself uses.
    assert float(assembly[2].get("BaselineShift")) == pytest.approx(5.2625 * ratio, abs=1e-4)
    assert float(assembly[4].get("BaselineShift")) == pytest.approx(-6.1867 * ratio, abs=1e-4)
    assert float(assembly[5].get("BaselineShift")) == pytest.approx(-6.0068 * ratio, abs=1e-4)
    assert float(assembly[5].get("UnderlineOffset")) == pytest.approx(2 * ratio)
    assert float(assembly[5].get("UnderlineWeight")) == pytest.approx(0.5 * ratio)
    # Non-numeric Position enum is left alone.
    assert assembly[5].get("Position") == "Superscript"


def test_assembly_leaves_em_relative_and_percentage_attributes_alone(tmp_path):
    pkg, _ = _assembly_pkg(tmp_path)
    assembly, _ = _runs(pkg)
    assert assembly[3].get("Tracking") == "-1000"
    assert assembly[3].get("HorizontalScale") == "260"
    assert assembly[2].get("HorizontalScale") == "90"


def test_assembly_scales_numeric_leading_but_not_auto(tmp_path):
    pkg, _ = _assembly_pkg(tmp_path, delta=3.0)
    assembly, _ = _runs(pkg)
    leading = [c for c in assembly[2].find("Properties") if c.tag == "Leading"][0]
    assert float(leading.text) == pytest.approx(14 * 0.75)
    auto = [c for c in assembly[5].find("Properties") if c.tag == "Leading"][0]
    assert auto.text == "Auto"


def test_standalone_math_glyph_outside_assembly_is_untouched(tmp_path):
    pkg, _ = _assembly_pkg(tmp_path, delta=3.0)
    _, prose = _runs(pkg)
    assert prose[0].get("PointSize") == "9.00"   # existing flat shrink
    assert prose[1].get("PointSize") == "12"     # math glyph: never resized


def test_assembly_scaling_is_idempotent_across_reapply(tmp_path):
    pkg, segs = _assembly_pkg(tmp_path, delta=3.0)
    before = [r.get("PointSize") for r in _runs(pkg)[0]]
    pkg.apply(segs, size_delta=3.0)
    assert [r.get("PointSize") for r in _runs(pkg)[0]] == before


def test_assembly_never_drives_a_run_below_floor(tmp_path):
    pkg, _ = _assembly_pkg(tmp_path, delta=8.0)  # 12 -> 4 would put the 8pt run at 2.67
    assembly, _ = _runs(pkg)
    sizes = [float(r.get("PointSize")) for r in assembly]
    assert min(sizes) >= 4.0
    # Still one ratio: the 8pt run sits at floor, the 12pt runs at 12 * (4/8).
    assert sizes == pytest.approx([6.0] * 5 + [4.0])


def test_assembly_text_is_untouched(tmp_path):
    pkg, _ = _assembly_pkg(tmp_path)
    assembly, _ = _runs(pkg)
    assert [r.find("Content").text for r in assembly] == \
        ["The ratio is ", "2", "5.4", " ", ".....", "1,000"]


# ---- font resolution through named styles -----------------------------------

STYLES_MATHPI = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <RootCharacterStyleGroup Self="u7f">
    <CharacterStyle Self="CharacterStyle/$ID/[No character style]" Name="$ID/[No character style]"/>
    <CharacterStyle Self="CharacterStyle/MathPi base" Name="MathPi base">
      <Properties><AppliedFont type="string">Mathematical Pi LT Std</AppliedFont></Properties>
    </CharacterStyle>
    <CharacterStyle Self="CharacterStyle/MathPi 1" Name="MathPi 1" BasedOn="CharacterStyle/MathPi base"/>
  </RootCharacterStyleGroup>
  <RootParagraphStyleGroup Self="u80">
    <ParagraphStyle Self="ParagraphStyle/$ID/[No paragraph style]" Name="$ID/[No paragraph style]" PointSize="12"/>
    <ParagraphStyle Self="ParagraphStyle/Body" Name="Body" BasedOn="ParagraphStyle/$ID/[No paragraph style]">
      <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
    </ParagraphStyle>
    <ParagraphStyle Self="ParagraphStyle/EqLine" Name="EqLine">
      <Properties><AppliedFont type="string">Mathematical Pi LT Std</AppliedFont></Properties>
    </ParagraphStyle>
  </RootParagraphStyleGroup>
</idPkg:Styles>
"""

STYLED_MATH_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">
        <Content>Solve </Content>
      </CharacterStyleRange>
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/MathPi 1">
        <Content>5</Content>
      </CharacterStyleRange>
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/MathPi 1">
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>7</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/EqLine">
      <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">
        <Content>3</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


def _make_idml_with_styles(path, story_xml, styles_xml):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr("Resources/Styles.xml", styles_xml)
        z.writestr("Stories/Story_u10.xml", story_xml)


def test_font_resolves_through_character_style_based_on_chain(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_with_styles(src, STYLED_MATH_STORY, STYLES_MATHPI)
    segs = IdmlPackage(src).segments()
    by_text = {s.placeholders.get(s.source, s.source): s for s in segs}
    # "5" styled via MathPi 1 -> BasedOn MathPi base -> Mathematical Pi: a glyph.
    five = next(s for s in segs if s.font.startswith("Mathematical"))
    assert five.has_math_font
    assert five.source.startswith("⟦m")
    # Prose run with no font anywhere but the paragraph style: not math.
    prose = next(s for s in segs if s.source.startswith("Solve"))
    assert prose.font == "Minion Pro"
    assert not prose.has_math_font


def test_inline_applied_font_wins_over_character_style(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_with_styles(src, STYLED_MATH_STORY, STYLES_MATHPI)
    segs = IdmlPackage(src).segments()
    seven = next(s for s in segs if "7" in s.source or s.source == "⟦=7⟧")
    assert seven.font == "Minion Pro"
    assert not seven.has_math_font


def test_font_falls_back_to_paragraph_style_when_character_style_silent(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_with_styles(src, STYLED_MATH_STORY, STYLES_MATHPI)
    segs = IdmlPackage(src).segments()
    three = [s for s in segs if s.has_math_font]
    # Both "5" (character style) and "3" (paragraph style EqLine) are math.
    assert len(three) == 2
    assert all(s.font == "Mathematical Pi LT Std" for s in three)


def test_font_without_styles_xml_still_reads_inline_font(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml(src)  # module-level STORY, no Resources/Styles.xml
    segs = IdmlPackage(src).segments()
    assert [s.font for s in segs] == ["Minion Pro", "Minion Pro", "MathematicalPi LT Std"]


# ---- embedded markers (<?ACE 7?> Indent To Here, etc.) ----------------------

MARKER_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content><?ACE 7?>Look at the shapes: which one is round?</Content>
      </CharacterStyleRange>
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>1.\t<?ACE 7?>Count the dots.</Content>
      </CharacterStyleRange>
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>First<?ACE 8?>Second<?ACE 7?>Third</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


def _marker_pkg(tmp_path, targets):
    src = str(tmp_path / "in.idml")
    _make_idml_from(src, MARKER_STORY)
    pkg = IdmlPackage(src)
    segs = pkg.segments()
    for s, t in zip(segs, targets):
        s.target = t
        s.status = "translated"
    pkg.apply(segs)
    return pkg, segs


def _content_xml(pkg):
    tree = pkg._stories["Stories/Story_u10.xml"]
    out = []
    for c in tree.iter():
        if c.tag == "Content":
            xml = etree.tostring(c, encoding="unicode").strip()
            out.append(re.sub(r"<Content[^>]*>", "<Content>", xml, count=1))
    return out


def test_text_after_embedded_marker_reaches_the_segment(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_from(src, MARKER_STORY)
    segs = IdmlPackage(src).segments()
    assert len(segs) == 3
    assert segs[0].source == "Look at the shapes: which one is round?"
    assert segs[1].source == "⟦=1⟧.\tCount the dots."
    assert segs[2].source == "FirstSecondThird"


def test_marker_at_start_of_run_stays_at_start(tmp_path):
    pkg, _ = _marker_pkg(tmp_path, [
        "Mira las formas: ¿cuál es redonda?", "1.\tCuenta los puntos.", "UnoDosTres"])
    assert _content_xml(pkg)[0] == "<Content><?ACE 7?>Mira las formas: ¿cuál es redonda?</Content>"


def test_marker_follows_its_list_number_prefix(tmp_path):
    pkg, _ = _marker_pkg(tmp_path, [
        "Mira las formas.", "⟦=1⟧.\tCuenta los puntos.", "UnoDosTres"])
    assert _content_xml(pkg)[1] == "<Content>1.\t<?ACE 7?>Cuenta los puntos.</Content>"


def test_multiple_markers_keep_order_and_fall_back_proportionally(tmp_path):
    # Prefixes "First"/"Second" do not survive translation: fall back to the
    # marker's proportional position rather than stranding it at the end.
    pkg, _ = _marker_pkg(tmp_path, ["Mira.", "1.\tCuenta.", "UnoDosTres"])
    xml = _content_xml(pkg)[2]
    assert xml.index("<?ACE 8?>") < xml.index("<?ACE 7?>")
    assert not xml.endswith("<?ACE 7?></Content>")
    assert xml.startswith("<Content>Uno")


def test_markers_survive_save_roundtrip(tmp_path):
    pkg, _ = _marker_pkg(tmp_path, ["Mira.", "1.\tCuenta.", "UnoDosTres"])
    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert story.count("<?ACE 7?>") == 3
    assert story.count("<?ACE 8?>") == 1
    assert "Look at the shapes" not in story


def test_untranslated_marker_run_is_left_byte_identical(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_from(src, MARKER_STORY)
    pkg = IdmlPackage(src)
    segs = pkg.segments()
    pkg.apply(segs)  # nothing translated
    assert _content_xml(pkg)[2] == "<Content>First<?ACE 8?>Second<?ACE 7?>Third</Content>"


# ---- frame auto-sizing for translated stories -------------------------------

_TFP_OFF = ('<TextFramePreference TextColumnCount="1" AutoSizingType="Off" '
            'AutoSizingReferencePoint="CenterPoint" '
            'UseMinimumHeightForAutoSizing="false" MinimumHeightForAutoSizing="0"/>')

AUTOSIZE_SPREAD = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="us1">
    <Page Self="up1" GeometricBounds="0 0 400 300" ItemTransform="1 0 0 1 0 0"/>
    <TextFrame Self="uf1" ParentStory="u10" ItemTransform="1 0 0 1 20 20">GEOM_A TFP</TextFrame>
    <TextFrame Self="uf2" ParentStory="u99" ItemTransform="1 0 0 1 20 120">GEOM_A TFP</TextFrame>
    <TextFrame Self="uf3" ParentStory="u10" ItemTransform="1 0 0 1 20 220">GEOM_A <TextFramePreference AutoSizingType="WidthAndHeight" AutoSizingReferencePoint="BottomLeftPoint" UseMinimumHeightForAutoSizing="true" MinimumHeightForAutoSizing="7"/></TextFrame>
    <TextFrame Self="uf4" ParentStory="u10" ItemTransform="1 0 0 1 20 320">GEOM_A</TextFrame>
  </Spread>
</idPkg:Spread>
""".replace("GEOM_A", _path_geometry(-50, -30, 50, 30)).replace("TFP", _TFP_OFF)

AUTOSIZE_MASTER = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:MasterSpread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <MasterSpread Self="um1">
    <Page Self="ump1" GeometricBounds="0 0 400 300" ItemTransform="1 0 0 1 0 0"/>
    <TextFrame Self="umf1" ParentStory="u10" ItemTransform="1 0 0 1 20 20">GEOM_A TFP</TextFrame>
  </MasterSpread>
</idPkg:MasterSpread>
""".replace("GEOM_A", _path_geometry(-50, -30, 50, 30)).replace("TFP", _TFP_OFF)

# Story u10 (translated) carries an anchored frame whose own story is u20.
ANCHORED_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u10">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Understanding Ratios</Content>
      </CharacterStyleRange>
      <CharacterStyleRange>
        <TextFrame Self="uaf1" ParentStory="u20" ItemTransform="1 0 0 1 0 0">GEOM_B TFP</TextFrame>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
""".replace("GEOM_B", _path_geometry(0, 0, 80, 40)).replace("TFP", _TFP_OFF)

CALLOUT_STORY = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u20">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Try it</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


def _autosize_pkg(tmp_path, translate_u20=False):
    src = str(tmp_path / "in.idml")
    with zipfile.ZipFile(src, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr("Spreads/Spread_us1.xml", AUTOSIZE_SPREAD)
        z.writestr("MasterSpreads/MasterSpread_um1.xml", AUTOSIZE_MASTER)
        z.writestr("Stories/Story_u10.xml", ANCHORED_STORY)
        z.writestr("Stories/Story_u20.xml", CALLOUT_STORY)
    pkg = IdmlPackage(src)
    segs = pkg.segments()
    for s in segs:
        if s.id.startswith("Story_u20") and not translate_u20:
            continue
        s.target = s.source + " (es)"
        s.status = "translated"
    pkg.apply(segs)
    return pkg


def _frame_prefs(pkg):
    out = {}
    for trees in (pkg._spreads, pkg._master_spreads, pkg._stories):
        for tree in trees.values():
            for tf in tree.iter():
                if tf.tag != "TextFrame":
                    continue
                tfp = next((c for c in tf if c.tag == "TextFramePreference"), None)
                out[tf.get("Self")] = dict(tfp.attrib) if tfp is not None else None
    return out


def test_autosize_grows_frames_of_rewritten_story_height_only(tmp_path):
    prefs = _frame_prefs(_autosize_pkg(tmp_path))
    f = prefs["uf1"]
    assert f["AutoSizingType"] == "HeightOnly"
    assert f["AutoSizingReferencePoint"] == "TopLeftPoint"
    assert f["UseMinimumHeightForAutoSizing"] == "true"
    assert float(f["MinimumHeightForAutoSizing"]) == 60.0  # frame's drawn height
    assert f["TextColumnCount"] == "1"  # other prefs untouched


def test_autosize_leaves_untouched_story_frames_alone(tmp_path):
    prefs = _frame_prefs(_autosize_pkg(tmp_path))
    assert prefs["uf2"] == dict(
        TextColumnCount="1", AutoSizingType="Off", AutoSizingReferencePoint="CenterPoint",
        UseMinimumHeightForAutoSizing="false", MinimumHeightForAutoSizing="0")


def test_autosize_leaves_designer_auto_sized_frames_alone(tmp_path):
    prefs = _frame_prefs(_autosize_pkg(tmp_path))
    assert prefs["uf3"]["AutoSizingType"] == "WidthAndHeight"
    assert prefs["uf3"]["MinimumHeightForAutoSizing"] == "7"


def test_autosize_creates_preference_when_frame_has_none(tmp_path):
    prefs = _frame_prefs(_autosize_pkg(tmp_path))
    assert prefs["uf4"]["AutoSizingType"] == "HeightOnly"
    assert float(prefs["uf4"]["MinimumHeightForAutoSizing"]) == 60.0


def test_autosize_covers_master_spread_frames(tmp_path):
    prefs = _frame_prefs(_autosize_pkg(tmp_path))
    assert prefs["umf1"]["AutoSizingType"] == "HeightOnly"


def test_autosize_anchored_frame_follows_its_own_story(tmp_path):
    # Anchored frame lives in story u10's XML but holds story u20.
    assert _frame_prefs(_autosize_pkg(tmp_path))["uaf1"]["AutoSizingType"] == "Off"
    prefs = _frame_prefs(_autosize_pkg(tmp_path, translate_u20=True))
    assert prefs["uaf1"]["AutoSizingType"] == "HeightOnly"
    assert float(prefs["uaf1"]["MinimumHeightForAutoSizing"]) == 40.0


def test_autosize_never_moves_or_widens_a_frame(tmp_path):
    pkg = _autosize_pkg(tmp_path)
    tree = pkg._spreads["Spreads/Spread_us1.xml"]
    tf = next(e for e in tree.iter() if e.get("Self") == "uf1")
    assert tf.get("ItemTransform") == "1 0 0 1 20 20"
    assert "MinimumWidthForAutoSizing" not in _frame_prefs(pkg)["uf1"]
    anchors = [pp.get("Anchor") for pp in tf.iter() if pp.tag == "PathPointType"]
    assert anchors == ["-50 -30", "-50 30", "50 30", "50 -30"]


def test_autosize_is_idempotent_across_reapply(tmp_path):
    pkg = _autosize_pkg(tmp_path)
    before = _frame_prefs(pkg)
    segs = pkg.segments()
    for s in segs:
        if s.id.startswith("Story_u10"):
            s.target, s.status = s.source, "translated"
    pkg.apply(segs)
    assert _frame_prefs(pkg) == before
