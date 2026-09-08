"""Tests for the evaluation suite.

The point of these is that every metric must be *wrong in a detectable way* when
the translation is wrong. A metric that returns a plausible number on broken
input is worse than no metric, so each test feeds a specific defect and asserts
the corresponding rate drops.
"""

from __future__ import annotations

import json
import os
import zipfile

import fitz
import pytest

from babel.eval import integrity, layout_idml, layout_pdf, quality, runner, scorecard
from babel.review.store import ReviewStore


def _pdf_text(data: bytes) -> str:
    """Text of a rendered PDF, with MuPDF's layout characters normalised.

    `fitz.Story` sets word gaps as U+00A0 and hyphens as U+00AD soft hyphens, so
    a naive substring check for "Accuracy report" fails on output that is
    perfectly correct on the page.
    """
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        raw = "\n".join(doc.load_page(i).get_text() for i in range(doc.page_count))
    finally:
        doc.close()
    # MuPDF also substitutes typographic ligatures, so "fits" comes back
    # as a single \ufb01 glyph and a naive substring check misses it.
    for bad, good in (("\u00a0", " "), ("\u00ad", "-"), ("\ufb00", "ff"),
                      ("\ufb01", "fi"), ("\ufb02", "fl"), ("\ufb03", "ffi"),
                      ("\ufb04", "ffl")):
        raw = raw.replace(bad, good)
    return raw


def seg(seg_id: str, source: str, target: str | None, *, status: str = "translated",
        placeholders: dict | None = None, has_math_font: bool = False,
        page: int = 0) -> dict:
    """A segment dict shaped exactly like ReviewStore._row_to_seg returns."""
    return {
        "job_id": "j", "seg_id": seg_id, "page": page,
        "source": source, "target": target,
        "source_restored": source, "target_restored": target,
        "status": status, "disagreement": False, "has_math_font": has_math_font,
        "placeholders": placeholders or {}, "notes": [], "approved": False,
    }


# --- integrity -------------------------------------------------------------


def test_placeholder_integrity_catches_dropped_math_token():
    segments = [
        seg("a", "Divide ⟦=3/4⟧ by ⟦=2⟧", "Divide ⟦=3/4⟧ entre ⟦=2⟧",
            placeholders={"⟦=3/4⟧": "3/4", "⟦=2⟧": "2"}),
        seg("b", "Add ⟦m0⟧ here", "Suma aquí", placeholders={"⟦m0⟧": "½"}),
    ]
    result = integrity.placeholder_integrity(segments)
    assert result["applicable"] == 2
    assert result["failures"] == 1
    assert result["rate"] == 0.5
    assert result["examples"][0]["seg_id"] == "b"


def test_number_preservation_catches_dropped_number():
    """The shipping gate allows extra ⟦=…⟧ tokens, so this is the only net —
    but only a *dropped* number gates; an added one is diagnostic only."""
    segments = [
        seg("ok", "⟦=24⟧ students read", "⟦=24⟧ estudiantes leen",
            placeholders={"⟦=24⟧": "24"}),
        seg("bad", "⟦=24⟧ students read", "⟦=25⟧ estudiantes leen",
            placeholders={"⟦=24⟧": "24"}),
    ]
    result = integrity.number_preservation(segments)
    assert result["applicable"] == 2
    assert result["dropped"] == 1
    assert result["examples"][0]["missing"] == ["24"]
    assert result["examples"][0]["invented"] == ["25"]


def test_number_preservation_does_not_gate_a_localized_addition():
    """Real EN->KO output: "Five boxes" -> "5상자" adds a digit that was already
    a number word in the source. That is correct localization, not a defect."""
    segments = [seg("a", "Five boxes cost $9", "5상자는 $9입니다")]
    result = integrity.number_preservation(segments)
    assert result["dropped"] == 0
    assert result["rate"] == 1.0
    assert result["added_only"] == 1


def test_number_preservation_tolerates_localized_decimal_separator():
    """3.5 -> 3,5 is a live policy question, not a lost number."""
    segments = [seg("a", "measure ⟦=3.5⟧ cm", "mide ⟦=3,5⟧ cm",
                    placeholders={"⟦=3.5⟧": "3.5"})]
    result = integrity.number_preservation(segments)
    assert result["dropped"] == 0
    assert result["number_format_changes"] == 1


def test_source_leakage_flags_untranslated_prose_but_not_short_labels():
    segments = [
        seg("prose", "Write the missing number", "Write the missing number"),
        seg("label", "Answers", "Answers"),  # too short to be evidence
        seg("good", "Write the missing number", "Escribe el número que falta"),
    ]
    result = integrity.source_leakage(segments)
    assert result["applicable"] == 2  # "Answers" excluded
    assert result["leaked"] == 1
    assert result["examples"][0]["seg_id"] == "prose"


def test_script_conformance_detects_english_left_in_a_korean_target():
    segments = [
        seg("hangul", "Write the number", "숫자를 쓰세요"),
        seg("english", "Write the number", "Write the number"),
    ]
    result = integrity.script_conformance(segments, "ko")
    assert result["available"] is True
    assert result["offenders"] == 1
    assert result["rate"] == 0.5


def test_translatable_words_ignores_urls_emails_and_acronyms():
    """All three appeared verbatim in a real IDML job and failed its gates."""
    assert integrity.translatable_words("www.stockindesign.com") == []
    assert integrity.translatable_words("editor@stockindesign") == []
    assert integrity.translatable_words("https://example.com/a/b") == []
    assert integrity.translatable_words("PBI MGMT") == []
    # A shouted heading is prose, not an acronym — it must stay translatable.
    assert integrity.translatable_words("THE ANSWER") == ["ANSWER"]
    assert integrity.translatable_words("Write the number") == ["Write", "the", "number"]


def test_untranslatable_segments_do_not_fail_leakage_or_script_gates():
    """A Korean document still says "www.stockindesign.com" and "MGMT"."""
    segments = [
        seg("url", "www.stockindesign.com", "www.stockindesign.com"),
        seg("mail", "editor@stockindesign", "editor@stockindesign"),
        seg("acronym", "PBI MGMT", "PBI MGMT"),
        seg("real", "Write the missing number", "숫자를 쓰세요"),
    ]
    leak = integrity.source_leakage(segments)
    assert leak["applicable"] == 1 and leak["leaked"] == 0  # only "real" is scored
    script = integrity.script_conformance(segments, "ko")
    assert script["applicable"] == 1 and script["offenders"] == 0


def test_genuinely_untranslated_prose_still_fails_after_the_url_fix():
    """The false-positive fix must not blunt the metric it was protecting."""
    segments = [
        seg("url", "www.stockindesign.com", "www.stockindesign.com"),
        seg("leaked", "Write the missing number", "Write the missing number"),
    ]
    result = integrity.source_leakage(segments)
    assert result["applicable"] == 1 and result["leaked"] == 1
    assert result["examples"][0]["seg_id"] == "leaked"


def test_script_conformance_unavailable_for_latin_targets():
    assert integrity.script_conformance([seg("a", "x y z", "a b c")], "es")["available"] is False


def test_glossary_adherence_denominator_excludes_segments_without_terms():
    segments = [
        seg("no-term", "Write the answer here", "Escribe la respuesta aquí"),
        seg("term", "Find the unit rate", "Halla la tasa por unidad"),
    ]
    result = integrity.glossary_adherence(segments, "es")
    assert result["available"] is True
    # Only the segment actually containing a glossary term is scored.
    assert result["applicable"] == 1


def test_coverage_and_rates_skip_unshipped_segments():
    segments = [
        seg("a", "one two three", "uno dos tres"),
        seg("b", "four five six", None, status="pending"),
    ]
    cov = integrity.coverage(segments)
    assert cov["applicable"] == 2 and cov["with_target"] == 1 and cov["rate"] == 0.5
    assert integrity.source_leakage(segments)["applicable"] == 1


def test_empty_denominator_reports_none_not_a_pass():
    """An empty rate must never read as 1.0 — that is how eval suites lie."""
    assert integrity.number_preservation([])["rate"] is None
    assert integrity.source_leakage([])["rate"] is None


def test_length_ratio_reports_distribution():
    segments = [seg(str(i), "a" * 20, "b" * 25) for i in range(5)]
    result = integrity.length_ratio(segments)
    assert result["applicable"] == 5
    assert result["median"] == 1.25


# --- gates and scoring -----------------------------------------------------


def test_gates_fail_on_broken_placeholders_and_skip_unmeasured():
    result = {
        "integrity": {
            "placeholder_integrity": {"rate": 0.5},
            "number_preservation": {"rate": 1.0},
            "source_leakage": {"rate": 1.0},
            "script_conformance": {"rate": None, "reason": "Latin-script target"},
        },
        "layout": {"tofu": {"rate": 1.0}, "overflow": {"rate": 0.0}},
    }
    gates = scorecard.run_gates(result)
    assert gates["passed"] is False
    assert "placeholder_integrity" in gates["failed"]
    assert "script_conformance" in gates["skipped"]
    # A skipped gate must not be reported as a pass.
    statuses = {c["gate"]: c["status"] for c in gates["checks"]}
    assert statuses["script_conformance"] == "skip"
    assert statuses["idml_overset"] == "skip"


def test_coverage_is_gated():
    """A real Korean job shipped 32.6% translated and passed every other gate,
    because they all look only at segments that did translate."""
    result = {"integrity": {"coverage": {"rate": 0.326},
                            "placeholder_integrity": {"rate": 1.0},
                            "number_preservation": {"rate": 1.0},
                            "source_leakage": {"rate": 1.0},
                            "script_conformance": {"rate": 1.0}},
              "layout": {"tofu": {"rate": 1.0}, "overflow": {"rate": 0.0}}}
    gates = scorecard.run_gates(result)
    assert gates["failed"] == ["coverage"]
    assert gates["passed"] is False


def test_overflow_gate_is_an_upper_bound():
    good = scorecard.run_gates({"layout": {"overflow": {"rate": 0.01}}})
    bad = scorecard.run_gates({"layout": {"overflow": {"rate": 0.5}}})
    assert "overflow" not in good["failed"]
    assert "overflow" in bad["failed"]


def test_catastrophic_overflow_cannot_be_masked_by_a_good_layout_score():
    """The reason overflow is a gate and not a weighted term."""
    layout = {
        "vector_preservation": {"rate": 1.0},
        "masked_pixel_similarity": {"mean": 0.95},
        "block_iou": {"mean": 0.9},
        "overflow": {"rate": 1.0},
    }
    score = scorecard.layout_score(layout)
    assert score["score"] > 0.9  # composite looks healthy...
    assert "overflow" in scorecard.run_gates({"layout": layout})["failed"]  # ...gate still fails


def test_layout_score_renormalises_over_available_components():
    full = scorecard.layout_score({
        "vector_preservation": {"rate": 0.8},
        "masked_pixel_similarity": {"mean": 0.8},
        "block_iou": {"mean": 0.8},
    })
    assert full["score"] == 0.8 and full["weight_covered"] == 1.0

    partial = scorecard.layout_score({
        "vector_preservation": {"rate": 0.8},
        "masked_pixel_similarity": {"mean": None, "available": False},
        "block_iou": {"mean": 0.8},
    })
    # A missing dependency must not drag the score down.
    assert partial["score"] == 0.8
    assert partial["weight_covered"] == 0.7
    assert partial["missing"] == ["masked_pixel_similarity"]


def test_layout_score_none_when_nothing_measurable():
    assert scorecard.layout_score({})["score"] is None


def test_idml_gets_no_invented_composite_but_an_explicit_reason():
    """Folding the IDML structural gates into an average would manufacture a
    near-constant 1.0 that looks like a measurement and is not one."""
    idml = scorecard.layout_score(
        {"run_preservation": {"rate": 1.0}, "style_preservation": {"rate": 1.0}},
        fmt="idml")
    assert idml["score"] is None
    assert idml["structural_only"] is True
    assert "InDesign export" in idml["reason"]
    # A PDF with nothing measurable is a different situation and says so.
    assert "structural_only" not in scorecard.layout_score({}, fmt="pdf")


def test_overall_score_is_defined_for_both_pdf_and_idml():
    pdf = scorecard.overall_score({
        "format": "pdf",
        "integrity": {"placeholder_integrity": {"rate": 1.0},
                      "source_leakage": {"rate": 0.9}},
        "layout": {},
        "layout_score": {"score": 0.8, "components": {"block_iou": {}}},
        "gates": {"passed": True, "failed": []},
    })
    # content = mean(1.0, 0.9) = 0.95 ; structure = 0.80
    assert pdf["halves"]["content"]["value"] == 0.95
    assert pdf["score"] == pytest.approx(0.95 * 0.6 + 0.80 * 0.4)

    idml = scorecard.overall_score({
        "format": "idml",
        "integrity": {"placeholder_integrity": {"rate": 1.0}},
        "layout": {"run_preservation": {"rate": 1.0},
                   "style_preservation": {"rate": 0.8},
                   "asset_preservation": {"rate": 1.0}},
        "layout_score": {"score": None, "structural_only": True},
        "gates": {"passed": True, "failed": []},
    })
    # IDML has no layout composite, so structure comes from its structural rates.
    assert idml["halves"]["structure"]["value"] == pytest.approx(0.9333, abs=1e-4)
    assert idml["score"] is not None


def test_overall_score_always_carries_the_gate_verdict():
    """It is a mean, so it cannot express "must not ship" — the verdict has to
    travel with it or the number gets quoted alone."""
    result = scorecard.overall_score({
        "format": "pdf",
        "integrity": {"placeholder_integrity": {"rate": 1.0},
                      "source_leakage": {"rate": 0.958}},
        "layout": {},
        "layout_score": {"score": 0.95},
        "gates": {"passed": False, "failed": ["source_leakage"]},
    })
    assert result["score"] > 0.95  # looks healthy...
    assert result["gates_passed"] is False  # ...and says so anyway
    assert result["gates_failed"] == ["source_leakage"]


def test_overall_score_renormalises_and_reports_nothing_measurable():
    only_content = scorecard.overall_score({
        "format": "idml",
        "integrity": {"coverage": {"rate": 0.5}},
        "layout": {}, "layout_score": {"score": None},
        "gates": {"passed": True},
    })
    assert only_content["score"] == 0.5  # structure absent, weight renormalised
    assert only_content["missing"] == ["structure"]

    empty = scorecard.overall_score({"format": "pdf", "integrity": {}, "layout": {},
                                     "layout_score": {}, "gates": {"passed": False}})
    assert empty["score"] is None and empty["gates_passed"] is False


def test_baseline_delta_splits_reconstruction_from_text_growth():
    delta = scorecard.baseline_delta({"score": 0.80}, {"score": 0.90})
    assert delta["reconstruction_loss"] == pytest.approx(0.10)
    assert delta["text_growth_loss"] == pytest.approx(0.10)
    assert scorecard.baseline_delta({"score": 0.8}, {})["available"] is False


def test_iou_geometry():
    assert layout_pdf._iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0
    assert layout_pdf._iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0.0
    assert layout_pdf._iou((0, 0, 10, 10), (0, 0, 10, 5)) == pytest.approx(0.5)


# --- PDF layout ------------------------------------------------------------


def _make_pdf(path, text: str, *, draw_lines: int = 3, y: float = 100.0) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, y), text, fontsize=11)
    for i in range(draw_lines):
        page.draw_line(fitz.Point(72, 200 + i * 20), fitz.Point(400, 200 + i * 20))
    doc.save(path)
    doc.close()


def test_vector_preservation_detects_lost_line_art(tmp_path):
    src, out = tmp_path / "s.pdf", tmp_path / "o.pdf"
    _make_pdf(src, "Write the missing number", draw_lines=4)
    _make_pdf(out, "Escribe el numero que falta", draw_lines=1)
    result = layout_pdf.vector_preservation(str(src), str(out))
    assert result["src_drawings"] == 4 and result["out_drawings"] == 1
    assert result["lost_drawings"] == 3
    assert result["rate"] == 0.25
    assert result["page_count_match"] is True


def test_block_iou_high_when_text_stays_put_low_when_it_moves(tmp_path):
    src, same, moved = tmp_path / "s.pdf", tmp_path / "a.pdf", tmp_path / "b.pdf"
    _make_pdf(src, "Write the missing number", y=100)
    _make_pdf(same, "Escribe el numero", y=100)
    _make_pdf(moved, "Escribe el numero", y=400)
    assert layout_pdf.block_iou(str(src), str(same))["mean"] > 0.5
    strayed = layout_pdf.block_iou(str(src), str(moved))
    assert strayed["mean"] == 0.0
    assert strayed["unmatched"] == 1


def test_masked_pixel_similarity_ignores_changed_text(tmp_path):
    """Different words, same layout — the score must stay high, or the metric is
    measuring translation rather than layout."""
    pytest.importorskip("skimage")
    src, out = tmp_path / "s.pdf", tmp_path / "o.pdf"
    _make_pdf(src, "Write the missing number here", draw_lines=3)
    _make_pdf(out, "Escribe aqui el numero que falta", draw_lines=3)
    result = layout_pdf.masked_pixel_similarity(str(src), str(out), dpi=72)
    assert result["available"] is True
    assert result["mean"] > 0.95


def test_tofu_flags_glyphs_the_target_font_cannot_render():
    result = layout_pdf.tofu([seg("a", "hello", "안녕하세요")], "es")
    if not result["available"]:
        pytest.skip(result["reason"])
    # Hangul in a Latin face is exactly the empty-box failure this catches.
    assert result["segments_with_tofu"] == 1
    assert result["rate"] == 0.0


def test_pdf_pair_evaluation_produces_gates_and_a_score(tmp_path):
    src, out = tmp_path / "s.pdf", tmp_path / "o.pdf"
    _make_pdf(src, "Write the missing number")
    _make_pdf(out, "Escribe el numero que falta")
    result = runner.evaluate_pdf_pair(str(src), str(out), lang="es")
    assert result["layout_score"]["score"] is not None
    assert "gates" in result
    assert result["integrity"]["available"] is False
    assert scorecard.render_markdown(result).startswith("# Accuracy report")


# --- IDML layout -----------------------------------------------------------

_STORY = """<Story Self="story">
  <ParagraphStyleRange AppliedParagraphStyle="ps/Body">
    <CharacterStyleRange AppliedCharacterStyle="cs/None" PointSize="11">
      <Properties><AppliedFont type="string">{font}</AppliedFont></Properties>
      <Content>{text}</Content>
    </CharacterStyleRange>
  </ParagraphStyleRange>
  <ParagraphStyleRange AppliedParagraphStyle="ps/Body">
    <CharacterStyleRange AppliedCharacterStyle="cs/None" PointSize="11">
      <Properties><AppliedFont type="string">MathematicalPi-One</AppliedFont></Properties>
      <Content>{math}</Content>
    </CharacterStyleRange>
  </ParagraphStyleRange>
</Story>"""


def _make_idml(path, text: str, math: str = "½", font: str = "Minion Pro",
               spread: bytes = b"<Spread Self='s1'/>") -> None:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("Spreads/Spread_s1.xml", spread)
        z.writestr("Stories/Story_u1.xml",
                   _STORY.format(text=text, math=math, font=font))


def test_idml_structural_metrics_pass_on_a_clean_translation(tmp_path):
    src, out = tmp_path / "s.idml", tmp_path / "o.idml"
    _make_idml(src, "Write the missing number")
    _make_idml(out, "Escribe el numero que falta")
    result = layout_idml.evaluate(str(src), str(out))
    assert result["run_preservation"]["rate"] == 1.0
    assert result["style_preservation"]["rate"] == 1.0
    assert result["math_run_preservation"]["rate"] == 1.0
    assert result["asset_preservation"]["rate"] == 1.0
    assert result["run_translation"]["translated"] == 1
    assert result["overset_frames"]["available"] is False


def test_idml_detects_corrupted_math_run_and_moved_spread(tmp_path):
    src, out = tmp_path / "s.idml", tmp_path / "o.idml"
    _make_idml(src, "Write the missing number", math="½")
    _make_idml(out, "Escribe el numero", math="un medio",
               spread=b"<Spread Self='s1' moved='yes'/>")
    result = layout_idml.evaluate(str(src), str(out))
    assert result["math_run_preservation"]["rate"] == 0.0
    assert "Spreads/Spread_s1.xml" in result["asset_preservation"]["changed"]


def test_idml_font_override_is_reported_separately_from_style_loss(tmp_path):
    """Rewriting AppliedFont for a CJK target is intentional, not a style loss."""
    src, out = tmp_path / "s.idml", tmp_path / "o.idml"
    _make_idml(src, "Write the missing number", font="Minion Pro")
    _make_idml(out, "숫자를 쏰세요", font="Noto Sans KR")
    result = layout_idml.evaluate(str(src), str(out))
    assert result["style_preservation"]["rate"] == 1.0
    assert result["style_preservation"]["font_overrides"] == 1


def test_idml_overset_read_from_export_json(tmp_path):
    export = tmp_path / "export.json"
    export.write_text(json.dumps({"overset_frames": 3}), encoding="utf-8")
    result = layout_idml.overset_from_export(str(export))
    assert result["available"] is True and result["count"] == 3
    assert "idml_overset" in scorecard.run_gates(
        {"layout": {"overset_frames": result}})["failed"]


def test_idml_pair_evaluation_end_to_end(tmp_path):
    src, out = tmp_path / "s.idml", tmp_path / "o.es.idml"
    _make_idml(src, "Write the missing number")
    _make_idml(out, "Escribe el numero que falta")
    result = runner.evaluate_idml_pair(str(src), str(out))
    assert result["target_lang"] == "es"  # inferred from the .es.idml filename
    assert scorecard.render_markdown(result).startswith("# Accuracy report")


# --- runner / gold corpus --------------------------------------------------


def _saved_job(tmp_path, segments) -> tuple[str, str]:
    """Persist real Segments through ReviewStore so runner reads a genuine row."""
    from babel.models import Segment

    db = str(tmp_path / "review.db")
    store = ReviewStore(db, tm_path=str(tmp_path / "tm.db"))
    try:
        job_id = store.save_job(
            str(tmp_path / "src.pdf"), str(tmp_path / "src.es.pdf"),
            [Segment(id=s["seg_id"], page=0, bbox=(0, 0, 10, 10), font="F", size=10,
                     color=0, source=s["source"], target=s["target"],
                     status=s["status"], placeholders=s["placeholders"])
             for s in segments],
            {"engine_primary": "test"},
        )
    finally:
        store.close()
    return db, job_id


def test_evaluate_job_scores_integrity_without_the_documents_on_disk(tmp_path):
    db, job_id = _saved_job(tmp_path, [
        seg("a", "Write the missing number", "Escribe el numero que falta"),
        seg("b", "Add ⟦m0⟧ here", "Suma aquí", placeholders={"⟦m0⟧": "½"}),
    ])
    result = runner.evaluate_job(job_id, review_db=db)
    assert result["target_lang"] == "es"
    assert result["integrity"]["placeholder_integrity"]["failures"] == 1

    # The review panel renders these; they come from the same source the PDF
    # prints, so the screen and the downloaded report cannot disagree.
    terms = {e["term"] for e in result["explanations"]}
    assert "Math placeholders intact" in terms
    assert all(e["text"] and e["formula"] for e in result["explanations"])
    assert result["score_formulas"][0].startswith("Overall accuracy = 0.60")
    assert result["gates"]["passed"] is False
    # Missing files must degrade layout only, never break the run.
    assert result["layout"]["available"] is False
    assert scorecard.render_markdown(result).startswith("# Accuracy report")


def test_idml_job_does_not_score_glyphs_against_the_pdf_path_font(tmp_path):
    """InDesign sets IDML runs in Language.idml_font, not the PDF reassembler's
    face. Checking Korean IDML text against Arial failed real jobs on ornament
    characters that the actual target font renders fine."""
    from babel.models import Segment

    db = str(tmp_path / "review.db")
    src, out = tmp_path / "s.idml", tmp_path / "s.ko.idml"
    _make_idml(src, "Write the missing number")
    _make_idml(out, "숫자를 쓰세요 ᴥ")

    store = ReviewStore(db, tm_path=str(tmp_path / "tm.db"))
    try:
        job_id = store.save_job(
            str(src), str(out),
            [Segment(id="a", page=0, bbox=(0, 0, 0, 0), font="Minion Pro", size=0,
                     color=0, source="Write the missing number",
                     target="숫자를 쓰세요 ᴥ", status="translated")],
            {"engine_primary": "test", "format": "idml"},
        )
    finally:
        store.close()

    result = runner.evaluate_job(job_id, review_db=db)
    tofu = result["layout"]["tofu"]
    assert tofu["available"] is False
    assert "Noto Sans KR" in tofu["reason"]  # the font InDesign will actually use
    # An unmeasurable check must skip, never fail the job.
    assert "tofu" in result["gates"]["skipped"]
    assert "tofu" not in result["gates"]["failed"]
    assert result["layout_score"]["structural_only"] is True


def test_freeze_gold_writes_restored_pairs(tmp_path):
    from babel.models import Segment

    db = str(tmp_path / "review.db")
    store = ReviewStore(db, tm_path=str(tmp_path / "tm.db"))
    try:
        job_id = store.save_job(
            str(tmp_path / "src.pdf"), str(tmp_path / "src.es.pdf"),
            [Segment(id="a", page=0, bbox=(0, 0, 10, 10), font="F", size=10, color=0,
                     source="Divide ⟦=3/4⟧ by ⟦=2⟧", target="Divide ⟦=3/4⟧ entre ⟦=2⟧",
                     status="translated",
                     placeholders={"⟦=3/4⟧": "3/4", "⟦=2⟧": "2"})],
            {"engine_primary": "test"},
        )
        store.update_segment(job_id, "a", "Divide ⟦=3/4⟧ entre ⟦=2⟧", approve=True)
    finally:
        store.close()

    out = tmp_path / "gold.jsonl"
    stats = runner.freeze_gold(db, str(out), lang="es")
    assert stats["entries"] == 1
    row = json.loads(out.read_text(encoding="utf-8").strip())
    # Placeholders must be restored, or a model scores ⟦=3/4⟧ instead of the number.
    assert row["source"] == "Divide 3/4 by 2"
    assert row["target"] == "Divide 3/4 entre 2"

    gold = quality.load_gold(str(out))
    assert gold["Divide 3/4 by 2"] == "Divide 3/4 entre 2"


# --- optional tiers degrade, never crash -----------------------------------


def test_quality_without_gold_or_neural_is_reported_as_unavailable():
    result = quality.evaluate([seg("a", "one two three", "uno dos tres")], "es",
                              neural=False)
    assert result["surface"]["matched"] == 0
    assert result["comet_kiwi"]["available"] is False


def test_quality_pairs_are_restored_and_exclude_tm_hits():
    segments = [
        seg("a", "Divide ⟦=3/4⟧", "Divide ⟦=3/4⟧", placeholders={"⟦=3/4⟧": "3/4"}),
        seg("b", "cached line", "linea en cache", status="tm_hit"),
    ]
    assert quality.pairs(segments)[0]["src"] == "Divide 3/4"
    assert len(quality.pairs(segments)) == 2
    assert len(quality.pairs(segments, exclude_tm=True)) == 1


def test_mqm_scoring_weights_severities_and_ignores_unscored_chunks():
    from babel.eval import mqm

    items = [{"seg_id": "a", "src": "one two three four five", "mt": "x"},
             {"seg_id": "b", "src": "six seven eight nine ten", "mt": "y"},
             {"seg_id": "c", "src": "unscored chunk here ok", "mt": "z"}]
    verdicts = [
        [{"category": "accuracy/mistranslation", "severity": "critical",
          "span": "x", "note": "wrong"}],
        [],
        None,  # a failed chunk must not count as perfect
    ]
    result = mqm.score(items, verdicts)
    assert result["scored"] == 2
    assert result["words"] == 10
    assert result["penalty"] == 10.0  # one critical
    assert result["penalty_per_100_words"] == 100.0
    assert result["mqm_score"] == 0.0
    assert result["critical_errors"] == 1


def test_eval_endpoint_scores_caches_and_404s(monkeypatch, tmp_path):
    """The UI panel's contract: a scorecard, cached, and honest about bad ids."""
    from fastapi.testclient import TestClient

    import babel.api as api
    from babel.models import Segment

    api._REVIEW_DB = str(tmp_path / "review.db")
    api._TM_DB = str(tmp_path / "tm.db")
    monkeypatch.setenv("BABEL_OUT_DIR", str(tmp_path / "out"))

    store = ReviewStore(api._REVIEW_DB, tm_path=api._TM_DB)
    try:
        job_id = store.save_job(
            str(tmp_path / "src.pdf"), str(tmp_path / "src.es.pdf"),
            [Segment(id="a", page=0, bbox=(0, 0, 10, 10), font="F", size=10, color=0,
                     source="Write the missing number",
                     target="Escribe el numero que falta", status="translated")],
            {"engine_primary": "identity"},
        )
    finally:
        store.close()

    client = TestClient(api.app)
    assert client.get("/api/jobs/nope/eval").status_code == 404

    body = client.get(f"/api/jobs/{job_id}/eval").json()
    assert body["job_id"] == job_id
    assert body["integrity"]["placeholder_integrity"]["rate"] == 1.0
    assert "checks" in body["gates"]

    cached = tmp_path / "out" / "eval" / f"{job_id}.eval.json"
    assert cached.exists()
    # A second request must serve the cache, not re-render every page.
    cached.write_text(json.dumps({"job_id": job_id, "sentinel": True}), encoding="utf-8")
    assert client.get(f"/api/jobs/{job_id}/eval").json().get("sentinel") is True
    # ...and refresh must bypass it, since rates move as segments get approved.
    assert "sentinel" not in client.get(f"/api/jobs/{job_id}/eval?refresh=1").json()


def test_eval_download_serves_markdown_and_json(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    import babel.api as api
    from babel.models import Segment

    api._REVIEW_DB = str(tmp_path / "review.db")
    api._TM_DB = str(tmp_path / "tm.db")
    monkeypatch.setenv("BABEL_OUT_DIR", str(tmp_path / "out"))

    store = ReviewStore(api._REVIEW_DB, tm_path=api._TM_DB)
    try:
        job_id = store.save_job(
            str(tmp_path / "src.pdf"), str(tmp_path / "src.es.pdf"),
            [Segment(id="a", page=0, bbox=(0, 0, 10, 10), font="F", size=10, color=0,
                     source="Write the missing number",
                     target="Escribe el numero que falta", status="translated")],
            {"engine_primary": "identity"},
            original_filename="Grade 6 Workbook.pdf",
        )
    finally:
        store.close()

    client = TestClient(api.app)

    pdf = client.get(f"/api/jobs/{job_id}/eval/download")  # pdf is the default
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")
    assert 'filename="Grade 6 Workbook-accuracy.pdf"' in pdf.headers["content-disposition"]

    md = client.get(f"/api/jobs/{job_id}/eval/download?format=md")
    assert md.status_code == 200
    assert md.headers["content-type"].startswith("text/markdown")
    # Named after the upload, so it is recognisable in a Downloads folder.
    assert 'filename="Grade 6 Workbook-accuracy.md"' in md.headers["content-disposition"]
    body = md.text
    assert body.startswith("# Accuracy report")
    assert "## Gates" in body and "SKIP" in body
    assert "evaluated:" in body  # a downloaded report must stand alone

    js = client.get(f"/api/jobs/{job_id}/eval/download?format=json")
    assert js.status_code == 200
    assert json.loads(js.text)["job_id"] == job_id
    assert 'filename="Grade 6 Workbook-accuracy.json"' in js.headers["content-disposition"]

    assert client.get(f"/api/jobs/{job_id}/eval/download?format=docx").status_code == 400
    assert client.get("/api/jobs/nope/eval/download").status_code == 404


def test_pdf_report_renders_readable_text_and_marks_skips(tmp_path):
    """The PDF must carry the same verdicts as the screen — and must not print a
    skipped check as if it had passed."""
    from babel.eval import report_pdf

    result = {
        "job_id": "j1", "format": "pdf", "target_lang": "es",
        "original_filename": "Grade 6.pdf", "evaluated_at": 1_755_000_000.0,
        "integrity": {
            "segments": 500,
            "placeholder_integrity": {"rate": 1.0, "applicable": 500},
            "source_leakage": {"rate": 0.95, "applicable": 300},
            "script_conformance": {"rate": None, "reason": "Latin-script target"},
        },
        "layout": {"vector_preservation": {"rate": 1.0},
                   "block_iou": {"mean": 0.88},
                   "overflow": {"rate": 0.0}},
        "layout_score": {"score": 0.94, "formula": "0.45*v + 0.25*b / 0.7"},
        "gates": {
            "passed": False,
            "checks": [
                {"gate": "placeholder_integrity", "status": "pass", "value": 1.0,
                 "why": "corrupted mathematics"},
                {"gate": "source_leakage", "status": "fail", "value": 0.95,
                 "why": "untranslated English left standing"},
                {"gate": "script_conformance", "status": "skip", "value": None,
                 "why": "…", "reason": "Latin-script target"},
            ],
            "failed": ["source_leakage"], "skipped": ["script_conformance"],
        },
    }
    result["overall"] = scorecard.overall_score(result)

    data = report_pdf.render_pdf(result)
    assert data.startswith(b"%PDF")
    text = _pdf_text(data)

    assert "Accuracy report" in text
    assert "NOT READY TO DELIVER" in text

    # No sample sizes anywhere: "all 46 passed" under a document of 848 reads as
    # 802 pieces quietly ignored, which is the opposite of what it means.
    assert "of 500" not in text and "500 pieces" not in text
    # The headline figure and the verdict must both be on the page.
    assert "Overall accuracy" in text
    # A skip that cannot apply reads as NOT APPLICABLE; one that would apply but
    # is unconfigured is lifted out of this table into "Open items" entirely.
    # Collapsed, because a narrow table cell wraps the label across two lines.
    flat = " ".join(text.split())
    assert "FAILED" in flat and "NOT APPLICABLE" in flat
    assert "SKIPPED" not in flat

    # The language pair is spelled out in the opening sentence; a reader should
    # not have to know that "es" means Spanish. The internal job id is not their
    # concern and must not appear.
    assert "compares the Spanish version of the document against the English" in text
    assert "j1" not in text

    # A skipped check says why in the reader's terms, not "not measured" — and
    # follows it with what is or is not covered as a result, so the reader is
    # never left wondering whether the skip mattered.
    assert "Latin alphabet" in text
    assert "not measured" not in text
    assert "nothing is missed" in text  # the InDesign-only gates on a PDF job

    # Each figure is explained in words, not counts, and each row says what the
    # check looked at rather than how many of them there were.
    assert "no problems found" in flat or "text affected" in flat
    assert "pieces that were translated" in flat  # the "what it looked at" column
    # Overflow is an upper-bound gate: its label must match the value's polarity,
    # or a healthy 0.0% reads as "nothing fits".
    assert "Text fits its frame" not in text

    # A plain-language glossary closes the report. fitz.Story silently DROPS a
    # table that will not fit the remaining space, so this is built from
    # paragraphs — assert the definitions really reached the page, not just the
    # heading above them.
    assert "What each check means" in text
    assert "Math placeholders intact —" in text
    assert "set aside before translating" in text
    # Unconfigured checks sit in the main table, not a separate section.
    assert "Open items" not in flat

    # Each definition carries its formula, and the two composite scores are
    # spelled out, so the arithmetic can be checked without leaving the report.
    assert "Overall accuracy = 0.60 x wording + 0.40 x layout" in text
    assert "0.45 x Vector art" in text
    assert "pieces of text with every formula intact / pieces translated" in text
    # Overflow is shown inverted so it reads higher-is-better like every other
    # figure; the label and the formula both have to match the flipped value.
    assert "pieces whose text fits its box / total pieces" in flat
    assert "Text fits its box" in flat

    # Only checks that ran are defined; a PDF report must not explain the four
    # IDML gates it skipped.
    glossary = text.split("What each check means")[-1]
    assert "IDML runs preserved —" not in glossary
    assert "Target script used —" not in glossary  # skipped: Latin-script target

    # The optional quality tier is off by default; a standing apology for a
    # metric nobody asked for is noise on a client report.
    assert "was not run for this report" not in text
    assert "--neural" not in text


def test_pdf_report_embeds_a_font_covering_the_target_script(tmp_path):
    """Base-14 fonts are Latin-only — a Korean report would render as the very
    empty boxes the tofu metric exists to catch."""
    from babel.eval import report_pdf

    result = {
        "job_id": "j2", "format": "idml", "target_lang": "ko",
        "original_filename": "교재.idml", "evaluated_at": 1_755_000_000.0,
        "integrity": {"segments": 10},
        "layout": {},
        "layout_score": scorecard.layout_score({}, fmt="idml"),
        "gates": {"passed": True, "checks": [], "failed": [], "skipped": []},
    }
    from babel import languages

    if not any(os.path.exists(p) for p in languages.get("ko").fonts["regular"]):
        pytest.skip("no Korean face installed on this machine")

    data = report_pdf.render_pdf(result)
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        fonts = [f[3] for f in doc.load_page(0).get_fonts(full=True)]
    finally:
        doc.close()

    # The report no longer prints the filename, so the proof is the embedded
    # face itself: a Latin-only base-14 font would mean Hangul draws as boxes.
    assert fonts and "Helvetica" not in " ".join(fonts)
    assert any("Malgun" in f or "Gothic" in f or "Noto" in f for f in fonts), fonts
    # Subset, not the whole face: unsubset Malgun Gothic made this 13 MB.
    assert len(data) < 1_000_000, f"{len(data)} bytes — font subsetting regressed"
    assert "+" in fonts[0], f"{fonts[0]} is not a subset (no XXXXXX+ prefix)"


def test_report_filename_strips_header_unsafe_characters():
    """Uploads carry arbitrary names; a quote or newline here is header injection."""
    import babel.api as api

    name = api._report_filename({"original_filename": 'a"b\nc/d.pdf'}, "job1", "md")
    assert '"' not in name and "\n" not in name and "/" not in name
    assert name.endswith("-accuracy.md")
    # Falls back to the job id when nothing survives sanitising.
    assert api._report_filename({"original_filename": "***.pdf"}, "job1", "md") == \
        "job1-accuracy.md"


def test_markdown_report_states_why_idml_has_no_composite():
    """A blank layout section reads as breakage; the reason must survive into
    the downloaded file."""
    result = {
        "job_id": "j", "format": "idml", "target_lang": "ko",
        "integrity": {"segments": 10},
        "layout": {},
        "layout_score": scorecard.layout_score({"run_preservation": {"rate": 1.0}},
                                               fmt="idml"),
        "gates": {"passed": True, "checks": [], "failed": [], "skipped": []},
    }
    body = scorecard.render_markdown(result)
    assert "## Structure" in body
    assert "InDesign export" in body


def test_mqm_parse_rejects_malformed_and_unknown_severities():
    from babel.eval import mqm

    assert mqm._parse("not json", 2) == [[], []]
    # Wrong length means the model lost alignment; no verdict is safer than a
    # misaligned one.
    assert mqm._parse(json.dumps({"v": [{"errors": []}]}), 3) == [[], [], []]
    parsed = mqm._parse(json.dumps({"v": [{"errors": [
        {"category": "style", "severity": "nonsense"},
        {"category": "terminology", "severity": "major"}]}]}), 1)
    assert len(parsed[0]) == 1 and parsed[0][0]["severity"] == "major"


def test_overflow_tolerance_scales_with_the_line_height():
    """A taller script is not an overflowing one.

    Devanagari carries vowel marks above and below the baseline, so its line box
    is taller than the English it replaced even when the text fits. Against a
    fixed 1pt allowance that reported a seventh of a real Hindi page as
    overflowing, with a median overshoot of 1.6pt on a 13.5pt line. Overflow
    means the text gained a line, which is a whole line height lower.
    """
    from babel.eval.layout_pdf import _OVERFLOW_SLACK

    line = 13.5
    tolerance = max(1.0, line * _OVERFLOW_SLACK)
    assert 1.6 < tolerance, "a taller glyph box must not count as overflow"
    assert line > tolerance, "a full extra line must still count as overflow"


def test_product_names_are_not_counted_as_untranslated_text():
    """A Spanish edition still says "i-Ready Connect".

    On a real job 37 of 38 segments flagged as untranslated were two brand names
    repeated through the document, which failed the gate on a document that was
    correctly translated. Shape alone cannot tell a brand from a heading, so
    Title Case has to repeat before it is excused.
    """
    brand = [seg(f"b{i}", "i-Ready Connect", "i-Ready Connect") for i in range(4)]
    game = [seg(f"g{i}", "Hungry Guppy", "Hungry Guppy") for i in range(4)]
    heading = [seg("h", "Describe Position", "Describe Position")]
    prose = [seg("p", "Write the missing number", "Write the missing number")]

    result = integrity.source_leakage(brand + game + heading + prose)
    flagged = {e["text"] for e in result["examples"]}
    assert "i-Ready Connect" not in flagged   # internal capital: a brand mark
    assert "Hungry Guppy" not in flagged      # Title Case, repeated: a name
    assert "Describe Position" in flagged     # Title Case, rare: a heading
    assert "Write the missing number" in flagged


def test_tofu_scores_what_reassembly_draws_not_the_stored_text():
    """Reassembly swaps a character the face cannot draw for a plain equivalent,
    so the metric has to ask what reaches the page.

    Scoring the stored target instead reported the minus sign in "8 - 3 = 5" as
    unprintable on a Korean page where it had already been drawn as a hyphen --
    a defect the pipeline had fixed, still failing the gate. The substitution
    must not blind the check: a character with no equivalent still fails.
    """
    import os

    from babel import languages

    if not any(os.path.exists(p) for p in languages.get("ko").fonts["regular"]):
        pytest.skip("no Korean face installed on this machine")

    def one(target):
        return layout_pdf.tofu([seg("a", "x", target)], "ko")["segments_with_tofu"]

    assert one("8 − 3 = 5") == 0      # minus sign -> drawn as a hyphen
    assert one("One‑Variable") == 0    # non-breaking hyphen -> hyphen
    assert one("😀 hello") == 1     # emoji: no equivalent, still caught
    assert one("ꯀ test") == 1          # unsupported script, still caught
    assert one("안녕 3 - 2") == 0  # ordinary Korean and ASCII
