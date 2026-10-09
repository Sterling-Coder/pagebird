import pytest

from pagebirdy.office import pipeline
from pagebirdy.review.store import ReviewStore
from pagebirdy.translate.engine import Engine
from tests.office_fixtures import upper_outside_tokens


class Upper(Engine):
    """Uppercases words, never tokens: a stand-in engine that changes text
    while honouring every placeholder, like a real one should."""
    name = "upper"

    def translate(self, texts):
        return [upper_outside_tokens(t) for t in texts]


def _run(tmp_path, text, **kw):
    src = tmp_path / "doc.txt"
    src.write_bytes(text.encode("utf-8"))
    stages = []
    store = ReviewStore(str(tmp_path / "r.db"))
    job_id = store.create_pending_job(str(src), original_filename="doc.txt",
                                      meta={"target_lang": "es"})
    store.close()
    rep = pipeline.translate_document(
        str(src), str(tmp_path / "out"), target_lang="es",
        review_db=str(tmp_path / "r.db"), job_id=job_id,
        on_stage=lambda pct, stage: stages.append(stage), engines=(Upper(), None), **kw)
    return rep, stages


def test_report_and_output(tmp_path):
    rep, stages = _run(tmp_path, "Hello {name}\n12345\nhttps://x.com\n")
    out = open(rep["output"], "rb").read().decode("utf-8")
    assert out == "HELLO {name}\n12345\nhttps://x.com\n"
    assert rep["format"] == "txt" and rep["target_lang"] == "es" and rep["source_lang"] == "en"
    assert rep["segments_total"] == 3
    assert rep["segments_protected"] == 2 and rep["segments_translated"] == 1
    assert rep["errors"] == [] and rep["units"] == {"lines": 3}
    assert stages == list(pipeline.STAGES)
    assert rep["output"].endswith("doc.es.txt")


def test_job_row_lifecycle(tmp_path):
    rep, _ = _run(tmp_path, "Hello\n")
    store = ReviewStore(str(tmp_path / "r.db"))
    job = store.get_job(rep["job_id"])
    segs = store.get_segments(rep["job_id"])
    store.close()
    assert job["status"] == "complete" and job["meta"]["format"] == "txt"
    assert job["meta"]["stage"] == "complete" and job["output"] == rep["output"]
    assert [s["seg_id"] for s in segs] == ["txt:L0"]


def test_failure_marks_the_same_row_failed(tmp_path, monkeypatch):
    from pagebirdy.office import txt

    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(txt.TxtAdapter, "rebuild", boom)
    with pytest.raises(pipeline.PipelineFailed) as e:
        _run(tmp_path, "Hello\n")
    store = ReviewStore(str(tmp_path / "r.db"))
    row = store.get_job(e.value.job_id)
    store.close()
    assert row["status"] == "failed" and row["meta"]["failed_stage"] == "reconstructing"


def test_tag_rules_only_when_document_has_tags(tmp_path, monkeypatch):
    seen = {}

    def fake_build(doc_context="", target_lang=None, extra_rules=""):
        seen["rules"] = extra_rules
        return Upper(), None
    monkeypatch.setattr(pipeline, "build_engines", fake_build)
    src = tmp_path / "doc.txt"
    src.write_text("Hello\n", encoding="utf-8")
    pipeline.translate_document(str(src), str(tmp_path / "o"), target_lang="es",
                                review_db=None)
    assert seen["rules"] == ""


def test_rebuild_from_review_applies_edits(tmp_path):
    rep, _ = _run(tmp_path, "Hello\nWorld\n")
    store = ReviewStore(str(tmp_path / "r.db"))
    store.update_segment(rep["job_id"], "txt:L1", "Mundo", approve=True)
    job = store.get_job(rep["job_id"])
    store.close()
    out = pipeline.rebuild_from_review(job, str(tmp_path / "r.db"))
    assert open(out, "rb").read() == b"HELLO\nMundo\n"
