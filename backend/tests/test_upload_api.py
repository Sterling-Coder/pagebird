import io
import os

import fitz  # PyMuPDF
from fastapi.testclient import TestClient

import babel.api as api
from babel.review.store import ReviewStore


def _offline(monkeypatch):
    # Force the identity engine so upload runs offline and deterministically.
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY", "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)


def _sample_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Add the two numbers.", fontsize=14)
    data = doc.tobytes()
    doc.close()
    return data


def _wire(monkeypatch, tmp_path):
    api._REVIEW_DB = str(tmp_path / "review.db")
    api._TM_DB = str(tmp_path / "tm.db")
    monkeypatch.setenv("BABEL_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("BABEL_OUT_DIR", str(tmp_path / "out"))


def _make_idml(path):
    import zipfile
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr(
            "Stories/Story_u1.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u1">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Add the two numbers.</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
""",
        )


def test_upload_indd_translates_and_downloads(monkeypatch, tmp_path):
    _offline(monkeypatch)
    _wire(monkeypatch, tmp_path)

    converted_idml = tmp_path / "converted.idml"
    _make_idml(str(converted_idml))
    final_indd = tmp_path / "out" / "doc.es.indd"

    from babel.idml.export import ConvertResult, ExportResult
    import babel.api as api_mod

    def fake_convert(indd_path, out_dir):
        return ConvertResult(ok=True, idml=str(converted_idml), message="ok")

    def fake_export(idml_path, out_dir):
        os.makedirs(os.path.dirname(str(final_indd)), exist_ok=True)
        with open(final_indd, "wb") as f:
            f.write(b"fake-indd-bytes")
        return ExportResult(ok=True, indd=str(final_indd), message="ok")

    monkeypatch.setattr("babel.idml.export.convert_to_idml", fake_convert)
    monkeypatch.setattr("babel.idml.export.export", fake_export)

    client = TestClient(api_mod.app)
    r = client.post(
        "/api/translate",
        files={"file": ("doc.indd", b"fake-indd-source-bytes", "application/octet-stream")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["format"] == "indd"
    assert body["has_output_pdf"] is False
    assert body["output"] == str(final_indd)
    assert body["source"].endswith(".indd")
    jid = body["job_id"]

    dl = client.get(f"/api/jobs/{jid}/download")
    assert dl.status_code == 200
    assert dl.content == b"fake-indd-bytes"
    assert dl.headers["content-type"] == "application/octet-stream"


def test_upload_indd_no_server_configured_fails(monkeypatch, tmp_path):
    _offline(monkeypatch)
    _wire(monkeypatch, tmp_path)
    monkeypatch.delenv("INDESIGN_SERVER", raising=False)

    client = TestClient(api.app)
    r = client.post(
        "/api/translate",
        files={"file": ("doc.indd", b"fake-indd-source-bytes", "application/octet-stream")},
    )
    assert r.status_code == 500
    assert "INDESIGN_SERVER" in r.text


def test_upload_indd_export_failure_cleans_up_job(monkeypatch, tmp_path):
    # translate_idml succeeds (runs for real, offline/identity engine) but the
    # subsequent export() fails — the job row translate_idml persisted
    # internally must not be left behind as a phantom, downloadable job.
    # The outer failure handler still persists one visible "failed" job row
    # (that's the point of failed-job tracking) — just not the phantom one.
    _offline(monkeypatch)
    _wire(monkeypatch, tmp_path)

    converted_idml = tmp_path / "converted.idml"
    _make_idml(str(converted_idml))

    from babel.idml.export import ConvertResult, ExportResult
    import babel.api as api_mod

    def fake_convert(indd_path, out_dir):
        return ConvertResult(ok=True, idml=str(converted_idml), message="ok")

    def fake_export(idml_path, out_dir):
        return ExportResult(ok=False, indd=None, message="InDesign Server error: boom")

    monkeypatch.setattr("babel.idml.export.convert_to_idml", fake_convert)
    monkeypatch.setattr("babel.idml.export.export", fake_export)

    client = TestClient(api_mod.app)
    r = client.post(
        "/api/translate",
        files={"file": ("doc.indd", b"fake-indd-source-bytes", "application/octet-stream")},
    )
    assert r.status_code == 500
    assert "boom" in r.text

    # The phantom job (pointing at the un-exported intermediate .idml) must
    # not survive, but the outer failure handler still records one visible
    # "failed" job so the failure isn't silently lost.
    jobs = client.get("/api/jobs").json()
    assert len(jobs) == 1
    assert jobs[0]["status"] == "failed"
    assert "boom" in jobs[0]["error"]


def test_pdf_upload_translates(monkeypatch, tmp_path):
    _offline(monkeypatch)
    _wire(monkeypatch, tmp_path)
    client = TestClient(api.app)
    r = client.post(
        "/api/translate",
        files={"file": ("doc.pdf", _sample_pdf(), "application/pdf")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["format"] == "pdf"
    assert body["has_output_pdf"] is True
    assert body["job_id"]

    job = client.get(f"/api/jobs/{body['job_id']}").json()
    assert job["original_filename"] == "doc.pdf"


def test_rebuild_after_edit_reflects_new_text(monkeypatch, tmp_path):
    """The editor calls POST .../rebuild after every segment save — it must
    redraw the PDF with the edited text, not just accept the edit into the
    review DB (ReviewStore.update_segment alone never touches the file)."""
    _offline(monkeypatch)
    _wire(monkeypatch, tmp_path)
    client = TestClient(api.app)
    r = client.post(
        "/api/translate",
        files={"file": ("doc.pdf", _sample_pdf(), "application/pdf")},
    )
    job_id = r.json()["job_id"]

    segs = client.get(f"/api/jobs/{job_id}/segments").json()
    seg_id = segs[0]["seg_id"]

    edit = client.patch(f"/api/segments/{job_id}/{seg_id}",
                         json={"target": "Suma los dos numeros.", "approve": True})
    assert edit.status_code == 200

    res = client.post(f"/api/jobs/{job_id}/rebuild")
    assert res.status_code == 200
    output_path = res.json()["output"]
    assert os.path.exists(output_path)

    doc = fitz.open(output_path)
    try:
        text = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()
    normalized = text.replace("\xa0", " ")
    assert "Suma los dos numeros" in normalized
    assert "Add the two numbers" not in normalized


def test_bad_extension_upload_rejected(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    client = TestClient(api.app)
    r = client.post(
        "/api/translate",
        files={"file": ("doc.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400


def test_upload_idml_translates_and_downloads_no_indesign_server(monkeypatch, tmp_path):
    # .idml uploads skip convert_to_idml/export entirely — no INDESIGN_SERVER
    # needed. This is the local/dev unblock: round-trip to .indd stays manual
    # (desktop InDesign File > Save As) until INDESIGN_SERVER is configured.
    _offline(monkeypatch)
    _wire(monkeypatch, tmp_path)
    monkeypatch.delenv("INDESIGN_SERVER", raising=False)

    idml_bytes = io.BytesIO()
    import zipfile
    with zipfile.ZipFile(idml_bytes, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr(
            "Stories/Story_u1.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u1">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Add the two numbers.</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
""",
        )

    client = TestClient(api.app)
    r = client.post(
        "/api/translate",
        files={"file": ("doc.idml", idml_bytes.getvalue(), "application/octet-stream")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["format"] == "idml"
    assert body["has_output_pdf"] is False
    jid = body["job_id"]

    dl = client.get(f"/api/jobs/{jid}/download")
    assert dl.status_code == 200
    assert dl.headers["content-type"] == "application/octet-stream"


def test_upload_idml_logs_progress(monkeypatch, tmp_path, caplog):
    import logging

    _offline(monkeypatch)
    _wire(monkeypatch, tmp_path)
    monkeypatch.delenv("INDESIGN_SERVER", raising=False)

    idml_bytes = io.BytesIO()
    import zipfile
    with zipfile.ZipFile(idml_bytes, "w") as z:
        z.writestr("mimetype", "application/vnd.adobe.indesign-idml-package")
        z.writestr("designmap.xml", "<Document/>")
        z.writestr(
            "Stories/Story_u1.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <Story Self="u1">
    <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/Body">
      <CharacterStyleRange>
        <Properties><AppliedFont type="string">Minion Pro</AppliedFont></Properties>
        <Content>Add the two numbers.</Content>
      </CharacterStyleRange>
    </ParagraphStyleRange>
  </Story>
</idPkg:Story>
""",
        )

    client = TestClient(api.app)
    with caplog.at_level(logging.INFO, logger="babel.api"):
        r = client.post(
            "/api/translate",
            files={"file": ("doc.idml", idml_bytes.getvalue(), "application/octet-stream")},
        )
    assert r.status_code == 200, r.text

    messages = [rec.message for rec in caplog.records]
    assert any("doc.idml" in m for m in messages)  # upload received
    assert any("complete" in m.lower() for m in messages)  # pipeline finished


def test_download_unknown_job_404(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    client = TestClient(api.app)
    assert client.get("/api/jobs/nope/download").status_code == 404


def test_bad_extension_rejected(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    client = TestClient(api.app)
    r = client.post("/api/translate", files={"file": ("notes.txt", b"hi", "text/plain")})
    assert r.status_code == 400


def test_source_unknown_job_404(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    client = TestClient(api.app)
    assert client.get("/api/jobs/nope/source").status_code == 404


def test_failed_translation_persists_job(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    monkeypatch.delenv("INDESIGN_SERVER", raising=False)
    client = TestClient(api.app)

    # No INDESIGN_SERVER configured: convert_to_idml fails before any real
    # conversion is attempted, so this is a deterministic pipeline failure.
    r = client.post(
        "/api/translate",
        files={"file": ("broken.indd", b"not a real indd", "application/octet-stream")},
    )
    assert r.status_code == 500

    jobs = client.get("/api/jobs").json()
    assert len(jobs) == 1
    assert jobs[0]["status"] == "failed"
    assert jobs[0]["error"]
    assert jobs[0]["original_filename"] == "broken.indd"
    assert jobs[0]["file_size"] == len(b"not a real indd")


def test_output_404_for_idml_without_preview(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    # Save a job whose output is an .es.idml with no sibling preview PDF.
    from babel.models import Segment

    store = ReviewStore(api._REVIEW_DB, tm_path=api._TM_DB)
    jid = store.save_job(
        str(tmp_path / "in.idml"),
        str(tmp_path / "out" / "in.es.idml"),
        [Segment(id="a", page=0, bbox=(0, 0, 1, 1), font="f", size=11, color=0,
                 source="Solve", target="Solve", status="translated")],
        {"format": "idml"},
    )
    store.close()
    client = TestClient(api.app)
    assert client.get(f"/api/jobs/{jid}/output").status_code == 404
