import zipfile

from babel.idml.package import IdmlPackage
from babel.pipeline import regenerate_idml_from_review
from babel.review.store import ReviewStore
from babel.translate.engine import Engine
from babel.translate.translator import Translator

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
    Translator(eng, None, None).run(segs)

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
    Translator(eng, None, None).run(segs)

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
    Translator(eng, None, None).run(segs)

    pkg.apply(segs)  # default idml_font=None — today's behavior
    out = str(tmp_path / "out.idml")
    pkg.save(out)

    with zipfile.ZipFile(out) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert "<AppliedFont type=\"string\">Minion Pro</AppliedFont>" in story


def test_translate_idml_passes_idml_font_for_chinese(tmp_path, monkeypatch):
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY", "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    from babel.pipeline import translate_idml

    src = str(tmp_path / "in.idml")
    _make_idml(src)  # module-level STORY fixture: Minion Pro prose + numeric + math runs

    report = translate_idml(src, out_dir=str(tmp_path / "out"),
                             tm_path=str(tmp_path / "tm.db"), review_db=None,
                             target_lang="zh")

    with zipfile.ZipFile(report["output"]) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert "<AppliedFont type=\"string\">Noto Sans SC</AppliedFont>" in story
    # Math run's original font is untouched regardless of target language.
    assert "MathematicalPi LT Std" in story


def test_translate_idml_leaves_applied_font_alone_for_spanish(tmp_path, monkeypatch):
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY", "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    from babel.pipeline import translate_idml

    src = str(tmp_path / "in.idml")
    _make_idml(src)

    report = translate_idml(src, out_dir=str(tmp_path / "out"),
                             tm_path=str(tmp_path / "tm.db"), review_db=None,
                             target_lang="es")

    with zipfile.ZipFile(report["output"]) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert "<AppliedFont type=\"string\">Minion Pro</AppliedFont>" in story


def test_translate_idml_logs_stage_progress(tmp_path, monkeypatch, caplog):
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY", "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    import logging

    from babel.pipeline import translate_idml

    src = str(tmp_path / "in.idml")
    _make_idml(src)

    with caplog.at_level(logging.INFO, logger="babel.pipeline"):
        report = translate_idml(src, out_dir=str(tmp_path / "out"),
                                 tm_path=str(tmp_path / "tm.db"), review_db=None,
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
    store = ReviewStore(review_db, tm_path=str(tmp_path / "tm.db"))
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
    Translator(eng, None, None).run(segs)

    applied = pkg.apply(segs, idml_font="Noto Sans SC")
    assert applied == 1

    out = str(tmp_path / "out.idml")
    pkg.save(out)
    with zipfile.ZipFile(out) as z:
        story = z.read("Stories/Story_u10.xml").decode("utf-8")
    assert "<AppliedFont type=\"string\">Noto Sans SC</AppliedFont>" in story
    assert "必备品" in story
