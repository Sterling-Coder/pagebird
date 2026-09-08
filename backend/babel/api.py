"""FastAPI review API — backs the human-review UI.

    GET  /api/jobs                       list jobs + status counts
    GET  /api/jobs/{id}/segments?status= segments (optionally filtered)
    PATCH /api/segments/{job}/{seg}      { target, approve, reviewer } edit/approve one
    GET  /api/jobs/{id}/segments/{seg}/history  audit trail for one segment
    GET  /api/jobs/{id}/eval?refresh=    accuracy scorecard (gates + layout + integrity)
    GET  /api/jobs/{id}/eval/download?format=pdf|md|json   same scorecard as a file
    GET  /api/health
    GET  /api/languages                  target languages the UI can offer
    POST /api/translate                  upload + translate an INDD file
    GET  /api/jobs/{job_id}/source       serve source PDF (PDF-path jobs only)
    GET  /api/jobs/{job_id}/output       serve output PDF (PDF-path jobs only)
    GET  /api/jobs/{job_id}/download     serve the translated .indd

Run:  .venv/bin/uvicorn babel.api:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
import os.path
import threading
from collections import deque

from babel.config import load_env

load_env()

import requests
from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel

from babel import languages
from babel.auth import effective_owner_ids, get_or_create_profile, require_trial_active, require_user
from babel.pipeline import rebuild_from_edits, regenerate_idml_from_review, translate_idml, translate_pdf
from babel.review.store import ReviewStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger("babel.api")

# ---- in-app log tail --------------------------------------------------
# Lets the frontend show what the server is doing (upload received, LLM
# calls, pipeline stages) without a separate terminal. A bounded ring
# buffer of formatted lines, fed by a logging.Handler attached to the
# root logger so it picks up babel.*, uvicorn.access, and httpx request
# logs alike. Polled via GET /api/logs — no SSE, simplest thing that works.
_LOG_BUFFER: deque[dict] = deque(maxlen=1000)
_LOG_LOCK = threading.Lock()
_LOG_NEXT_ID = 0


class _BufferLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        global _LOG_NEXT_ID
        try:
            line = self.format(record)
        except Exception:
            return
        with _LOG_LOCK:
            _LOG_NEXT_ID += 1
            _LOG_BUFFER.append({
                "id": _LOG_NEXT_ID,
                "level": record.levelname,
                "logger": record.name,
                "line": line,
            })


_buffer_handler = _BufferLogHandler()
_buffer_handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
logging.getLogger().addHandler(_buffer_handler)
logging.getLogger().setLevel(logging.INFO)

_REVIEW_DB = os.environ.get("BABEL_REVIEW_DB", "babel_review.db")
_TM_DB = os.environ.get("BABEL_TM_DB", "babel_tm.db")
_UPLOAD_DIR = os.environ.get("BABEL_UPLOAD_DIR", "uploads")
_OUT_DIR = os.environ.get("BABEL_OUT_DIR", "out")

app = FastAPI(title="babel review")
_frontend_origins = [
    o.strip() for o in os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_frontend_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


def _store() -> ReviewStore:
    return ReviewStore(_REVIEW_DB, tm_path=_TM_DB)


def _upload_dir() -> str:
    return os.environ.get("BABEL_UPLOAD_DIR", _UPLOAD_DIR)


def _out_dir() -> str:
    return os.environ.get("BABEL_OUT_DIR", _OUT_DIR)


def _find_job(job_id: str) -> dict | None:
    s = _store()
    try:
        for j in s.list_jobs():
            if j["id"] == job_id:
                return j
        return None
    finally:
        s.close()


def _assert_owns_project(store: ReviewStore, project_id: str, user: dict) -> dict:
    """404 if the project doesn't exist, 403 if it belongs to someone outside
    the caller's team (or predates auth and has no owner — same effect,
    treated as orphaned)."""
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    if project.get("created_by") not in effective_owner_ids(user["id"]):
        raise HTTPException(status_code=403, detail="not your project")
    return project


def _assert_owns_folder(store: ReviewStore, folder_id: str, user: dict) -> dict:
    folder = store.get_folder(folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="folder not found")
    _assert_owns_project(store, folder["project_id"], user)
    return folder


def _find_owned_job(job_id: str, user: dict) -> dict:
    job = _find_job(job_id)
    if job is None or job.get("created_by") not in effective_owner_ids(user["id"]):
        raise HTTPException(status_code=404, detail="job not found")
    return job


def _output_pdf_path(output: str) -> str:
    """The browser-renderable PDF for a job output.

    PDF jobs: the output itself. IDML jobs: the deterministic .pdf sibling
    of the .es.idml (produced only when INDESIGN_SERVER exported one)."""
    if output.lower().endswith(".pdf"):
        return output
    return os.path.splitext(output)[0] + ".pdf"


class SegmentEdit(BaseModel):
    target: str
    approve: bool = False
    reviewer: str = "unknown"


class ProjectCreate(BaseModel):
    name: str
    job_type: str = "document"
    source_lang: str | None = None
    target_lang: str | None = None
    client: str | None = None
    vendor: str | None = None
    deadline: float | None = None


class FolderCreate(BaseModel):
    name: str
    parent_folder_id: str | None = None


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/logs")
def get_logs(since: int = 0) -> dict:
    """Log lines newer than `since` (the `id` of the last line the caller
    already has). Poll this with the last-seen id to tail the server."""
    with _LOG_LOCK:
        lines = [entry for entry in _LOG_BUFFER if entry["id"] > since]
    return {"lines": lines}


@app.post("/api/projects")
def create_project(body: ProjectCreate, user: dict = Depends(require_user)) -> dict:
    s = _store()
    try:
        project_id = s.create_project(
            body.name, body.job_type,
            source_lang=body.source_lang, target_lang=body.target_lang,
            client=body.client, vendor=body.vendor, deadline=body.deadline,
            created_by=user["id"],
        )
        return s.get_project(project_id)
    finally:
        s.close()


@app.get("/api/projects")
def list_projects(user: dict = Depends(require_user)) -> list[dict]:
    s = _store()
    try:
        return s.list_projects(created_by=effective_owner_ids(user["id"]))
    finally:
        s.close()


@app.get("/api/projects/{project_id}")
def get_project(project_id: str, user: dict = Depends(require_user)) -> dict:
    s = _store()
    try:
        return _assert_owns_project(s, project_id, user)
    finally:
        s.close()


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str, user: dict = Depends(require_user)) -> dict:
    s = _store()
    try:
        _assert_owns_project(s, project_id, user)
        s.delete_project(project_id)
    finally:
        s.close()
    return {"ok": True}


@app.post("/api/projects/{project_id}/folders")
def create_folder(project_id: str, body: FolderCreate, user: dict = Depends(require_user)) -> dict:
    s = _store()
    try:
        _assert_owns_project(s, project_id, user)
        if body.parent_folder_id is not None:
            _assert_owns_folder(s, body.parent_folder_id, user)
        folder_id = s.create_folder(project_id, body.name, body.parent_folder_id)
        return s.get_folder(folder_id)
    finally:
        s.close()


@app.get("/api/projects/{project_id}/folders")
def list_folders(project_id: str, parent_folder_id: str | None = None,
                  user: dict = Depends(require_user)) -> list[dict]:
    s = _store()
    try:
        _assert_owns_project(s, project_id, user)
        return s.list_folders(project_id, parent_folder_id)
    finally:
        s.close()


@app.get("/api/folders/{folder_id}")
def get_folder(folder_id: str, user: dict = Depends(require_user)) -> dict:
    s = _store()
    try:
        return _assert_owns_folder(s, folder_id, user)
    finally:
        s.close()


@app.delete("/api/folders/{folder_id}")
def delete_folder(folder_id: str, user: dict = Depends(require_user)) -> dict:
    s = _store()
    try:
        _assert_owns_folder(s, folder_id, user)
        s.delete_folder(folder_id)
    finally:
        s.close()
    return {"ok": True}


@app.get("/api/projects/{project_id}/files")
def list_project_files(project_id: str, folder_id: str | None = None,
                        all: bool = False, user: dict = Depends(require_user)) -> list[dict]:
    s = _store()
    try:
        _assert_owns_project(s, project_id, user)
        jobs = s.list_jobs(created_by=effective_owner_ids(user["id"]))
    finally:
        s.close()
    if all:
        return [j for j in jobs if j.get("project_id") == project_id]
    return [
        j for j in jobs
        if j.get("project_id") == project_id and j.get("folder_id") == folder_id
    ]


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, user: dict = Depends(require_user)) -> dict:
    return _find_owned_job(job_id, user)


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, user: dict = Depends(require_user)) -> dict:
    _find_owned_job(job_id, user)
    s = _store()
    try:
        s.delete_job(job_id)
    finally:
        s.close()
    return {"ok": True}


@app.get("/api/jobs/{job_id}/history")
def get_job_history(job_id: str, user: dict = Depends(require_user)) -> list[dict]:
    _find_owned_job(job_id, user)
    s = _store()
    try:
        return s.get_job_history(job_id)
    finally:
        s.close()


@app.get("/api/jobs")
def list_jobs(user: dict = Depends(require_user)) -> list[dict]:
    s = _store()
    try:
        return s.list_jobs(created_by=effective_owner_ids(user["id"]))
    finally:
        s.close()


@app.get("/api/jobs/{job_id}/segments")
def get_segments(job_id: str, status: str | None = None,
                  user: dict = Depends(require_user)) -> list[dict]:
    _find_owned_job(job_id, user)
    s = _store()
    try:
        return s.get_segments(job_id, status=status)
    finally:
        s.close()


@app.patch("/api/segments/{job_id}/{seg_id}")
def update_segment(job_id: str, seg_id: str, edit: SegmentEdit,
                    user: dict = Depends(require_user)) -> dict:
    _find_owned_job(job_id, user)
    s = _store()
    try:
        return s.update_segment(job_id, seg_id, edit.target, edit.approve, reviewer=edit.reviewer)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        s.close()


@app.get("/api/jobs/{job_id}/segments/{seg_id}/history")
def get_segment_history(job_id: str, seg_id: str, user: dict = Depends(require_user)) -> list[dict]:
    _find_owned_job(job_id, user)
    s = _store()
    try:
        return s.get_segment_history(job_id, seg_id)
    finally:
        s.close()


@app.post("/api/jobs/{job_id}/rebuild")
async def rebuild_job(job_id: str, user: dict = Depends(require_user)) -> dict:
    """Redraw a job's output file from the review store's current
    target/status per segment — call after editing/approving a segment so
    the preview/download reflect it. PDF jobs re-extract and reassemble;
    IDML jobs re-apply onto a fresh copy of the source .idml."""
    job = _find_owned_job(job_id, user)
    require_trial_active(user)

    is_idml = str(job.get("output", "")).lower().endswith(".idml")

    def _run() -> str:
        if is_idml:
            return regenerate_idml_from_review(job, review_db=_REVIEW_DB)
        return rebuild_from_edits(job_id, out_dir=_out_dir(), review_db=_REVIEW_DB)

    try:
        output = await run_in_threadpool(_run)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("rebuild failed for job %s", job_id)
        raise HTTPException(status_code=500, detail=f"rebuild failed: {e}")

    return {"ok": True, "output": output}


def _eval_cache_path(job_id: str) -> str:
    return os.path.join(_out_dir(), "eval", f"{job_id}.eval.json")


async def _eval_report(job_id: str, user: dict, refresh: bool = False) -> dict:
    """Scorecard for a job, from cache when possible. Shared by view + download.

    Deliberately the *cheap* tier only — no model download, no engine calls, no
    network. The neural metrics (COMET-KIWI) and the MQM judge are minutes of
    work and a 2.3GB checkpoint, so they belong in a background job rather than
    on a request the UI is waiting for. Run them from the CLI:

        python -m babel.eval job <id> --neural --mqm

    Cached to out/eval/<job_id>.eval.json because the layout metrics re-render
    every page. `refresh` recomputes — needed after approving edits, since
    integrity rates move as segments change.
    """
    import json

    _find_owned_job(job_id, user)

    cache = _eval_cache_path(job_id)
    if not refresh and os.path.exists(cache):
        try:
            with open(cache, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass  # unreadable cache is not an error, just recompute

    from babel.eval import runner

    def _run() -> dict:
        return runner.evaluate_job(job_id, review_db=_REVIEW_DB)

    try:
        report = await run_in_threadpool(_run)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.info("eval failed for job %s: %s", job_id, e)
        raise HTTPException(status_code=500, detail=f"evaluation failed: {e}")

    os.makedirs(os.path.dirname(cache), exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report


@app.get("/api/jobs/{job_id}/eval")
async def get_eval(job_id: str, refresh: bool = False, user: dict = Depends(require_user)) -> dict:
    """Accuracy scorecard for one job: gates, layout fidelity, content integrity."""
    return JSONResponse(
        await _eval_report(job_id, user, refresh=refresh),
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


def _report_filename(job: dict | None, job_id: str, ext: str) -> str:
    """A download name a person can recognise in their Downloads folder."""
    stem = os.path.splitext(os.path.basename(
        (job or {}).get("original_filename") or (job or {}).get("source") or job_id
    ))[0]
    # Keep it filesystem- and header-safe: uploads carry arbitrary user names,
    # and a quote or newline in Content-Disposition is a header-injection bug.
    safe = "".join(c for c in stem if c.isalnum() or c in "-_. ").strip() or job_id
    return f"{safe}-accuracy.{ext}"


_REPORT_FORMATS = ("pdf", "md", "json")


@app.get("/api/jobs/{job_id}/eval/download")
async def download_eval(job_id: str, format: str = "pdf", refresh: bool = False,
                         user: dict = Depends(require_user)) -> Response:
    """The scorecard as a file.

    `pdf` is the shareable artefact, `md` the same content as text, `json` the
    raw data for scripting. PDF rendering is CPU work (PyMuPDF lays out the
    whole document), so it runs off the event loop like the scoring itself.
    """
    import json

    if format not in _REPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"format must be one of {', '.join(_REPORT_FORMATS)}")

    report = await _eval_report(job_id, user, refresh=refresh)

    if format == "json":
        body = json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8")
        media = "application/json; charset=utf-8"
    elif format == "md":
        from babel.eval import scorecard

        body = scorecard.render_markdown(report).encode("utf-8")
        media = "text/markdown; charset=utf-8"
    else:
        from babel.eval import report_pdf

        body = await run_in_threadpool(report_pdf.render_pdf, report)
        media = "application/pdf"

    filename = _report_filename(_find_job(job_id), job_id, format)
    return Response(
        content=body,
        media_type=media,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            # The URL never changes, so a browser will happily re-serve an old
            # report from disk cache and the reader sees stale numbers after a
            # rescore. A scorecard must always be the current one.
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )


_UI_DEFAULT_LANG = "zh"  # UI-only default; pipeline's implicit fallback stays languages.DEFAULT


@app.get("/api/languages")
def list_languages() -> dict:
    """Target languages the UI may offer, and which ones the PDF path renders."""
    return {"languages": languages.listing(), "default": _UI_DEFAULT_LANG}


@app.post("/api/translate")
async def translate_upload(
    file: UploadFile = File(...),
    target_lang: str = Form(default=""),
    project_id: str = Form(default=""),
    folder_id: str = Form(default=""),
    user: dict = Depends(require_user),
) -> dict:
    import hashlib
    import time

    require_trial_active(user)

    if project_id:
        s = _store()
        try:
            _assert_owns_project(s, project_id, user)
        finally:
            s.close()

    name = file.filename or ""
    ext = os.path.splitext(name)[1].lower()
    if ext not in (".pdf", ".indd", ".idml"):
        raise HTTPException(status_code=400, detail="upload a .pdf, .indd or .idml file")
    try:
        lang = languages.get(target_lang or None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    upload_dir = _upload_dir()
    os.makedirs(upload_dir, exist_ok=True)
    # De-dupe filename so distinct uploads with the same name don't clobber.
    import uuid

    stem, dot_ext = os.path.splitext(os.path.basename(name))
    saved = os.path.join(upload_dir, f"{stem}-{uuid.uuid4().hex[:8]}{dot_ext}")
    data = await file.read()
    with open(saved, "wb") as f:
        f.write(data)

    file_hash = hashlib.sha256(data).hexdigest()
    file_size = len(data)
    started = time.time()

    logger.info("upload received: %s (%d bytes) ext=%s target_lang=%s",
                name, file_size, ext, lang.code)

    # Translation is blocking (network LLM calls). Run it off the event loop
    # so a single upload doesn't freeze the whole server for other requests.
    def _run() -> dict:
        from babel.idml.export import convert_to_idml, export

        if ext == ".pdf":
            logger.info("upload: .pdf path, running translate_pdf directly for %s", name)
            report = translate_pdf(saved, out_dir=_out_dir(), tm_path=_TM_DB,
                                   review_db=_REVIEW_DB, target_lang=lang.code,
                                   project_id=project_id or None, folder_id=folder_id or None, created_by=user["id"],
                                   original_filename=name)
            report["format"] = "pdf"
            report["has_output_pdf"] = True
            logger.info("upload: pipeline complete for %s (job_id=%s)",
                        name, report.get("job_id"))
            return report

        if ext == ".idml":
            # No INDESIGN_SERVER needed for this path: the .idml is already
            # the format translate_idml understands, and the translated
            # .idml itself is a valid deliverable (round-trip to .indd is a
            # manual File > Save As in desktop InDesign). Lets local/dev use
            # exercise the full translate core without InDesign Server.
            logger.info("upload: .idml path, running translate_idml directly for %s", name)
            report = translate_idml(saved, out_dir=_out_dir(), tm_path=_TM_DB,
                                    review_db=_REVIEW_DB, target_lang=lang.code,
                                    project_id=project_id or None, folder_id=folder_id or None, created_by=user["id"],
                                    original_filename=name)
            report["format"] = "idml"
            report["has_output_pdf"] = False
            logger.info("upload: pipeline complete for %s (job_id=%s)",
                        name, report.get("job_id"))
            return report

        conv = convert_to_idml(saved, _out_dir())
        if not conv.ok:
            raise RuntimeError(conv.message)

        report = translate_idml(conv.idml, out_dir=_out_dir(), tm_path=_TM_DB,
                                review_db=_REVIEW_DB, target_lang=lang.code,
                                project_id=project_id or None, folder_id=folder_id or None, created_by=user["id"],
                                original_filename=name)
        report["source"] = saved  # show the original .indd name, not the intermediate .idml

        exp = export(report["output"], _out_dir())
        if not exp.ok:
            # translate_idml already persisted a job row pointing at the
            # intermediate .idml. Since export failed, that job has no usable
            # deliverable (no PDF fallback in this INDD-only flow) — delete it
            # so it doesn't stay browsable/downloadable as a phantom success.
            job_id = report.get("job_id")
            if job_id:
                store = _store()
                try:
                    store.delete_job(job_id)
                finally:
                    store.close()
            raise RuntimeError(exp.message)

        report["output"] = exp.indd
        report["format"] = "indd"
        report["has_output_pdf"] = False

        # translate_idml already persisted a job record pointing at the
        # intermediate .idml source/output — repoint it at the original
        # upload and the final exported .indd so /source, /output, and
        # /download all resolve the right files.
        job_id = report.get("job_id")
        if job_id:
            store = _store()
            try:
                store.update_job_paths(job_id, source=saved, output=exp.indd)
            finally:
                store.close()

        return report

    try:
        report = await run_in_threadpool(_run)
    except Exception as e:  # surface pipeline failure to the UI, but still record it
        logger.info("upload: pipeline failed for %s: %s", name, e)
        store = _store()
        try:
            store.save_job(
                saved, "", [], {},
                original_filename=name, file_hash=file_hash, file_size=file_size,
                duration_sec=time.time() - started, status="failed", error=str(e),
                created_by=user["id"],
            )
        finally:
            store.close()
        raise HTTPException(status_code=500, detail=f"translation failed: {e}")

    if project_id:
        store = _store()
        try:
            store.set_project_target_lang_if_unset(project_id, lang.code)
        finally:
            store.close()

    return report


@app.get("/api/jobs/{job_id}/source")
def get_source(job_id: str, user: dict = Depends(require_user)) -> FileResponse:
    job = _find_owned_job(job_id, user)
    if not str(job["source"]).lower().endswith(".pdf") or not os.path.exists(job["source"]):
        raise HTTPException(status_code=404, detail="no renderable source")
    return FileResponse(job["source"], media_type="application/pdf")


@app.get("/api/jobs/{job_id}/output")
def get_output(job_id: str, user: dict = Depends(require_user)) -> FileResponse:
    job = _find_owned_job(job_id, user)
    pdf = _output_pdf_path(job["output"])
    if not os.path.exists(pdf):
        raise HTTPException(status_code=404, detail="no renderable output pdf")
    return FileResponse(pdf, media_type="application/pdf")


@app.get("/api/jobs/{job_id}/download")
def download_output(job_id: str, format: str | None = None, type: str | None = None,
                     user: dict = Depends(require_user)) -> FileResponse:
    job = _find_owned_job(job_id, user)

    out = str(job["output"])
    fmt = (format or "").lower().strip()
    target_type = (type or "").lower().strip()
    source = str(job.get("source", ""))

    # If source file requested
    if target_type == "source" or fmt == "source":
        if fmt == "idml":
            if source.lower().endswith(".idml") and os.path.exists(source):
                return FileResponse(source, media_type="application/octet-stream", filename=os.path.basename(source))
            src_idml = os.path.splitext(source)[0] + ".idml"
            if os.path.exists(src_idml):
                return FileResponse(src_idml, media_type="application/octet-stream", filename=os.path.basename(src_idml))
        if os.path.exists(source):
            filename = os.path.basename(source)
            media = "application/pdf" if filename.lower().endswith(".pdf") else "application/octet-stream"
            return FileResponse(source, media_type=media, filename=filename)
        raise HTTPException(status_code=404, detail="Source file not found")

    if fmt == "pdf":
        pdf_path = _output_pdf_path(out)
        if os.path.exists(pdf_path):
            filename = os.path.basename(pdf_path)
            return FileResponse(pdf_path, media_type="application/pdf", filename=filename)
        if source.lower().endswith(".pdf") and os.path.exists(source):
            return FileResponse(source, media_type="application/pdf", filename=os.path.basename(source))
        raise HTTPException(status_code=404, detail="PDF format not found for this job")

    if fmt == "idml":
        meta = job.get("meta") or {}
        if meta.get("format") == "idml" and source.lower().endswith(".idml") \
                and os.path.exists(source):
            # Review-store approvals/edits made after the initial MT export
            # never get written back to the saved .idml on their own — bring
            # the file up to date before serving it (see
            # pipeline.regenerate_idml_from_review).
            from babel.pipeline import regenerate_idml_from_review
            try:
                regenerate_idml_from_review(job, review_db=_REVIEW_DB)
            except Exception:
                logger.exception("download: failed to regenerate idml for job %s", job_id)
        if out.lower().endswith(".idml") and os.path.exists(out):
            return FileResponse(out, media_type="application/octet-stream", filename=os.path.basename(out))
        idml_path = os.path.splitext(out)[0] + ".idml"
        if os.path.exists(idml_path):
            return FileResponse(idml_path, media_type="application/octet-stream", filename=os.path.basename(idml_path))
        if source.lower().endswith(".idml") and os.path.exists(source):
            return FileResponse(source, media_type="application/octet-stream", filename=os.path.basename(source))
        raise HTTPException(status_code=404, detail="IDML format not available for this job")

    if not os.path.exists(out):
        raise HTTPException(status_code=404, detail="output not found")
    return FileResponse(job["output"], media_type="application/octet-stream",
                        filename=os.path.basename(job["output"]))



class TeamInvite(BaseModel):
    email: str


@app.get("/api/me")
def get_me(user: dict = Depends(require_user)) -> dict:
    """Signed-in user's profile — email, member-since, trial status.
    Self-heals a missing profile row (accounts created before the trial
    trigger existed)."""
    profile = get_or_create_profile(user)
    return {
        "id": user["id"],
        "email": profile.get("email") or user.get("email"),
        "created_at": profile.get("created_at"),
        "trial_ends_at": profile.get("trial_ends_at"),
    }



class TeamAccept(BaseModel):
    owner_id: str


def _team_headers() -> dict:
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    return {"apikey": service_key, "Authorization": f"Bearer {service_key}"}


@app.get("/api/team")
def list_team(user: dict = Depends(require_user)) -> dict:
    """The caller's workspace: people they've invited (any status — pending
    shows as "invited, not yet accepted"), the pending invites addressed to
    them, and the accepted owner(s) whose workspace they're actually in."""
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    headers = _team_headers()

    invited = requests.get(
        f"{base}/rest/v1/team_members",
        params={"owner_id": f"eq.{user['id']}", "select": "member_id,email,status,created_at"},
        headers=headers, timeout=10,
    )
    invited.raise_for_status()

    involving_me = requests.get(
        f"{base}/rest/v1/team_members",
        params={"member_id": f"eq.{user['id']}", "select": "owner_id,email,status,created_at"},
        headers=headers, timeout=10,
    )
    involving_me.raise_for_status()
    involving_me_rows = involving_me.json()

    return {
        "members": invited.json(),
        "pending_invitations": [r for r in involving_me_rows if r["status"] == "pending"],
        "workspaces": [r for r in involving_me_rows if r["status"] == "accepted"],
    }


@app.post("/api/team/invite")
def invite_team_member(body: TeamInvite, user: dict = Depends(require_user)) -> dict:
    """Creates a *pending* invite — grants no access until the invitee
    explicitly accepts it via POST /api/team/accept. Anyone could otherwise
    add an arbitrary email and (previously) get standing access to that
    person's data without their consent."""
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    headers = _team_headers()
    frontend_origin = _frontend_origins[0] if _frontend_origins else None

    resp = requests.post(
        f"{base}/auth/v1/invite",
        json={"email": body.email, "data": {}, **(
            {"redirect_to": f"{frontend_origin}/auth/callback"} if frontend_origin else {}
        )},
        headers=headers, timeout=10,
    )

    if resp.status_code in (200, 201):
        member_id = resp.json()["id"]
    else:
        # Already-registered users can't be re-invited by email — look them
        # up so we can still record the (still-pending) invite.
        lookup = requests.get(
            f"{base}/auth/v1/admin/users", params={"email": body.email},
            headers=headers, timeout=10,
        )
        lookup.raise_for_status()
        users = lookup.json().get("users", [])
        if not users:
            raise HTTPException(status_code=400, detail=resp.json().get("msg", "Invite failed"))
        member_id = users[0]["id"]

    upsert = requests.post(
        f"{base}/rest/v1/team_members",
        params={"on_conflict": "owner_id,member_id"},
        json={
            "owner_id": user["id"], "member_id": member_id, "email": body.email,
            "status": "pending",
        },
        headers={**headers, "Prefer": "resolution=merge-duplicates"},
        timeout=10,
    )
    upsert.raise_for_status()
    return {"ok": True}


@app.post("/api/team/accept")
def accept_team_invite(body: TeamAccept, user: dict = Depends(require_user)) -> dict:
    """The invitee accepts — only now does the owner's workspace become
    visible to them. Scoped to member_id = the caller, so you can only
    accept invites actually addressed to you."""
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    resp = requests.patch(
        f"{base}/rest/v1/team_members",
        params={"owner_id": f"eq.{body.owner_id}", "member_id": f"eq.{user['id']}"},
        json={"status": "accepted"},
        headers=_team_headers(), timeout=10,
    )
    resp.raise_for_status()
    return {"ok": True}


@app.post("/api/team/decline")
def decline_team_invite(body: TeamAccept, user: dict = Depends(require_user)) -> dict:
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    resp = requests.delete(
        f"{base}/rest/v1/team_members",
        params={"owner_id": f"eq.{body.owner_id}", "member_id": f"eq.{user['id']}"},
        headers=_team_headers(), timeout=10,
    )
    resp.raise_for_status()
    return {"ok": True}


@app.delete("/api/team/{other_user_id}")
def remove_team_member(other_user_id: str, user: dict = Depends(require_user)) -> dict:
    """Removes the relationship in either direction: an owner removing a
    member, or a member leaving a workspace they'd joined."""
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    resp = requests.delete(
        f"{base}/rest/v1/team_members",
        params={
            "or": (
                f"(and(owner_id.eq.{user['id']},member_id.eq.{other_user_id}),"
                f"and(owner_id.eq.{other_user_id},member_id.eq.{user['id']}))"
            ),
        },
        headers=_team_headers(), timeout=10,
    )
    resp.raise_for_status()
    return {"ok": True}
