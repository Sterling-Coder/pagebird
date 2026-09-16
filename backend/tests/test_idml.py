import zipfile

import pytest
from lxml import etree

from pagebirdy.idml.package import IdmlPackage, _reflect_transform, _page_ranges, _mirror_spread
from pagebirdy.pipeline import regenerate_idml_from_review
from pagebirdy.review.store import ReviewStore
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


def test_regenerate_idml_from_review_applies_post_export_approval(tmp_path):
    """A segment that failed the integrity gate at export time (needs_human,
    target=None) is left English in the saved .idml, by design, pending human
    review. Once a reviewer approves a fix through ReviewStore.update_segment,
    the saved .idml must be brought up to date on next download — that's what
    regenerate_idml_from_review does. Without it, the approval is stuck in the
    review DB and the shipped file still reads English."""
    src = str(tmp_path / "in.idml")
    _make_idml(src)  # 3 runs: "Understanding Ratios" prose, "Divide 3 by 4" numeric, math

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    prose = next(s for s in segs if "Understanding" in s.source)
    numeric = next(s for s in segs if s.source.startswith("Divide"))

    # Simulate the initial MT pass: prose translated fine, numeric failed the
    # integrity gate (e.g. a chunk API failure) and is left untranslated.
    prose.target, prose.status, prose.engine = "Comprendiendo razones", "translated", "fake"
    numeric.target, numeric.status, numeric.engine = None, "needs_human", "fake"

    applied = pkg.apply(segs)
    assert applied == 1  # only prose written; numeric skipped (target is None)
    out = str(tmp_path / "out" / "in.es.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert "Comprendiendo razones" in story
    assert "Divide 3 by 4" in story  # still English

    # Reviewer fixes the numeric segment in the UI and approves it.
    review_db = str(tmp_path / "review.db")
    store = ReviewStore(review_db)
    job_id = store.save_job(src, out, segs, {"format": "idml", "target_lang": "es"})
    res = store.update_segment(job_id, numeric.id, "Divide ⟦=3⟧ entre ⟦=4⟧", approve=True)
    assert res["status"] == "approved"
    store.close()

    job = {"id": job_id, "source": src, "output": out,
           "meta": {"format": "idml", "target_lang": "es"}}
    regenerate_idml_from_review(job, review_db=review_db)

    with zipfile.ZipFile(out) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert "Divide 3 entre 4" in story  # approved fix now reached the file
    assert "Divide 3 by 4" not in story
    assert "Comprendiendo razones" in story  # earlier translated run preserved
    assert "½" in story  # math run still untouched


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


def test_apply_flips_story_direction_for_rtl(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_from(src, STORY_WITH_PREFERENCE)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    eng = MapEngine({"Understanding Ratios": "فهم النسب"})
    Translator(eng, None).run(segs)

    pkg.apply(segs, idml_font="Noto Sans Arabic", direction="rtl")

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert 'StoryDirection="RightToLeftDirection"' in story
    assert "فهم النسب" in story


def test_apply_leaves_story_direction_alone_for_ltr(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_from(src, STORY_WITH_PREFERENCE)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    Translator(MapEngine({}), None).run(segs)
    pkg.apply(segs)  # no direction kwarg — the default, same as every non-RTL call site

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert 'StoryDirection="LeftToRightDirection"' in story


STORY_TWO_RUNS_ONE_PARAGRAPH = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u40">
    <StoryPreference StoryDirection="LeftToRightDirection"/>
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Understanding </Content>
      </CharacterStyleRange>
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Ratios</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
"""


def test_apply_flips_justification_once_for_shared_paragraph(tmp_path):
    """Two runs in the same paragraph must not get the justification flipped
    twice (Left -> Right -> Left, silently wrong)."""
    src = str(tmp_path / "in.idml")
    _make_idml_from(src, STORY_TWO_RUNS_ONE_PARAGRAPH)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    assert len(segs) == 2
    eng = MapEngine({"Understanding": "فهم", "Ratios": "النسب"})
    Translator(eng, None).run(segs)

    pkg.apply(segs, idml_font="Noto Sans Arabic", direction="rtl")

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert story.count('Justification="RightAlign"') == 1
    assert 'Justification="LeftAlign"' not in story


def test_apply_leaves_center_justification_alone_for_rtl(tmp_path):
    story = STORY_TWO_RUNS_ONE_PARAGRAPH.replace(
        'AppliedParagraphStyle="ParagraphStyle/Body"',
        'AppliedParagraphStyle="ParagraphStyle/Body" Justification="CenterAlign"',
    )
    src = str(tmp_path / "in.idml")
    _make_idml_from(src, story)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    Translator(MapEngine({}), None).run(segs)
    pkg.apply(segs, direction="rtl")

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        result = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert 'Justification="CenterAlign"' in result


def _make_idml_with_preferences(path, story_xml, page_binding="LeftToRight"):
    prefs = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<idPkg:Preferences xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging">'
        f'<DocumentPreference PageBinding="{page_binding}"/>'
        "</idPkg:Preferences>"
    )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr("Resources/Preferences.xml", prefs)
        z.writestr("Stories/Story_u10.xml", story_xml)


def test_apply_flips_page_binding_for_rtl(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_with_preferences(src, STORY)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    Translator(MapEngine({}), None).run(segs)
    pkg.apply(segs, direction="rtl")

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        prefs = z.read("Resources/Preferences.xml").decode("utf-8")
    assert 'PageBinding="RightToLeft"' in prefs


def test_apply_leaves_page_binding_alone_for_ltr(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_with_preferences(src, STORY)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    Translator(MapEngine({}), None).run(segs)
    pkg.apply(segs)

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        prefs = z.read("Resources/Preferences.xml").decode("utf-8")
    assert 'PageBinding="LeftToRight"' in prefs


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


def test_reflect_transform_pure_translation():
    # A frame whose own X-extent is 0..40 in a 300-wide spread (centerX=150)
    # moves so its extent becomes 260..300 — same width, mirrored position,
    # linear part (and so the frame's content) untouched.
    result = _reflect_transform("1 0 0 1 20 20", center_x=150, item_center_x=20)
    a, b, c, d, tx, ty = (float(t) for t in result.split())
    assert (a, b, c, d) == (1, 0, 0, 1)  # NOT negated — content is not flipped
    assert tx == 280
    assert ty == 20


def test_reflect_transform_rotated_frame_matches_hahawww_example():
    # The real rotated side-tab frame from hahawww.idml (spec's Math section).
    # Its own anchors put it at spread X 556..588, so item_center_x = 572;
    # about the 612pt page's centerX=306 that reflects to 24..56 (center 40).
    transform = "0 1 -1 0 557.0661115895514 -247.44880838544424"
    result = _reflect_transform(transform, center_x=306, item_center_x=572)
    a, b, c, d, tx, ty = (float(t) for t in result.split())
    # Orientation preserved exactly: same rotation, same (positive) determinant.
    assert (a, d) == (0, 0)
    assert b == pytest.approx(1)
    assert c == pytest.approx(-1)
    assert a * d - b * c == pytest.approx(1)
    assert tx == pytest.approx(557.0661115895514 + 2 * (306 - 572))
    assert ty == pytest.approx(-247.44880838544424)
    # And the frame really does land on the mirrored X-extent.
    for local_y, expected_x in ((-30.933888410448613, 56.0), (1.0661115895513844, 24.0)):
        assert c * local_y + tx == pytest.approx(expected_x)


def test_reflect_transform_preserves_linear_part_verbatim():
    # Only tx is rewritten — a b c d ty come back as the exact source tokens,
    # so no float round-trip can perturb the item's orientation or scale.
    original = "1.0000000000000004 0 0 1.0000000000000004 490.15 -276.43"
    out = _reflect_transform(original, center_x=306, item_center_x=500)
    toks = out.split()
    assert toks[:4] == original.split()[:4]
    assert toks[5] == original.split()[5]
    assert float(toks[4]) == pytest.approx(490.15 + 2 * (306 - 500))


def test_page_ranges_single_page():
    tree = etree.fromstring(SPREAD_SIMPLE.encode())
    # GeometricBounds="0 0 100 300" ItemTransform tx=0 -> left=0, right=300
    assert _page_ranges(tree) == [(0, 300)]


def test_page_ranges_no_page_returns_none():
    no_page = SPREAD_SIMPLE.replace(
        '<Page Self="up1" GeometricBounds="0 0 100 300" ItemTransform="1 0 0 1 0 0"/>',
        "",
    )
    tree = etree.fromstring(no_page.encode())
    assert _page_ranges(tree) is None


def test_page_ranges_non_translation_page_transform_returns_none():
    rotated_page = SPREAD_SIMPLE.replace(
        'ItemTransform="1 0 0 1 0 0"/>\n    <TextFrame',
        'ItemTransform="0 1 -1 0 0 0"/>\n    <TextFrame',
    )
    tree = etree.fromstring(rotated_page.encode())
    assert _page_ranges(tree) is None


def test_page_ranges_two_pages_kept_separate():
    # The actual bug this function exists to prevent: collapsing two
    # pages' ranges into one combined center puts that center on the seam
    # between them (x=300 here), so mirroring an item on page 1 about that
    # combined center would land it on page 2 — confirmed against a real
    # client file where this happened (page "4"'s content mirrored onto
    # page "5", reading as "the page backgrounds got swapped").
    two_page = SPREAD_SIMPLE.replace(
        '<Page Self="up1" GeometricBounds="0 0 100 300" ItemTransform="1 0 0 1 0 0"/>',
        '<Page Self="up1" GeometricBounds="0 0 100 300" ItemTransform="1 0 0 1 0 0"/>\n'
        '    <Page Self="up2" GeometricBounds="0 0 100 300" ItemTransform="1 0 0 1 300 0"/>',
    )
    tree = etree.fromstring(two_page.encode())
    # Two separate ranges, NOT one combined (0, 600) range.
    assert _page_ranges(tree) == [(0, 300), (300, 600)]


SPREAD_WITH_GROUP = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="us1">
    <Page Self="up1" GeometricBounds="0 0 100 300" ItemTransform="1 0 0 1 0 0"/>
    <TextFrame Self="uf1" ParentStory="u10" ItemTransform="1 0 0 1 20 20">GEOM_F</TextFrame>
    <Group Self="ug1" ItemTransform="1 0 0 1 50 10">
      <Rectangle Self="ur1" ItemTransform="1 0 0 1 5 5">GEOM_R1</Rectangle>
    </Group>
    <Rectangle Self="ur2" ItemTransform="1 0 0 1 100 40">GEOM_R2</Rectangle>
  </Spread>
</idPkg:Spread>
""".replace("GEOM_F", _path_geometry(-20, -10, 20, 10)) \
   .replace("GEOM_R1", _path_geometry(-5, -5, 5, 5)) \
   .replace("GEOM_R2", _path_geometry(-30, -10, 30, 10))


def test_mirror_spread_reflects_top_level_items():
    tree = etree.fromstring(SPREAD_WITH_GROUP.encode())
    assert _mirror_spread(tree) is True

    def transform_of(self_id):
        for el in tree.iter():
            if el.get("Self") == self_id:
                return el.get("ItemTransform")

    # centerX = 150 (Page spans 0..300). TextFrame's own anchors put it at
    # spread X 0..40 (center 20), which mirrors to 260..300 -> tx 280.
    assert transform_of("uf1") == "1 0 0 1 280 20"
    # The Group carries no PathPointType geometry of its own (its extent is
    # implicit in its children), so its position is unresolvable and it is
    # left completely untouched — a known limitation, see _mirror_spread.
    assert transform_of("ug1") == "1 0 0 1 50 10"
    # Its child Rectangle's transform (relative to the group) is untouched too.
    assert transform_of("ur1") == "1 0 0 1 5 5"
    # Rectangle spans spread X 70..130 (center 100) -> mirrors to 200..260.
    assert transform_of("ur2") == "1 0 0 1 200 40"
    # Page itself is left alone — only free-floating items move.
    assert transform_of("up1") == "1 0 0 1 0 0"


SPREAD_TWO_PAGES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Spread Self="us1">
    <Page Self="up1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 -612 0"/>
    <Page Self="up2" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 0"/>
    <TextFrame Self="uf1" ParentStory="u10" ItemTransform="1 0 0 1 -600 20">GEOM_F1</TextFrame>
    <Rectangle Self="ur1" ItemTransform="1 0 0 1 100 40">GEOM_R1</Rectangle>
  </Spread>
</idPkg:Spread>
""".replace("GEOM_F1", _path_geometry(0, -10, 50, 10)) \
   .replace("GEOM_R1", _path_geometry(-20, -10, 20, 10))


def test_mirror_spread_keeps_each_item_within_its_own_page():
    """The bug this test locks in: `<Page up1>` spans spread-space
    -612..0 ("page 4"), `<Page up2>` spans 0..612 ("page 5") — a real
    2-page spread shape (verified against a real client file, where 7 of
    9 spreads are exactly this shape). A combined spread-wide center
    (here, x=0 — precisely the seam between the two pages) would mirror
    `uf1` (well inside page up1, spread X -600..-550) onto page up2's
    side entirely — content belonging to one page (e.g. a lesson's blue
    "Activity" page) landing on the facing page (a differently-templated
    "Explore" page), which reads as "the page backgrounds got swapped."
    Each item must mirror about ITS OWN page's center instead.
    """
    tree = etree.fromstring(SPREAD_TWO_PAGES.encode())
    assert _mirror_spread(tree) is True

    def transform_of(self_id):
        for el in tree.iter():
            if el.get("Self") == self_id:
                return el.get("ItemTransform")

    # uf1: own anchors at spread X -600..-550 (center -575), on page up1
    # (range -612..0, center -306). Mirrors to 2*(-306)-(-575) = -37
    # center, i.e. tx = -600 + 2*(-306-(-575)) = -1138+... — the concrete
    # check that matters is simply: stays within page up1's own range.
    tx1 = float(transform_of("uf1").split()[4])
    assert -612 <= tx1 <= 0, f"uf1 tx={tx1} landed outside its own page (up1: -612..0)"
    assert tx1 != -600  # actually moved, not a no-op

    # ur1: own anchors at spread X 80..120 (center 100), on page up2
    # (range 0..612, center 306). Must stay within page up2's range, not
    # cross the seam back onto page up1.
    tx2 = float(transform_of("ur1").split()[4])
    assert 0 <= tx2 <= 612, f"ur1 tx={tx2} landed outside its own page (up2: 0..612)"


def test_mirror_spread_preserves_determinant_sign():
    """A negative-determinant ItemTransform is exactly how InDesign encodes
    "Flip Horizontal" on an item, so mirroring must never change the sign:
    doing so mirrors the item's CONTENT (translated text renders backwards),
    not just its position."""
    rotated = SPREAD_WITH_GROUP.replace(
        '<TextFrame Self="uf1" ParentStory="u10" ItemTransform="1 0 0 1 20 20">',
        '<TextFrame Self="uf1" ParentStory="u10" '
        'ItemTransform="0 1 -1 0 557.0661115895514 -247.44880838544424">',
    )
    tree = etree.fromstring(rotated.encode())

    def det_of(self_id):
        for el in tree.iter():
            if el.get("Self") == self_id:
                a, b, c, d, _tx, _ty = (float(t) for t in el.get("ItemTransform").split())
                return a * d - b * c

    before = {sid: det_of(sid) for sid in ("uf1", "ur2")}
    assert _mirror_spread(tree) is True
    for sid, det in before.items():
        assert det_of(sid) == pytest.approx(det)
        assert det > 0  # source document has no flipped items


def test_mirror_spread_skips_item_with_no_own_geometry():
    """No PathPointType anchors -> the item's spread-space position is
    unresolvable, so it is left completely untouched rather than guessed at
    (the Group case)."""
    tree = etree.fromstring(SPREAD_WITH_GROUP.encode())
    group = next(el for el in tree.iter() if el.get("Self") == "ug1")
    before = etree.tostring(group)
    assert _mirror_spread(tree) is True  # other items still mirror
    assert etree.tostring(group) == before


def test_mirror_spread_skips_unresolvable_spread():
    no_page = SPREAD_WITH_GROUP.replace(
        '<Page Self="up1" GeometricBounds="0 0 100 300" ItemTransform="1 0 0 1 0 0"/>',
        "",
    )
    tree = etree.fromstring(no_page.encode())
    original = etree.tostring(tree)
    assert _mirror_spread(tree) is False
    assert etree.tostring(tree) == original  # untouched


def test_mirror_spread_skips_item_with_malformed_transform_not_others():
    bad_item = SPREAD_WITH_GROUP.replace(
        'ItemTransform="1 0 0 1 100 40"', 'ItemTransform="garbage"'
    )
    tree = etree.fromstring(bad_item.encode())
    assert _mirror_spread(tree) is True  # still mirrors the good items

    def transform_of(self_id):
        for el in tree.iter():
            if el.get("Self") == self_id:
                return el.get("ItemTransform")

    assert transform_of("uf1") == "1 0 0 1 280 20"  # good item still mirrored
    assert transform_of("ur2") == "garbage"  # bad item left as-is, no crash


def test_apply_mirrors_spreads_for_rtl(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_with_spread(src, spread_xml=SPREAD_SIMPLE, story_xml=STORY)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    Translator(MapEngine({}), None).run(segs)
    pkg.apply(segs, direction="rtl")

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        spread = z.read("Spreads/Spread_us1.xml").decode("utf-8")
    # TextFrame spanning spread X 0..40 in a 300-wide spread (centerX=150)
    # mirrors to 260..300 -> tx=280, linear part unchanged.
    assert 'ItemTransform="1 0 0 1 280 20"' in spread


def test_apply_leaves_spreads_alone_for_ltr(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_with_spread(src, spread_xml=SPREAD_SIMPLE, story_xml=STORY)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    Translator(MapEngine({}), None).run(segs)
    pkg.apply(segs)  # no direction — default, same as every LTR call site

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        spread = z.read("Spreads/Spread_us1.xml").decode("utf-8")
    assert 'ItemTransform="1 0 0 1 20 20"' in spread


MASTER_SPREAD_SIMPLE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:MasterSpread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <MasterSpread Self="um1">
    <Page Self="up9" GeometricBounds="0 0 100 300" ItemTransform="1 0 0 1 0 0"/>
    <TextFrame Self="umf1" ItemTransform="1 0 0 1 20 20">GEOM_F</TextFrame>
  </MasterSpread>
</idPkg:MasterSpread>
""".replace("GEOM_F", _path_geometry(-20, -10, 20, 10))


def test_apply_leaves_master_spreads_untouched_for_rtl(tmp_path):
    """MasterSpreads carry the shared template chrome (badge, running-head
    side-tab, footer, page number) that repeats identically on every page —
    verified against a real client's Portuguese/Arabic edition pair that
    chrome sits in the exact same position in both languages, so it must
    NOT mirror even for an RTL target (only content Spreads do — see
    test_apply_mirrors_spreads_for_rtl). An earlier version mirrored
    MasterSpreads too, which visibly collided that chrome into space a
    page's own mirrored content was already using."""
    src = str(tmp_path / "in.idml")
    _make_idml_with_spread(src, master_spread_xml=MASTER_SPREAD_SIMPLE)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    Translator(MapEngine({}), None).run(segs)
    pkg.apply(segs, direction="rtl")

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        master = z.read("MasterSpreads/MasterSpread_us1.xml").decode("utf-8")
    assert 'ItemTransform="1 0 0 1 20 20"' in master  # unchanged, not mirrored


def test_apply_leaves_master_spreads_alone_for_ltr(tmp_path):
    src = str(tmp_path / "in.idml")
    _make_idml_with_spread(src, master_spread_xml=MASTER_SPREAD_SIMPLE)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    Translator(MapEngine({}), None).run(segs)
    pkg.apply(segs)

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        master = z.read("MasterSpreads/MasterSpread_us1.xml").decode("utf-8")
    assert 'ItemTransform="1 0 0 1 20 20"' in master


def test_apply_mirrors_content_spread_but_not_master_spread_in_same_document(tmp_path):
    """The actual bug this fix addresses: a document with BOTH a content
    Spread and a MasterSpread mirrored differently in one apply() call —
    not either case in isolation, which passed even with the old (wrong)
    behavior if only one spread type was present in a test."""
    src = str(tmp_path / "in.idml")
    _make_idml_with_spread(src, spread_xml=SPREAD_SIMPLE,
                           master_spread_xml=MASTER_SPREAD_SIMPLE)

    pkg = IdmlPackage(src)
    segs = pkg.segments()
    Translator(MapEngine({}), None).run(segs)
    pkg.apply(segs, direction="rtl")

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        spread = z.read("Spreads/Spread_us1.xml").decode("utf-8")
        master = z.read("MasterSpreads/MasterSpread_us1.xml").decode("utf-8")
    assert 'ItemTransform="1 0 0 1 280 20"' in spread  # content: mirrored
    assert 'ItemTransform="1 0 0 1 20 20"' in master    # chrome: untouched


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
