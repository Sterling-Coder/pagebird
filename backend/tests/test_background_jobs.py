import io
import threading
import time

import fitz
import pytest
from fastapi.testclient import TestClient

import pagebirdy.api as api
from pagebirdy.review.store import ReviewStore


def _pdf() -> bytes:
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Hello there.", fontsize=14)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.delenv("PAGEBIRDY_SYNC_JOBS", raising=False)
    monkeypatch.setenv("BABEL_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("BABEL_OUT_DIR", str(tmp_path / "out"))
    api._REVIEW_DB = str(tmp_path / "review.db")
    monkeypatch.setattr(api, "require_trial_active", lambda user: None)
    api.app.dependency_overrides[api.require_user] = lambda: {"id": "u-bg", "email": "a@b.c"}
    yield TestClient(api.app)
    api.app.dependency_overrides.pop(api.require_user, None)


def _job(job_id):
    s = ReviewStore("")
    try:
        return s.get_job(job_id)
    finally:
        s.close()


def _wait_for(predicate, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.05)
    return False


def test_upload_returns_202_at_once_and_the_job_finishes_in_the_background(client, monkeypatch):
    started, release, finished = threading.Event(), threading.Event(), threading.Event()

    def slow_translate(saved, **kw):
        started.set()
        assert release.wait(10)
        finished.set()
        return {"job_id": kw["job_id"]}

    monkeypatch.setattr(api, "translate_pdf", slow_translate)

    t0 = time.time()
    res = client.post("/api/translate", data={"target_lang": "es"},
                      files={"file": ("doc.pdf", io.BytesIO(_pdf()), "application/pdf")})
    assert res.status_code == 202
    assert time.time() - t0 < 5  # did not wait for the translation
    body = res.json()
    assert body["status"] == "processing" and body["format"] == "pdf"

    assert started.wait(5)
    assert _job(body["job_id"])["status"] == "processing"  # visible while it runs
    release.set()
    assert finished.wait(5)


def test_a_failing_translation_is_recorded_on_the_job(client, monkeypatch):
    def boom(saved, **kw):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(api, "translate_pdf", boom)
    res = client.post("/api/translate", data={"target_lang": "es"},
                      files={"file": ("doc.pdf", io.BytesIO(_pdf()), "application/pdf")})
    assert res.status_code == 202
    job_id = res.json()["job_id"]
    assert _wait_for(lambda: _job(job_id)["status"] == "failed")
    assert "model exploded" in _job(job_id)["error"]


def test_sync_mode_still_returns_the_report_and_500s_on_failure(client, monkeypatch):
    monkeypatch.setenv("PAGEBIRDY_SYNC_JOBS", "1")
    monkeypatch.setattr(api, "translate_pdf", lambda saved, **kw: {"job_id": kw["job_id"]})
    ok = client.post("/api/translate", data={"target_lang": "es"},
                     files={"file": ("doc.pdf", io.BytesIO(_pdf()), "application/pdf")})
    assert ok.status_code == 200 and "job_id" in ok.json()

    def boom(saved, **kw):
        raise RuntimeError("nope")

    monkeypatch.setattr(api, "translate_pdf", boom)
    bad = client.post("/api/translate", data={"target_lang": "es"},
                      files={"file": ("doc.pdf", io.BytesIO(_pdf()), "application/pdf")})
    assert bad.status_code == 500 and "translation failed: nope" in bad.json()["detail"]
