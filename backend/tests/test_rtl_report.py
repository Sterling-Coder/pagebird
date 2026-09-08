"""QA report fields an RTL job must carry.

A reviewer opening an RTL job needs to know three things the LTR report never
had to say: that the page geometry was mirrored, which pages hold figures that
the mirror may have inverted, and whether the fonts it rendered with were the
vendored ones or whatever the host happened to have.
"""

import fitz
import pytest

from babel.pipeline import translate_pdf
from babel.reassemble.pdf import figure_pages


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    """Force the identity engine for every test in this module.

    These tests assert that nothing lands in `needs_human`, which only holds if
    translation is a passthrough. Any test that imports `babel.api` calls
    `load_env()`, which loads a real OPENAI_API_KEY out of backend/.env into the
    process — so in a full-suite run these hit the live API, the call fails, and
    every segment gets flagged. A test must not depend on whether the developer
    running it happens to have keys configured.
    """
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY",
                "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(key, raising=False)


def _pdf_with_a_figure(path):
    doc = fitz.open()
    page = doc.new_page(width=300, height=200)
    page.insert_text((20, 40), "Number of pets", fontsize=11, fontname="helv")
    # a raster image: the case detect_graphic_pages (vector density) misses
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 20, 20))
    pix.set_rect(pix.irect, (255, 0, 0))
    page.insert_image(fitz.Rect(40, 80, 140, 180), pixmap=pix)
    doc.new_page(width=300, height=200).insert_text(
        (20, 40), "no figures here", fontsize=11, fontname="helv")
    doc.save(path)
    doc.close()


def test_figure_pages_reports_a_page_holding_a_raster_image(tmp_path):
    src = str(tmp_path / "in.pdf")
    _pdf_with_a_figure(src)
    doc = fitz.open(src)
    try:
        assert figure_pages(doc) == [0]
    finally:
        doc.close()


def _report(tmp_path, lang):
    src = str(tmp_path / "in.pdf")
    _pdf_with_a_figure(src)
    return translate_pdf(src, out_dir=str(tmp_path / "out"),
                         tm_path=str(tmp_path / "tm.db"), review_db=None,
                         target_lang=lang)


def test_rtl_report_records_direction_and_that_it_mirrored(tmp_path):
    report = _report(tmp_path, "ar")
    assert report["direction"] == "rtl"
    assert report["mirrored"] is True


def test_ltr_report_records_that_nothing_was_mirrored(tmp_path):
    report = _report(tmp_path, "es")
    assert report["direction"] == "ltr"
    assert report["mirrored"] is False
    assert report["figure_pages"] == []   # only mirroring puts figures at risk


def test_rtl_report_lists_figure_pages_for_review(tmp_path):
    report = _report(tmp_path, "ar")
    assert report["figure_pages"] == [0]


def test_report_names_the_face_it_rendered_with(tmp_path):
    report = _report(tmp_path, "ar")
    assert report["font_source"] == "bundled"
    assert "NotoNaskhArabic" in report["font_regular"]


def test_urdu_is_flagged_as_style_degraded(tmp_path):
    """Urdu renders in Naskh because MuPDF draws Nastaliq blank; say so."""
    assert _report(tmp_path, "ur")["style_degraded"] is True


def test_arabic_is_not_flagged_as_style_degraded(tmp_path):
    assert _report(tmp_path, "ar")["style_degraded"] is False


def test_segments_on_a_figure_page_are_queued_for_review(tmp_path):
    """Listing the page is not enough — the work has to reach someone's queue."""
    report = _report(tmp_path, "ar")
    queued = {s["id"] for s in report["needs_human"] if s["page"] == 0}
    assert queued, "figure page produced no review items"
    assert all("mirror" in " ".join(s["notes"]).lower()
               for s in report["needs_human"] if s["page"] == 0)


def test_segments_on_a_clean_page_are_not_queued(tmp_path):
    report = _report(tmp_path, "ar")
    assert not [s for s in report["needs_human"] if s["page"] == 1]


def test_ltr_job_queues_nothing_for_figures(tmp_path):
    assert _report(tmp_path, "es")["needs_human"] == []


def test_review_job_records_the_language_and_direction(tmp_path):
    """The review UI sets `dir` on the target pane from this.

    Without it the caret jumps and trailing punctuation drifts to the wrong end
    while editing RTL text, which reviewers report as a translation bug.
    """
    from babel.review.store import ReviewStore

    src = str(tmp_path / "in.pdf")
    _pdf_with_a_figure(src)
    db = str(tmp_path / "review.db")
    translate_pdf(src, out_dir=str(tmp_path / "out"),
                  tm_path=str(tmp_path / "tm.db"), review_db=db, target_lang="ar")

    store = ReviewStore(db, tm_path=str(tmp_path / "tm.db"))
    try:
        job = store.list_jobs()[0]
    finally:
        store.close()
    assert job["meta"]["target_lang"] == "ar"
    assert job["meta"]["direction"] == "rtl"
