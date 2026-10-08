"""Photoshop (.psd) and Illustrator (.ai) uploads in Images mode.

A PSD is flattened to its composite and goes through the raster pipeline; it
comes back as PNG, because its layers cannot be written back. An .ai is
translated as vectors, through the same pieces `idml/graphics.py` uses for a
linked .ai, and comes back as an .ai with the same artboard.
"""

import io
import sys
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import pagebirdy.api as api
from pagebirdy import image_api
from pagebirdy.image import pipeline as image_pipeline
from pagebirdy.image import translate as image_translate
from pagebirdy.image import vector as image_vector
from pagebirdy.image.pipeline import translate_image
from pagebirdy.image.validate import ImageValidationError, supported_formats, validate_image_bytes

sys.path.insert(0, str(Path(__file__).parent))
from api_support import wire  # noqa: E402
from image_fixtures import (DictEngine, Scene, TextItem, fake_ocr, make_ai,  # noqa: E402
                            make_psd, render_scene)

SCENE = Scene(items=[TextItem(["Welcome to our store"], 30, 70, size=28)])
AI_TEXT = [("Welcome to our store", 30, 60, 22), ("y = 8x", 30, 150, 14)]
FR = {"Welcome to our store": "Bienvenue dans notre magasin"}


@pytest.fixture(autouse=True)
def _no_real_ocr(monkeypatch):
    # The .ai path reaches ingest/ocr.py; keep every test away from Vision.
    monkeypatch.setenv("BABEL_OCR_ENGINE", "none")


def _filled_rects(page):
    return [d["rect"] for d in page.get_drawings() if d.get("fill")]


# ---- validation -------------------------------------------------------------

def test_both_formats_are_advertised():
    assert {"AI", "PSD"} <= {f["format"] for f in supported_formats()}


def test_psd_is_recognised_by_content_and_comes_back_as_png(tmp_path):
    make_psd(tmp_path / "a.psd", SCENE)
    info = validate_image_bytes((tmp_path / "a.psd").read_bytes())
    assert (info.format, info.kind, info.output_extension) == ("PSD", "raster", ".png")
    assert (info.width, info.height) == (480, 260)


def test_psd_pixel_limit_is_read_from_the_header(tmp_path, monkeypatch):
    make_psd(tmp_path / "a.psd", SCENE)
    monkeypatch.setenv("BABEL_IMAGE_MAX_PIXELS", "1000")
    with pytest.raises(ImageValidationError, match="too many pixels"):
        validate_image_bytes((tmp_path / "a.psd").read_bytes())


def test_corrupt_psd_is_rejected(tmp_path):
    make_psd(tmp_path / "a.psd", SCENE)
    with pytest.raises(ImageValidationError):
        validate_image_bytes((tmp_path / "a.psd").read_bytes()[:40])


def test_illustrator_file_is_accepted_as_vector(tmp_path):
    make_ai(tmp_path / "a.ai", AI_TEXT)
    info = validate_image_bytes((tmp_path / "a.ai").read_bytes())
    assert (info.format, info.kind, info.output_extension) == ("AI", "vector", ".ai")
    assert (info.width, info.height) == (400, 200)


def test_a_plain_pdf_is_sent_to_documents_not_accepted_as_artwork(tmp_path):
    make_ai(tmp_path / "doc.pdf", AI_TEXT, private_data=False, creator="Microsoft Word")
    with pytest.raises(ImageValidationError, match="Documents"):
        validate_image_bytes((tmp_path / "doc.pdf").read_bytes())


def test_postscript_only_illustrator_file_asks_for_pdf_compatibility():
    data = b"%!PS-Adobe-3.0\n%%Creator: Adobe Illustrator(R) 8.0\n%%EndComments\n"
    with pytest.raises(ImageValidationError, match="PDF compatibility"):
        validate_image_bytes(data)


# ---- pipeline ---------------------------------------------------------------

def test_psd_translates_through_the_raster_pipeline(tmp_path):
    regions = make_psd(tmp_path / "poster.psd", SCENE)
    report, _ = translate_image(str(tmp_path / "poster.psd"), str(tmp_path / "out"), "fr",
                                engines=(DictEngine(FR), None), ocr=fake_ocr(regions),
                                verify=False)
    assert report["output"].endswith("poster.fr.png")
    assert (report["input_format"], report["output_format"]) == ("PSD", "PNG")
    with Image.open(report["output"]) as out:
        assert (out.format, out.size) == ("PNG", (480, 260))
    assert Path(report["source_preview"]).exists()
    assert report["regions"][0]["target"] == "Bienvenue dans notre magasin"
    assert report["quality"]["passed"], report["quality"]
    assert any("flattened" in w["message"] for w in report["warnings"])


def test_ai_is_translated_as_vectors_with_the_same_artboard(tmp_path):
    make_ai(tmp_path / "badge.ai", AI_TEXT)
    eng = DictEngine(FR)
    report, _ = translate_image(str(tmp_path / "badge.ai"), str(tmp_path / "out"), "fr",
                                engines=(eng, None), verify=False)
    assert report["output"].endswith("badge.fr.ai") and report["output_format"] == "AI"
    doc = fitz.open(report["output"])
    try:
        assert (doc[0].rect.width, doc[0].rect.height) == (400, 200)
        text = doc[0].get_text().replace("\xa0", " ")
        assert "Bienvenue dans notre magasin" in text and "Welcome" not in text
        assert "y = 8x" in text  # a graph label is left exactly as drawn
        assert _filled_rects(doc[0])  # the artwork is still vector artwork
    finally:
        doc.close()
    assert all("8x" not in s for s in eng.seen)
    assert report["quality"]["passed"], report["quality"]
    assert Path(report["source_preview"]).exists() and Path(report["output_preview"]).exists()
    r = report["regions"][0]
    assert (r["content_type"], r["status"], r["target"]) == (
        "live_text", "translated", "Bienvenue dans notre magasin")


def test_illustrator_native_data_is_removed_so_illustrator_opens_the_translation(tmp_path):
    make_ai(tmp_path / "badge.ai", AI_TEXT)
    assert b"AIPrivateData" in (tmp_path / "badge.ai").read_bytes()
    report, _ = translate_image(str(tmp_path / "badge.ai"), str(tmp_path / "out"), "fr",
                                engines=(DictEngine(FR), None), verify=False)
    data = Path(report["output"]).read_bytes()
    assert b"AIPrivateData" not in data and b"PieceInfo" not in data
    assert report["private_data_removed"] == 1


def test_ai_to_arabic_keeps_the_artboard_unmirrored(tmp_path):
    make_ai(tmp_path / "badge.ai", AI_TEXT)
    report, _ = translate_image(
        str(tmp_path / "badge.ai"), str(tmp_path / "out"), "ar",
        engines=(DictEngine({"Welcome to our store": "مرحبا بكم في متجرنا"}), None), verify=False)
    doc = fitz.open(report["output"])
    try:
        assert _filled_rects(doc[0])[0].x0 > 300  # the square stays on the right
        assert (doc[0].rect.width, doc[0].rect.height) == (400, 200)
    finally:
        doc.close()
    assert report["direction"] == "rtl" and report["quality"]["passed"]


def test_ai_with_no_text_is_returned_unchanged(tmp_path):
    make_ai(tmp_path / "shape.ai", [])
    report, segments = translate_image(str(tmp_path / "shape.ai"), str(tmp_path / "out"), "fr",
                                       engines=(DictEngine({}), None), verify=False)
    assert Path(report["output"]).read_bytes() == (tmp_path / "shape.ai").read_bytes()
    assert any("No translatable text" in w["message"] for w in report["warnings"])


def test_ai_without_ocr_says_outlined_text_was_not_read(tmp_path):
    make_ai(tmp_path / "badge.ai", AI_TEXT)
    report, _ = translate_image(str(tmp_path / "badge.ai"), str(tmp_path / "out"), "fr",
                                engines=(DictEngine(FR), None), verify=False)
    assert any("outlines" in w["message"] for w in report["warnings"])


# ---- API --------------------------------------------------------------------

@pytest.fixture
def client(monkeypatch, tmp_path):
    wire(monkeypatch, tmp_path)
    monkeypatch.setenv("BABEL_IMAGE_VERIFY_OCR", "0")
    _, regions = render_scene(SCENE)
    engines = lambda doc_context="", target_lang=None: (DictEngine(FR), None)  # noqa: E731
    monkeypatch.setattr(image_api, "ocr_engine", lambda: "vision")
    monkeypatch.setattr(image_pipeline, "ocr_engine", lambda: "vision")
    monkeypatch.setattr(image_pipeline, "run_ocr", lambda img: (fake_ocr(regions)(img), "vision"))
    monkeypatch.setattr(image_translate, "build_engines", engines)
    monkeypatch.setattr(image_vector, "build_engines", engines)
    return TestClient(api.app)


def _upload(client, path, name):
    r = client.post("/api/image-translation", data={"target_lang": "fr"},
                    files={"file": (name, path.read_bytes(), "application/octet-stream")})
    assert r.status_code == 200, r.text
    job_id = r.json()["job_id"]
    job = client.get(f"/api/image-translation/{job_id}").json()
    assert job["status"] == "complete", job
    return job_id


def test_api_ai_previews_as_png_and_downloads_as_ai(client, tmp_path):
    make_ai(tmp_path / "badge.ai", AI_TEXT)
    job_id = _upload(client, tmp_path / "badge.ai", "badge.ai")
    for which in ("source", "result"):
        view = client.get(f"/api/image-translation/{job_id}/{which}")
        assert view.status_code == 200 and view.headers["content-type"] == "image/png"
    dl = client.get(f"/api/image-translation/{job_id}/result?download=true")
    assert dl.headers["content-type"] == "application/illustrator"
    assert "badge.fr.ai" in dl.headers["content-disposition"]
    assert dl.content[:5] == b"%PDF-"


def test_api_ai_needs_no_ocr_engine(client, tmp_path, monkeypatch):
    monkeypatch.setattr(image_api, "ocr_engine", lambda: "none")
    make_ai(tmp_path / "badge.ai", AI_TEXT)
    _upload(client, tmp_path / "badge.ai", "badge.ai")


def test_api_psd_previews_source_and_returns_png(client, tmp_path):
    make_psd(tmp_path / "poster.psd", SCENE)
    job_id = _upload(client, tmp_path / "poster.psd", "poster.psd")
    assert client.get(f"/api/image-translation/{job_id}/source").headers["content-type"] == "image/png"
    out = client.get(f"/api/image-translation/{job_id}/result?download=true")
    assert out.headers["content-type"] == "image/png"
    assert "poster.fr.png" in out.headers["content-disposition"]
    with Image.open(io.BytesIO(out.content)) as im:
        assert im.size == (480, 260)
    original = client.get(f"/api/image-translation/{job_id}/source?download=true")
    assert original.content[:4] == b"8BPS"


@pytest.mark.parametrize("kind", ["ai", "psd"])
def test_picked_file_gets_a_png_preview_before_any_job_exists(client, tmp_path, kind):
    path = tmp_path / f"art.{kind}"
    make_ai(path, AI_TEXT) if kind == "ai" else make_psd(path, SCENE)
    r = client.post("/api/image-translation/preview",
                    files={"file": (path.name, path.read_bytes(), "application/octet-stream")})
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    with Image.open(io.BytesIO(r.content)) as im:
        assert im.format == "PNG" and max(im.size) <= 900
    expected = ("400", "200", "pt") if kind == "ai" else ("480", "260", "px")
    assert (r.headers["x-image-width"], r.headers["x-image-height"], r.headers["x-image-units"]) == expected


def test_preview_rejects_a_bad_file_with_the_upload_message(client, tmp_path):
    make_ai(tmp_path / "doc.pdf", AI_TEXT, private_data=False, creator="Microsoft Word")
    r = client.post("/api/image-translation/preview",
                    files={"file": ("doc.ai", (tmp_path / "doc.pdf").read_bytes(), "application/pdf")})
    assert r.status_code == 400 and "Documents" in r.json()["detail"]
