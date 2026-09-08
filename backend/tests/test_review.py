import json

from babel.models import Segment
from babel.review.store import ReviewStore
from babel.tm.store import TranslationMemory


def _seg(sid, source, target, placeholders=None, status="needs_human"):
    return Segment(id=sid, page=0, bbox=(0, 0, 1, 1), font="f", size=11, color=0,
                   source=source, target=target, placeholders=placeholders or {},
                   status=status)


def _store(tmp_path):
    return ReviewStore(str(tmp_path / "review.db"), tm_path=str(tmp_path / "tm.db"))


def test_save_and_list(tmp_path):
    st = _store(tmp_path)
    jid = st.save_job("in.pdf", "out.pdf",
                      [_seg("a", "The ratio", "The ratio", status="needs_human"),
                       _seg("b", "   ", None)],  # empty skipped
                      {"engine_primary": "identity"})
    jobs = st.list_jobs()
    assert jobs[0]["id"] == jid
    segs = st.get_segments(jid)
    assert len(segs) == 1 and segs[0]["seg_id"] == "a"


def test_edit_rejected_on_placeholder_mismatch(tmp_path):
    st = _store(tmp_path)
    jid = st.save_job("in.pdf", "out.pdf",
                      [_seg("a", "Divide ⟦m0⟧ by ⟦m1⟧", None,
                            {"⟦m0⟧": "3", "⟦m1⟧": "4"})],
                      {})
    # Human drops a placeholder -> same gate rejects it.
    res = st.update_segment(jid, "a", "Divide entre ⟦m1⟧", approve=True)
    assert res["status"] == "needs_human"
    assert not res["approved"]
    assert any("placeholder mismatch" in n for n in res["notes"])


def test_approve_writes_tm_and_is_reused(tmp_path):
    st = _store(tmp_path)
    jid = st.save_job("in.pdf", "out.pdf",
                      [_seg("a", "The ratio ⟦=5⟧", "The ratio ⟦=5⟧", {"⟦=5⟧": "5"})],
                      {})
    res = st.update_segment(jid, "a", "La razón ⟦=5⟧", approve=True)
    assert res["status"] == "approved" and res["approved"]
    assert res["target_restored"] == "La razón 5"

    # The approval is now an approved TM entry, reusable elsewhere.
    tm = TranslationMemory(str(tmp_path / "tm.db"))
    hit = tm.lookup("The ratio ⟦=5⟧")
    tm.close()
    assert hit == ("La razón ⟦=5⟧", True)


def test_hardening_pragmas_and_schema(tmp_path):
    st = _store(tmp_path)
    mode = st.conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal"
    fk = st.conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert fk == 1

    job_cols = {r[1] for r in st.conn.execute("PRAGMA table_info(jobs)")}
    assert {"original_filename", "file_hash", "file_size",
            "duration_sec", "status", "error"} <= job_cols

    event_cols = {r[1] for r in st.conn.execute("PRAGMA table_info(segment_events)")}
    assert {"id", "job_id", "seg_id", "action", "reviewer",
            "old_target", "new_target", "created_at"} == event_cols

    idx = {r[1] for r in st.conn.execute("PRAGMA index_list(segments)")}
    assert "idx_segments_job_status" in idx


def test_save_job_with_file_and_run_metadata(tmp_path):
    st = _store(tmp_path)
    jid = st.save_job(
        "in.pdf", "out.pdf", [_seg("a", "Hi", "Hola", status="translated")], {},
        original_filename="upload.pdf", file_hash="abc123", file_size=4096,
        duration_sec=12.5, status="complete",
    )
    row = st.conn.execute(
        "SELECT original_filename, file_hash, file_size, duration_sec, status, error "
        "FROM jobs WHERE id=?", (jid,)
    ).fetchone()
    assert row["original_filename"] == "upload.pdf"
    assert row["file_hash"] == "abc123"
    assert row["file_size"] == 4096
    assert row["duration_sec"] == 12.5
    assert row["status"] == "complete"
    assert row["error"] is None


def test_save_job_defaults_status_complete(tmp_path):
    # Existing callers (pipeline.py, older tests) don't pass the new kwargs.
    st = _store(tmp_path)
    jid = st.save_job("in.pdf", "out.pdf", [], {})
    row = st.conn.execute("SELECT status FROM jobs WHERE id=?", (jid,)).fetchone()
    assert row["status"] == "complete"


def test_save_failed_job(tmp_path):
    st = _store(tmp_path)
    jid = st.save_job("in.pdf", "", [], {}, status="failed", error="boom")
    row = st.conn.execute("SELECT status, error FROM jobs WHERE id=?", (jid,)).fetchone()
    assert row["status"] == "failed"
    assert row["error"] == "boom"


def test_update_segment_logs_event(tmp_path):
    st = _store(tmp_path)
    jid = st.save_job("in.pdf", "out.pdf",
                      [_seg("a", "The ratio ⟦=5⟧", "The ratio ⟦=5⟧", {"⟦=5⟧": "5"})], {})
    st.update_segment(jid, "a", "La razón ⟦=5⟧", approve=True, reviewer="ana")

    hist = st.get_segment_history(jid, "a")
    assert len(hist) == 1
    assert hist[0]["action"] == "approve"
    assert hist[0]["reviewer"] == "ana"
    assert hist[0]["old_target"] == "The ratio ⟦=5⟧"
    assert hist[0]["new_target"] == "La razón ⟦=5⟧"


def test_rejected_edit_logs_reject_event(tmp_path):
    st = _store(tmp_path)
    jid = st.save_job("in.pdf", "out.pdf",
                      [_seg("a", "Divide ⟦m0⟧ by ⟦m1⟧", None,
                            {"⟦m0⟧": "3", "⟦m1⟧": "4"})], {})
    st.update_segment(jid, "a", "Divide entre ⟦m1⟧", approve=True, reviewer="ana")
    hist = st.get_segment_history(jid, "a")
    assert hist[0]["action"] == "reject"
    assert hist[0]["reviewer"] == "ana"


def test_update_segment_defaults_reviewer_unknown(tmp_path):
    st = _store(tmp_path)
    jid = st.save_job("in.pdf", "out.pdf", [_seg("a", "Hi", "Hi")], {})
    st.update_segment(jid, "a", "Hola", approve=False)
    hist = st.get_segment_history(jid, "a")
    assert hist[0]["reviewer"] == "unknown"
    assert hist[0]["action"] == "edit"


def test_api_endpoints(tmp_path):
    import babel.api as api
    from fastapi.testclient import TestClient

    api._REVIEW_DB = str(tmp_path / "review.db")
    api._TM_DB = str(tmp_path / "tm.db")
    ReviewStore(api._REVIEW_DB, tm_path=api._TM_DB).save_job(
        "in.pdf", "out.pdf",
        [_seg("a", "Solve ⟦m0⟧", "Solve ⟦m0⟧", {"⟦m0⟧": "x"})], {"engine_primary": "identity"})

    client = TestClient(api.app)
    jobs = client.get("/api/jobs").json()
    assert len(jobs) == 1
    jid = jobs[0]["id"]

    segs = client.get(f"/api/jobs/{jid}/segments").json()
    assert segs[0]["seg_id"] == "a"

    r = client.patch(f"/api/segments/{jid}/a",
                     json={"target": "Resuelve ⟦m0⟧", "approve": True}).json()
    assert r["status"] == "approved"
    assert r["target_restored"] == "Resuelve x"

    assert client.get("/api/jobs/nope/segments").json() == []


def test_api_reviewer_and_history(tmp_path):
    import babel.api as api
    from fastapi.testclient import TestClient

    api._REVIEW_DB = str(tmp_path / "review.db")
    api._TM_DB = str(tmp_path / "tm.db")
    ReviewStore(api._REVIEW_DB, tm_path=api._TM_DB).save_job(
        "in.pdf", "out.pdf",
        [_seg("a", "Solve ⟦m0⟧", "Solve ⟦m0⟧", {"⟦m0⟧": "x"})], {})

    client = TestClient(api.app)
    jid = client.get("/api/jobs").json()[0]["id"]
    client.patch(f"/api/segments/{jid}/a",
                 json={"target": "Resuelve ⟦m0⟧", "approve": True, "reviewer": "luis"})

    hist = client.get(f"/api/jobs/{jid}/segments/a/history").json()
    assert hist[0]["reviewer"] == "luis"
    assert hist[0]["action"] == "approve"


def test_translate_pdf_records_duration_and_meta(tmp_path, monkeypatch):
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY", "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    import fitz
    from babel.pipeline import translate_pdf

    src = tmp_path / "doc.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Add the two numbers.", fontsize=14)
    doc.save(str(src))
    doc.close()

    review_db = str(tmp_path / "review.db")
    report = translate_pdf(str(src), out_dir=str(tmp_path / "out"),
                            tm_path=str(tmp_path / "tm.db"), review_db=review_db)

    import sqlite3
    conn = sqlite3.connect(review_db)
    row = conn.execute(
        "SELECT duration_sec, status, meta_json FROM jobs WHERE id=?",
        (report["job_id"],),
    ).fetchone()
    conn.close()
    assert row[0] is not None and row[0] >= 0
    assert row[1] == "complete"
    meta = json.loads(row[2])
    assert "engine_failures" in meta
    assert "disagreements" in meta
    assert "needs_human_count" in meta
    assert "verify_flagged" in meta


def test_translate_pdf_merges_ocr_image_regions_by_default(tmp_path, monkeypatch):
    """A live job (like the API upload path) must pick up text baked into a
    graphic's pixels, not just the PDF's own text objects."""
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY", "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    import fitz
    from babel.models import Line, Span
    from babel.pipeline import translate_pdf

    src = tmp_path / "doc.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Add the two numbers.", fontsize=14)
    doc.save(str(src))
    doc.close()

    banner_line = Line(
        page=0, bbox=(400, 400, 460, 420),
        spans=[Span(text="GO!", font="OCR", size=14, color=0, bbox=(400, 400, 460, 420))],
        block=9000, from_ocr=True, in_image=True,
    )
    import babel.ingest.ocr as ocr_mod
    monkeypatch.setattr(
        ocr_mod, "ocr_image_regions",
        lambda path, regions=None, dpi=300: ([banner_line], "image-OCR (fake): 1 lines"),
    )

    without = translate_pdf(str(src), out_dir=str(tmp_path / "a"),
                            tm_path=str(tmp_path / "tm1.db"), review_db=None, with_ocr=False)
    with_ocr = translate_pdf(str(src), out_dir=str(tmp_path / "b"),
                             tm_path=str(tmp_path / "tm2.db"), review_db=None, with_ocr=True)

    assert with_ocr["segments_total"] == without["segments_total"] + 1
