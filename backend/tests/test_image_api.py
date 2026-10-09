"""The image-translation endpoints, end to end through FastAPI.

OCR and the engine are swapped for deterministic stand-ins; everything else —
validation, the background task, the job row in the review store, the report
file, file serving — is the real thing.
"""

import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import pagebirdy.api as api
from pagebirdy import image_api
from pagebirdy.image import pipeline as image_pipeline
from pagebirdy.image import translate as image_translate

sys.path.insert(0, str(Path(__file__).parent))
from api_support import wire  # noqa: E402
from image_fixtures import DictEngine, Scene, TextItem, fake_ocr, render_scene  # noqa: E402

SCENE = Scene(items=[TextItem(["Welcome to our store"], 30, 70, size=28),
                     TextItem(["www.example.com"], 30, 160, size=18),
                     TextItem(["Faded text"], 30, 220, size=18, confidence=0.5)])
TABLE = {"Welcome to our store": "Bienvenue dans notre magasin"}


@pytest.fixture
def client(monkeypatch, tmp_path):
    wire(monkeypatch, tmp_path)
    monkeypatch.setenv("BABEL_IMAGE_VERIFY_OCR", "0")
    _, regions = render_scene(SCENE)
    monkeypatch.setattr(image_api, "ocr_engine", lambda: "vision")
    monkeypatch.setattr(image_pipeline, "ocr_engine", lambda: "vision")
    monkeypatch.setattr(image_pipeline, "run_ocr", lambda img: (fake_ocr(regions)(img), "vision"))
    monkeypatch.setattr(image_translate, "build_engines",
                        lambda doc_context="", target_lang=None: (DictEngine(TABLE), None))
    return TestClient(api.app)


def _png(scene=SCENE, fmt="PNG"):
    img, _ = render_scene(scene)
    buf = io.BytesIO()
    img.save(buf, fmt)
    return buf.getvalue()


def _post(client, data=None, name="poster.png", **form):
    form.setdefault("target_lang", "fr")
    return client.post("/api/image-translation", data=form,
                       files={"file": (name, data if data is not None else _png(), "image/png")})


def test_config_advertises_only_what_the_backend_handles(client):
    cfg = client.get("/api/image-translation/config").json()
    names = {f["format"] for f in cfg["formats"]}
    assert {"PNG", "JPEG"} <= names and "GIF" not in names
    assert [s["key"] for s in cfg["stages"]][:3] == ["uploading", "validation", "ocr"]
    assert cfg["ocr_available"] is True


def test_upload_runs_the_job_and_reports_the_result(client):
    r = _post(client)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "regions" not in body  # the answer stays small

    job = client.get(f"/api/image-translation/{body['job_id']}").json()
    assert job["status"] == "complete" and job["stage"] == "completed"
    assert job["target_lang"] == "fr" and job["source_lang"] == "en"
    assert job["stage_progress"]["quality"] == 100
    assert job["report"]["quality"]["checks"]


def test_result_is_the_translated_image_at_the_same_size(client):
    job_id = _post(client).json()["job_id"]
    res = client.get(f"/api/image-translation/{job_id}/result")
    assert res.status_code == 200 and res.headers["content-type"] == "image/png"
    assert res.headers["content-disposition"].startswith("inline")
    with Image.open(io.BytesIO(res.content)) as out, Image.open(io.BytesIO(_png())) as src:
        assert out.size == src.size
    dl = client.get(f"/api/image-translation/{job_id}/result?download=true")
    assert dl.headers["content-disposition"].startswith("attachment")
    assert "poster.fr.png" in dl.headers["content-disposition"]
    assert client.get(f"/api/image-translation/{job_id}/source").status_code == 200


def test_ocr_listing_shows_protected_and_low_confidence_regions(client):
    job_id = _post(client).json()["job_id"]
    ocr = client.get(f"/api/image-translation/{job_id}/ocr").json()
    by_text = {r["text"]: r for r in ocr["regions"]}
    assert by_text["Welcome to our store"]["target"] == "Bienvenue dans notre magasin"
    assert by_text["www.example.com"]["action"] == "protect"
    faded = by_text["Faded text"]
    assert faded["content_type"] == "low_confidence" and faded["status"] == "needs_human"
    assert faded["warnings"]


def test_job_is_persisted_in_the_review_store_with_its_segments(client):
    job_id = _post(client).json()["job_id"]
    job = client.get(f"/api/jobs/{job_id}").json()
    assert job["meta"]["format"] == "image" and job["status"] == "complete"
    segs = client.get(f"/api/jobs/{job_id}/segments").json()
    assert [s["source"] for s in segs] == ["Welcome to our store"]


@pytest.mark.parametrize("data,name,form,status,needle", [
    (b"not an image", "x.png", {}, 400, "not a readable image"),
    (None, "x.png", {"target_lang": ""}, 400, "target language"),
    (None, "x.png", {"target_lang": "xx"}, 400, "Unsupported target language"),
    (None, "x.png", {"source_lang": "de"}, 400, "English"),
])
def test_bad_requests_are_rejected_before_any_work(client, data, name, form, status, needle):
    r = _post(client, data=data, name=name, **form)
    assert r.status_code == status and needle in r.json()["detail"]


def test_unsupported_format_is_rejected(client):
    buf = io.BytesIO()
    Image.new("RGB", (64, 64)).save(buf, "GIF")
    r = _post(client, data=buf.getvalue(), name="a.png")  # the name lies; the content decides
    assert r.status_code == 400 and "Unsupported image format" in r.json()["detail"]


def test_no_ocr_engine_is_a_clear_503(client, monkeypatch):
    monkeypatch.setattr(image_api, "ocr_engine", lambda: "none")
    r = _post(client)
    assert r.status_code == 503 and "OCR" in r.json()["detail"]


def test_path_traversal_in_the_filename_is_neutralised(client):
    job_id = _post(client, name="../../evil.png").json()["job_id"]
    job = client.get(f"/api/image-translation/{job_id}").json()
    assert job["original_filename"] == "evil.png"
    assert api._find_job(job_id)["source"] == f"jobs/{job_id}/evil.png"


def test_engine_failure_is_persisted_without_internal_detail(client, monkeypatch):
    class Boom(DictEngine):
        def translate(self, texts):
            raise RuntimeError("secret-api-key sk-123 at /internal/path")

    monkeypatch.setattr(image_translate, "build_engines",
                        lambda doc_context="", target_lang=None: (Boom({}), None))
    r = _post(client)
    assert r.status_code == 500
    assert "sk-123" not in r.json()["detail"] and "/internal" not in r.json()["detail"]
    job = next(j for j in client.get("/api/jobs").json() if j["meta"]["format"] == "image")
    assert job["status"] == "failed" and job["meta"]["failed_stage"] == "translation"
    assert "sk-123" not in (job["error"] or "")
    assert client.get(f"/api/image-translation/{job['id']}/result").status_code == 409


def test_unknown_job_is_404(client):
    assert client.get("/api/image-translation/nope").status_code == 404


def test_document_translate_endpoint_still_rejects_images(client):
    r = client.post("/api/translate", data={"target_lang": "fr"},
                    files={"file": ("a.png", _png(), "image/png")})
    assert r.status_code == 400
