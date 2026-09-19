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

Run:  .venv/bin/uvicorn pagebirdy.api:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import logging
import os
import os.path
import re
import threading
from collections import deque

from pagebirdy.config import load_env

load_env()

import requests
from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, UUID4

from pagebirdy import languages, storage
from pagebirdy.auth import (effective_owner_ids, get_or_create_profile, get_profile_names,
                        invalidate_owner_ids_cache, require_trial_active, require_user)
from pagebirdy.pipeline import (rebuild_from_edits, translate_idml,
                            translate_links_folder, translate_pdf)
from pagebirdy.review.store import ReviewStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger("pagebirdy.api")

# ---- in-app log tail --------------------------------------------------
# Lets the frontend show what the server is doing (upload received,
# translation progress, job done/failed) without a separate terminal. This
# panel is client-visible (an MVP "server activity" widget, unauthenticated,
# shown in the app UI) — it must never carry internal engineering detail:
# stack traces, file paths, thread-pool/OCR/engine internals, uvicorn access
# lines, httpx request logs. Those stay on the normal `pagebirdy.*` loggers
# (stdout, per `logging.basicConfig` below) and are never fed to this
# buffer. Only an explicit call to `_activity()` reaches a client, so
# there's exactly one place to check when deciding what's shown.
#
# A bounded ring buffer of formatted lines, fed by a logging.Handler
# attached to a single dedicated logger (NOT the root logger — that's what
# used to leak every internal log line to this same client-facing panel).
# Polled via GET /api/logs — no SSE, simplest thing that works.
_LOG_BUFFER: deque[dict] = deque(maxlen=1000)
_LOG_LOCK = threading.Lock()
_LOG_NEXT_ID = 0
_ACTIVITY_LOGGER_NAME = "pagebirdy.activity"


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
                # Whoever's upload/job this line is about — GET /api/logs
                # filters to only the caller's own owner-id set, so one
                # customer polling the panel never sees another customer's
                # activity ("Uploaded Q3-report.pdf") leak through.
                "owner_id": getattr(record, "owner_id", None),
            })


_activity_handler = _BufferLogHandler()
_activity_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
_activity_logger = logging.getLogger(_ACTIVITY_LOGGER_NAME)
_activity_logger.addHandler(_activity_handler)
_activity_logger.setLevel(logging.INFO)
_activity_logger.propagate = False  # never let this also land in the normal pagebirdy.* stdout logs twice


def _activity(message: str, owner_id: str | None = None) -> None:
    """Log one client-visible line — plain English, no internal detail. This
    is the ONLY thing that reaches the frontend's Logs panel; everything
    else logged via `logger` (module-level, e.g. `logging.getLogger("pagebirdy.api")`)
    stays server-side. `owner_id` scopes the line to that user/team — GET
    /api/logs only ever returns the caller's own lines."""
    _activity_logger.info(message, extra={"owner_id": owner_id})

_REVIEW_DB = os.environ.get("BABEL_REVIEW_DB", "babel_review.db")
_UPLOAD_DIR = os.environ.get("BABEL_UPLOAD_DIR", "uploads")
_OUT_DIR = os.environ.get("BABEL_OUT_DIR", "out")

app = FastAPI(title="pagebirdy review")
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
    return ReviewStore(_REVIEW_DB)


def _upload_dir() -> str:
    return os.environ.get("BABEL_UPLOAD_DIR", _UPLOAD_DIR)


def _out_dir() -> str:
    return os.environ.get("BABEL_OUT_DIR", _OUT_DIR)


def _upload_with_retry(local_path: str, key: str, attempts: int = 3) -> None:
    """Storage calls occasionally hit a transient network/DNS blip (connect
    timeout to Supabase) rather than a real failure — one retry used to mean
    the whole persist step aborted, leaving a job marked "complete" in the DB
    while its files still pointed at local scratch space that Railway wipes
    on redeploy: permanently undownloadable, with no indication anything was
    wrong until someone tried."""
    import time

    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            storage.upload_file(local_path, key)
            return
        except Exception as e:
            last_error = e
            if attempt < attempts - 1:
                time.sleep(1.5 * (attempt + 1))
    raise last_error  # type: ignore[misc]


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


def _materialize_job_files(job: dict) -> tuple[str, str]:
    """Downloads a job's current source/output from Storage into a fresh
    local temp dir. `rebuild_from_edits` predates Storage and wants real
    files on disk; this lets it run unmodified via its source_path/output_path
    overrides. Returns (local_source, local_output) — local_output may not
    exist yet (it's a write target, not necessarily downloaded)."""
    import tempfile

    tmp_dir = tempfile.mkdtemp(prefix=f"job-{job['id']}-")
    source_key = str(job.get("source") or "")
    output_key = str(job.get("output") or "")
    local_source = os.path.join(tmp_dir, "source" + (os.path.splitext(source_key)[1] or ""))
    local_output = os.path.join(tmp_dir, "output" + (os.path.splitext(output_key)[1] or ""))
    if source_key and not storage.download_to(source_key, local_source):
        # A silently-discarded False here used to surface as a bare
        # `FileNotFoundError` from whatever tried to open `local_source` next
        # (IdmlPackage, fitz.open, ...) — no indication it was a Storage
        # fetch failure (missing object, or a transient network/DNS/timeout
        # reaching Supabase) rather than a real bug in the caller.
        raise RuntimeError(f"failed to download source {source_key!r} from storage")
    if output_key:
        storage.download_to(output_key, local_output)
    return local_source, local_output


def _output_pdf_path(output: str) -> str:
    """The browser-renderable PDF for a job output.

    PDF jobs: the output itself. IDML jobs: the deterministic .pdf sibling
    of the .es.idml (produced only when INDESIGN_SERVER exported one)."""
    if output.lower().endswith(".pdf"):
        return output
    return os.path.splitext(output)[0] + ".pdf"


_OUTPUT_HASH_RE = re.compile(r"^(.*)-[0-9a-f]{8}(\.[^.]+)$")


def _strip_output_hash(name: str) -> str:
    """Undo `idml/graphics.py`'s `_output_filename` disambiguation
    (`{base}-{8 hex digits}{ext}`), back to the original file's own stem —
    used to match a translated graphic back to the original it replaces."""
    m = _OUTPUT_HASH_RE.match(name)
    return m.group(1) if m else os.path.splitext(name)[0]


def _links_zip_entries(job_id: str, lang_code: str | None,
                       pair_by_stem: bool = True) -> dict[str, bytes] | None:
    """Every linked-graphic file this job has in Storage, keyed by its
    "Links/<name>" path inside a zip — translated version where translation
    happened, the original file everywhere else. Returns None if the job has
    no persisted Links at all.

    Storage keys are job-scoped (`jobs/{job_id}/Links/…`,
    `jobs/{job_id}/Links_{lang}/…`) — unlike the shared-per-language local
    disk folder `translate_idml` writes during processing, there is no
    cross-job leak risk here to guard against.

    `pair_by_stem=True` (an `.idml`'s own attached Links) matches a
    translated file back to the SAME original it replaces, so the zip never
    contains both. `pair_by_stem=False` (a standalone `/api/translate-links`
    batch) must NOT do that pairing: there, `Links/` and `Links_{lang}/`
    hold entirely different, unrelated source files that only sometimes
    happen to share a stem (e.g. a companion `.ai` + `.psd` pair) —
    "pairing" them silently dropped one of the two from the zip.
    """
    original_names = storage.list_prefix(f"jobs/{job_id}/Links/")
    translated_names = (
        storage.list_prefix(f"jobs/{job_id}/Links_{lang_code}/") if lang_code else []
    )
    if not original_names and not translated_names:
        return None

    entries: dict[str, bytes] = {}

    if not pair_by_stem:
        used_names: set[str] = set()
        for oname in original_names:
            name = _dedupe_flat_name(oname, used_names)
            data = storage.read_bytes(f"jobs/{job_id}/Links/{oname}")
            if data is not None:
                entries[f"Links/{name}"] = data
        for tname in translated_names:
            name = _dedupe_flat_name(tname, used_names)
            data = storage.read_bytes(f"jobs/{job_id}/Links_{lang_code}/{tname}")
            if data is not None:
                entries[f"Links/{name}"] = data
        return entries or None

    translated_by_stem = {_strip_output_hash(n): n for n in translated_names}
    covered_stems: set[str] = set()
    for oname in original_names:
        stem = os.path.splitext(oname)[0]
        covered_stems.add(stem)
        tname = translated_by_stem.get(stem)
        if tname:
            data = storage.read_bytes(f"jobs/{job_id}/Links_{lang_code}/{tname}")
            if data is not None:
                entries[f"Links/{stem}{os.path.splitext(tname)[1]}"] = data
                continue
        data = storage.read_bytes(f"jobs/{job_id}/Links/{oname}")
        if data is not None:
            entries[f"Links/{oname}"] = data
    # A translated graphic whose original wasn't (re-)attached this time
    # still belongs in the bundle under its real name.
    for stem, tname in translated_by_stem.items():
        if stem in covered_stems:
            continue
        data = storage.read_bytes(f"jobs/{job_id}/Links_{lang_code}/{tname}")
        if data is not None:
            entries[f"Links/{tname}"] = data
    return entries or None


def _dedupe_flat_name(name: str, used: set[str]) -> str:
    """Same collision-safe rename as `translate_links_folder`'s own
    disambiguation — needed again here because two files that are
    independently unique within their own storage prefix (`Links/` vs
    `Links_{lang}/`) can still collide once flattened into one list/zip."""
    if name not in used:
        used.add(name)
        return name
    base, ext = os.path.splitext(name)
    n = 2
    candidate = f"{base}_{n}{ext}"
    while candidate in used:
        n += 1
        candidate = f"{base}_{n}{ext}"
    used.add(candidate)
    return candidate


_LINK_MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".ai": "application/pdf",  # Adobe Illustrator files are PDF-compatible
    ".eps": "application/postscript",
    ".psd": "image/vnd.adobe.photoshop",
}


def _link_file_map(job_id: str, lang_code: str | None) -> dict[str, tuple[str, bool]]:
    """Display name -> (storage key, is_translated) for every linked-graphic
    file in a standalone links batch. Every file is independently either
    translated (`Links_{lang}/`) or untranslated-original (`Links/`), never
    both — unlike an .idml's own attached Links, there is no "same source,
    two states" pairing to do here, so this is a plain union. Pairing by
    stem (as `_links_zip_entries` does for that other case) would wrongly
    merge two different, unrelated files that happen to share a base name
    (e.g. a companion `.ai` + `.psd` asset pair), silently dropping one."""
    original_names = storage.list_prefix(f"jobs/{job_id}/Links/")
    translated_names = (
        storage.list_prefix(f"jobs/{job_id}/Links_{lang_code}/") if lang_code else []
    )
    entries: dict[str, tuple[str, bool]] = {}
    used_names: set[str] = set()
    for oname in original_names:
        name = _dedupe_flat_name(oname, used_names)
        entries[name] = (f"jobs/{job_id}/Links/{oname}", False)
    for tname in translated_names:
        name = _dedupe_flat_name(tname, used_names)
        entries[name] = (f"jobs/{job_id}/Links_{lang_code}/{tname}", True)
    return entries


@app.get("/api/jobs/{job_id}/links/list")
def list_link_files(job_id: str, user: dict = Depends(require_user)) -> list[dict]:
    """Every linked-graphic file for this job, for a Finder-style preview —
    name, translated status, and whether the browser can render it inline."""
    job = _find_owned_job(job_id, user)
    meta = job.get("meta") or {}
    file_map = _link_file_map(job_id, meta.get("target_lang"))
    return sorted(
        (
            {
                "name": name,
                "translated": translated,
                "previewable": os.path.splitext(name)[1].lower() in (".pdf", ".ai"),
            }
            for name, (_, translated) in file_map.items()
        ),
        key=lambda e: e["name"].lower(),
    )


@app.get("/api/jobs/{job_id}/links/file/{name}")
def get_link_file(job_id: str, name: str, user: dict = Depends(require_user)) -> Response:
    """Serve a single linked-graphic file's bytes (translated version if one
    exists, the original otherwise) so the frontend can preview or download
    it individually instead of pulling the whole zip bundle."""
    job = _find_owned_job(job_id, user)
    meta = job.get("meta") or {}
    file_map = _link_file_map(job_id, meta.get("target_lang"))
    entry = file_map.get(name)
    if entry is None:
        raise HTTPException(status_code=404, detail="file not found")
    key, _translated = entry
    data = storage.read_bytes(key)
    if data is None:
        raise HTTPException(status_code=404, detail="file not found")
    media = _LINK_MEDIA_TYPES.get(os.path.splitext(name)[1].lower(), "application/octet-stream")
    return Response(content=data, media_type=media)


def _idml_zip_response(idml_key: str, job_id: str, lang_code: str | None) -> Response | None:
    """Bundles an .idml with every one of its linked graphics — translated
    where translation happened, the original file everywhere else — so
    nothing is missing when InDesign asks to relink. Returns None if the job
    has no persisted Links (nothing to bundle; caller serves the plain .idml).
    """
    import io
    import zipfile

    idml_bytes = storage.read_bytes(idml_key)
    if idml_bytes is None:
        return None

    entries = _links_zip_entries(job_id, lang_code)
    if entries is None:
        return None

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(os.path.basename(idml_key), idml_bytes)
        for path, data in entries.items():
            z.writestr(path, data)
    buf.seek(0)

    zip_name = os.path.splitext(os.path.basename(idml_key))[0] + ".zip"
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )


def _links_zip_response(job_id: str, lang_code: str | None, base_name: str,
                        pair_by_stem: bool = True) -> Response | None:
    """Just the Links folder, no .idml — the standalone "download Links"
    button next to a job's own .idml download, OR the whole deliverable for
    a standalone `/api/translate-links` batch job (`pair_by_stem=False` for
    that case — see `_links_zip_entries`). Returns None if the job has no
    persisted Links."""
    import io
    import zipfile

    entries = _links_zip_entries(job_id, lang_code, pair_by_stem=pair_by_stem)
    if entries is None:
        return None

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path, data in entries.items():
            z.writestr(path, data)
    buf.seek(0)

    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{base_name}-links.zip"'},
    )


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
def get_logs(since: int = 0, user: dict = Depends(require_user)) -> dict:
    """Log lines newer than `since` (the `id` of the last line the caller
    already has), scoped to the caller's own activity — never another
    customer's. Poll this with the last-seen id to tail the server."""
    owner_ids = effective_owner_ids(user["id"])
    with _LOG_LOCK:
        lines = [
            {k: v for k, v in entry.items() if k != "owner_id"}
            for entry in _LOG_BUFFER
            if entry["id"] > since and entry.get("owner_id") in owner_ids
        ]
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
        job_ids = [j["id"] for j in s.list_jobs() if j.get("project_id") == project_id]
        s.delete_project(project_id)
    finally:
        s.close()
    for jid in job_ids:
        storage.delete_prefix(f"jobs/{jid}/")
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
                  all: bool = False, user: dict = Depends(require_user)) -> list[dict]:
    s = _store()
    try:
        _assert_owns_project(s, project_id, user)
        return s.list_folders(project_id, parent_folder_id, all=all)
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
        job_ids = s.delete_folder(folder_id)
    finally:
        s.close()
    for jid in job_ids:
        storage.delete_prefix(f"jobs/{jid}/")
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
    scoped = ([j for j in jobs if j.get("project_id") == project_id] if all else
              [j for j in jobs
               if j.get("project_id") == project_id and j.get("folder_id") == folder_id])
    # Resolve each job's raw created_by id to a display name in one batch
    # call rather than the Files table showing the id or an empty dash.
    names = get_profile_names([j.get("created_by") for j in scoped])
    for j in scoped:
        j["created_by_name"] = names.get(j.get("created_by"))
    return scoped


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
    storage.delete_prefix(f"jobs/{job_id}/")
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
    """Redraw a PDF job's output file from the review store's current
    target/status per segment — call after editing/approving a segment so
    the preview/download reflect it.

    IDML jobs never reach here: there is no in-browser editor for `.idml`
    (see the frontend file viewer, which skips straight to a download link
    for it), so nothing ever calls this for one — the review/approve/rebuild
    loop only exists for the PDF path."""
    job = _find_owned_job(job_id, user)
    require_trial_active(user)

    if str(job.get("output", "")).lower().endswith(".idml"):
        raise HTTPException(status_code=400, detail="rebuild is not supported for IDML jobs")

    output_key = str(job["output"])

    def _run() -> str:
        local_source, local_output = _materialize_job_files(job)
        rebuild_from_edits(
            job_id, review_db=_REVIEW_DB, source_path=local_source, output_path=local_output
        )
        storage.upload_file(local_output, output_key)
        return output_key

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

        python -m pagebirdy.eval job <id> --neural --mqm

    Cached to out/eval/<job_id>.eval.json because the layout metrics re-render
    every page. `refresh` recomputes — needed after approving edits, since
    integrity rates move as segments change.
    """
    import json
    import shutil

    job = _find_owned_job(job_id, user)

    cache = _eval_cache_path(job_id)
    if not refresh and os.path.exists(cache):
        try:
            with open(cache, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass  # unreadable cache is not an error, just recompute

    from pagebirdy.eval import runner

    # `job["source"]`/`job["output"]` are Storage KEYS, not local paths — the
    # layout metrics (everything but a links batch's own early return) need
    # real files to open. Without this, every one of them silently read as
    # "not measured" once local scratch space was gone, which on a job whose
    # files were never in this process's own temp dir (i.e. any job, once
    # requested from a fresh page load) was effectively always. A links job
    # has no single file to fetch, so skip straight past it.
    tmp_dir: str | None = None

    def _run() -> dict:
        nonlocal tmp_dir
        if job.get("job_type") == "links":
            return runner.evaluate_job(job_id, review_db=_REVIEW_DB)
        local_source, local_output = _materialize_job_files(job)
        tmp_dir = os.path.dirname(local_source)
        return runner.evaluate_job(job_id, review_db=_REVIEW_DB,
                                   source_path=local_source, output_path=local_output)

    try:
        report = await run_in_threadpool(_run)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.info("eval failed for job %s: %s", job_id, e)
        raise HTTPException(status_code=500, detail=f"evaluation failed: {e}")
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    os.makedirs(os.path.dirname(cache), exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report


@app.get("/api/jobs/{job_id}/eval")
async def get_eval(job_id: str, refresh: bool = False, cache_only: bool = False,
                    user: dict = Depends(require_user)) -> dict:
    """Accuracy scorecard for one job: gates, layout fidelity, content integrity.

    `cache_only=true` never runs a fresh evaluation (layout scoring re-renders
    every page — real CPU work) — it just reads whatever `_eval_cache_path`
    already holds, or reports `{"not_computed": true}`. That's what the Files
    list's QA column uses: showing a real score once someone has run "QA
    check" on the project, but never silently kicking off N evaluations just
    because the list happened to render."""
    if cache_only:
        import json

        _find_owned_job(job_id, user)
        cache = _eval_cache_path(job_id)
        if not os.path.exists(cache):
            return JSONResponse({"not_computed": True},
                                headers={"Cache-Control": "no-store, no-cache, must-revalidate"})
        try:
            with open(cache, encoding="utf-8") as f:
                return JSONResponse(json.load(f),
                                    headers={"Cache-Control": "no-store, no-cache, must-revalidate"})
        except (OSError, json.JSONDecodeError):
            return JSONResponse({"not_computed": True},
                                headers={"Cache-Control": "no-store, no-cache, must-revalidate"})

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
        from pagebirdy.eval import scorecard

        body = scorecard.render_markdown(report).encode("utf-8")
        media = "text/markdown; charset=utf-8"
    else:
        from pagebirdy.eval import report_pdf

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
    # Each upload gets its own dir so concurrent uploads with same-named
    # files never clobber each other.
    import uuid

    job_dir = os.path.join(upload_dir, uuid.uuid4().hex[:12])
    os.makedirs(job_dir, exist_ok=True)

    saved = os.path.join(job_dir, os.path.basename(name))
    data = await file.read()
    with open(saved, "wb") as f:
        f.write(data)

    file_hash = hashlib.sha256(data).hexdigest()
    file_size = len(data)
    started = time.time()

    logger.info("upload received: %s (%d bytes) ext=%s target_lang=%s",
                name, file_size, ext, lang.code)
    _activity(f"Uploaded {name} — translating to {lang.name}", owner_id=user["id"])

    # Persisted *before* translation starts — status="processing" — so the
    # Files list shows a real in-progress row from any tab, surviving a
    # navigation or a closed tab, instead of a client-side-only indicator
    # that vanishes the moment the uploading tab is gone.
    store = _store()
    try:
        job_id = store.create_pending_job(
            saved, original_filename=name, file_hash=file_hash, file_size=file_size,
            meta={"target_lang": lang.code}, project_id=project_id or None,
            folder_id=folder_id or None, created_by=user["id"],
        )
    finally:
        store.close()

    def _progress_cb(percent: int, stage: str) -> None:
        # Runs inside the threadpool worker doing the translation — a plain
        # blocking DB call is fine here, same thread, not the event loop.
        # Best-effort: a failed progress tick must never break translation.
        try:
            s = _store()
            try:
                s.update_job_progress(job_id, percent, stage)
            finally:
                s.close()
        except Exception:
            logger.exception("upload: failed to report progress for job %s (non-fatal)", job_id)

    # Translation is blocking (network LLM calls). Run it off the event loop
    # so a single upload doesn't freeze the whole server for other requests.
    def _run() -> dict:
        from pagebirdy.idml.export import convert_to_idml, export

        if ext == ".pdf":
            logger.info("upload: .pdf path, running translate_pdf directly for %s", name)
            report = translate_pdf(saved, out_dir=_out_dir(),
                                   review_db=_REVIEW_DB, target_lang=lang.code,
                                   project_id=project_id or None, folder_id=folder_id or None, created_by=user["id"],
                                   original_filename=name, job_id=job_id, progress_cb=_progress_cb)
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
            report = translate_idml(saved, out_dir=_out_dir(),
                                    review_db=_REVIEW_DB, target_lang=lang.code,
                                    project_id=project_id or None, folder_id=folder_id or None, created_by=user["id"],
                                    original_filename=name, job_id=job_id, progress_cb=_progress_cb)
            report["format"] = "idml"
            # A best-effort draft PDF (no InDesign) is rendered alongside the
            # .idml so the UI can offer a "Translated PDF" download/preview.
            report["has_output_pdf"] = bool(report.get("has_draft_pdf"))
            report["draft_pdf"] = bool(report.get("has_draft_pdf"))
            logger.info("upload: pipeline complete for %s (job_id=%s)",
                        name, report.get("job_id"))
            return report

        conv = convert_to_idml(saved, _out_dir())
        if not conv.ok:
            raise RuntimeError(conv.message)

        report = translate_idml(conv.idml, out_dir=_out_dir(),
                                review_db=_REVIEW_DB, target_lang=lang.code,
                                project_id=project_id or None, folder_id=folder_id or None, created_by=user["id"],
                                original_filename=name, job_id=job_id, progress_cb=_progress_cb)
        report["source"] = saved  # show the original .indd name, not the intermediate .idml

        exp = export(report["output"], _out_dir())
        if not exp.ok:
            # translate_idml already persisted a job row pointing at the
            # intermediate .idml. Since export failed, that job has no usable
            # deliverable (no PDF fallback in this INDD-only flow) — delete it
            # so it doesn't stay browsable/downloadable as a phantom success.
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
        _activity(f"Translation failed for {name}", owner_id=user["id"])
        store = _store()
        try:
            store.mark_job_failed(job_id, str(e), duration_sec=time.time() - started)
        finally:
            store.close()
        raise HTTPException(status_code=500, detail=f"translation failed: {e}")

    _activity(f"Finished translating {name}", owner_id=user["id"])

    # The pipeline wrote source/output to local scratch space (Railway's disk
    # resets on every redeploy) and pointed the job row at those local paths.
    # Upload both to durable Storage, then repoint the row at the storage
    # keys — same repoint mechanism already used above for the INDD export
    # swap, applied uniformly to every format now.
    job_id = report.get("job_id")
    if job_id and report.get("source") and report.get("output"):
        stem = os.path.splitext(os.path.basename(name))[0]
        source_ext = os.path.splitext(report["source"])[1] or ext
        output_ext = os.path.splitext(report["output"])[1] or ext
        source_key = f"jobs/{job_id}/{stem}{source_ext}"
        output_key = f"jobs/{job_id}/{stem}.{lang.code}{output_ext}"

        try:
            await run_in_threadpool(_upload_with_retry, report["source"], source_key)
            await run_in_threadpool(_upload_with_retry, report["output"], output_key)
        except Exception as e:
            # The two lines above are the ONLY thing that makes this job
            # durably downloadable — if they can't be persisted after
            # retrying, the job is not actually usable long-term even though
            # translation itself succeeded. Mark it failed rather than
            # leaving a "complete" row that 404s on every future download.
            logger.exception("upload: failed to persist job %s to storage, marking failed", job_id)
            store = _store()
            try:
                store.mark_job_failed(
                    job_id, f"translated successfully but failed to persist to storage: {e}",
                    duration_sec=time.time() - started,
                )
            finally:
                store.close()
            raise HTTPException(
                status_code=500,
                detail=f"translation succeeded but saving the result failed: {e}",
            )

        # Keep the local output path (needed for the draft-PDF sibling below)
        # before overwriting report["output"] with its storage key.
        local_output_path = report["output"]
        report["source"] = source_key
        report["output"] = output_key

        # Best-effort extras below: a missing draft-PDF preview or linked
        # graphic must not fail a job whose actual source/output are already
        # safely persisted above — log and move on.
        try:
            # The draft-PDF preview (idml jobs only, see pipeline.translate_idml)
            # lives as a local .pdf sibling of the .idml output — upload it under
            # the matching storage key so download_output's fmt="pdf" branch
            # (_output_pdf_path) can find it later.
            if report.get("draft_pdf"):
                local_draft_pdf = os.path.splitext(local_output_path)[0] + ".pdf"
                if os.path.exists(local_draft_pdf):
                    draft_pdf_key = os.path.splitext(output_key)[0] + ".pdf"
                    await run_in_threadpool(storage.upload_file, local_draft_pdf, draft_pdf_key)
        except Exception:
            logger.exception("upload: failed to persist draft pdf for job %s (non-fatal)", job_id)

        # Linked graphics are now their own independent upload/job (see
        # /api/translate-links) rather than an attachment to this one — no
        # per-document Links folder to persist here anymore. A document's own
        # translate_idml still best-effort-translates a linked graphic when
        # its *original absolute path* happens to resolve locally (rare in a
        # hosted deployment), but that no longer has a matching upload/persist
        # step; it stays an in-place edit of the .idml itself when it fires.

        store = _store()
        try:
            store.update_job_paths(job_id, source=source_key, output=output_key)
        finally:
            store.close()

    if project_id:
        store = _store()
        try:
            store.set_project_target_lang_if_unset(project_id, lang.code)
        finally:
            store.close()

    return report


@app.post("/api/translate-links")
async def translate_links_upload(
    files: list[UploadFile] = File(...),
    target_lang: str = Form(default=""),
    project_id: str = Form(default=""),
    folder_id: str = Form(default=""),
    user: dict = Depends(require_user),
) -> dict:
    """Translate a batch of linked-graphic files (.ai/.eps/.pdf/.psd) as its
    own independent job — no `.idml` involved, no relinking. See
    `pipeline.translate_links_folder` for the trade-off this makes versus
    the old design (Links attached to a specific `.idml` upload)."""
    import time

    require_trial_active(user)

    if project_id:
        s = _store()
        try:
            _assert_owns_project(s, project_id, user)
        finally:
            s.close()

    if not files:
        raise HTTPException(status_code=400, detail="attach at least one linked-graphic file")
    try:
        lang = languages.get(target_lang or None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    upload_dir = _upload_dir()
    import uuid

    job_dir = os.path.join(upload_dir, uuid.uuid4().hex[:12])
    links_dir = os.path.join(job_dir, "Links")
    os.makedirs(links_dir, exist_ok=True)

    saved_paths: list[str] = []
    total_size = 0
    seen_rel_paths: set[str] = set()
    for f in files:
        # Preserve the upload's relative path (a folder pick sends
        # "Unit01/CA001.ai" style names) rather than collapsing to the leaf
        # filename — two different subfolders reusing the same leaf name is
        # routine for a lesson-per-folder asset library, and saving both to
        # the same flat path silently overwrote one with the other before
        # translation ever ran (permanent data loss, not just a display gap).
        rel = (f.filename or "").replace("\\", "/").lstrip("/")
        parts = [p for p in rel.split("/") if p not in ("", ".", "..")]
        if not parts:
            continue
        rel = "/".join(parts)
        if rel in seen_rel_paths:
            # the exact same relative path was selected twice in one
            # upload — keep the first copy, skip re-reading a duplicate part
            logger.info("upload(links): skipped duplicate relative path %r in one upload", rel)
            continue
        seen_rel_paths.add(rel)
        path = os.path.join(links_dir, *parts)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = await f.read()
        with open(path, "wb") as out:
            out.write(data)
        saved_paths.append(path)
        total_size += len(data)

    if not saved_paths:
        raise HTTPException(status_code=400, detail="no valid files attached")

    # A production-traceable count at every stage of this pipeline (received
    # -> saved -> translated -> uploaded) is what actually lets a "why is my
    # file missing" report be answered from logs alone, without reproducing
    # the upload — this is the shape the 357-vs-199 filename-collision bug
    # (and its 137-file predecessor, dropped-with-no-text files) should have
    # been caught by well before a client noticed the count mismatch.
    if len(saved_paths) != len(files):
        logger.warning(
            "upload(links): received %d file part(s) but saved %d (empty/invalid names "
            "or duplicate relative paths were skipped — see prior log lines)",
            len(files), len(saved_paths))

    started = time.time()
    # A batch of one has no batch to speak of, and "1 linked graphic" tells
    # the user nothing they didn't already know — show the real filename
    # instead, same as any other job type's Document column does.
    display_name = (os.path.basename(saved_paths[0]) if len(saved_paths) == 1
                     else f"{len(saved_paths)} linked graphics")
    logger.info("upload received (links): %d file(s), %.1f MB, target_lang=%s",
                len(saved_paths), total_size / (1 << 20), lang.code)
    _activity(f"Uploaded {display_name} — translating to {lang.name}", owner_id=user["id"])

    # Distinct extensions across the batch (".ai", ".psd", ...), so the
    # frontend's Type column has something to show for a "links" job — its
    # own `original_filename` is a display label ("3 linked graphics"),
    # not a real filename with an extension to read.
    extensions = sorted({os.path.splitext(p)[1].lower().lstrip(".") for p in saved_paths if os.path.splitext(p)[1]})

    store = _store()
    try:
        job_id = store.create_pending_job(
            "links", original_filename=display_name, file_size=total_size,
            meta={"target_lang": lang.code, "job_type": "links", "total_files": len(saved_paths),
                  "extensions": extensions},
            project_id=project_id or None, folder_id=folder_id or None, created_by=user["id"],
            job_type="links",
        )
    finally:
        store.close()

    def _progress_cb(percent: int, stage: str) -> None:
        try:
            s = _store()
            try:
                s.update_job_progress(job_id, percent, stage)
            finally:
                s.close()
        except Exception:
            logger.exception("upload(links): failed to report progress for job %s (non-fatal)", job_id)

    def _run() -> dict:
        return translate_links_folder(
            saved_paths, out_dir=_out_dir(), review_db=_REVIEW_DB, target_lang=lang.code,
            project_id=project_id or None, folder_id=folder_id or None, created_by=user["id"],
            original_filename=display_name, job_id=job_id, progress_cb=_progress_cb,
        )

    try:
        report = await run_in_threadpool(_run)
    except Exception as e:
        logger.info("upload(links): pipeline failed: %s", e)
        _activity(f"Translation failed for {display_name}", owner_id=user["id"])
        store = _store()
        try:
            store.mark_job_failed(job_id, str(e), duration_sec=time.time() - started)
        finally:
            store.close()
        raise HTTPException(status_code=500, detail=f"translation failed: {e}")

    _activity(f"Translated {len(report.get('translated_files') or [])} of "
             f"{report.get('total_files', len(saved_paths))} file(s) in {display_name}",
             owner_id=user["id"])

    # Every translated output is persisted to storage. A file with no
    # extractable text (pure artwork — the common case) never produces a
    # translated output, so its untouched original is persisted instead
    # (see `translate_links_folder`'s `untranslated_files`) rather than
    # silently dropping it — a links batch is otherwise missing whatever
    # fraction of its files had nothing to translate, both from any per-file
    # listing and from the download zip's "original file everywhere else"
    # fallback (`_links_zip_entries`).
    translated_dir = os.path.join(_out_dir(), f"translated_{lang.code}")

    async def _upload_one(gname: str) -> bool:
        gpath = os.path.join(translated_dir, gname)
        if not os.path.isfile(gpath):
            logger.error(
                "upload(links): translated file %r missing on local disk for job %s "
                "(should be unreachable — translate_links_folder reported it as written)",
                gname, job_id)
            return False
        try:
            await run_in_threadpool(
                _upload_with_retry, gpath, f"jobs/{job_id}/Links_{lang.code}/{gname}")
        except Exception:
            logger.exception(
                "upload(links): failed to persist translated %r for job %s (non-fatal)", gname, job_id)
            return False
        return True

    async def _upload_original(item: dict) -> bool:
        # `path` is the file's real source path (possibly inside a
        # subfolder — `saved_paths`/`links_dir` preserve the upload's
        # relative structure), `name` is the disambiguated flat display name
        # `translate_links_folder` assigned it. Both still live on local disk
        # for the duration of this request.
        opath = item["path"]
        oname = item["name"]
        if not os.path.isfile(opath):
            logger.error(
                "upload(links): original file %r missing on local disk for job %s "
                "(should be unreachable)", oname, job_id)
            return False
        try:
            await run_in_threadpool(
                _upload_with_retry, opath, f"jobs/{job_id}/Links/{oname}")
        except Exception:
            logger.exception(
                "upload(links): failed to persist original %r for job %s (non-fatal)", oname, job_id)
            return False
        return True

    # These are independent uploads to Supabase Storage — doing them one at a
    # time in a loop was pure serialized network latency, the actual cause of
    # a 300+ file batch taking minutes just to finish persisting after
    # translation itself was already done. A semaphore caps how many run at
    # once so this doesn't hammer Storage with hundreds of concurrent PUTs.
    _UPLOAD_CONCURRENCY = 8
    upload_semaphore = asyncio.Semaphore(_UPLOAD_CONCURRENCY)

    async def _upload_one_bounded(gname: str) -> bool:
        async with upload_semaphore:
            return await _upload_one(gname)

    async def _upload_original_bounded(item: dict) -> bool:
        async with upload_semaphore:
            return await _upload_original(item)

    translated_names = report.get("translated_files") or []
    untranslated_items = report.get("untranslated_files") or []
    upload_results = await asyncio.gather(
        *(_upload_one_bounded(g) for g in translated_names),
        *(_upload_original_bounded(o) for o in untranslated_items),
    )
    persisted_count = sum(1 for ok in upload_results if ok)
    total_count = len(translated_names) + len(untranslated_items)
    # The end-to-end count for this job — received -> saved -> translated ->
    # persisted — so a client-reported "my file is missing" can be answered
    # by grepping this job id's logs instead of reproducing the upload.
    logger.info("upload(links): job %s persisted %d/%d file(s) to storage",
                job_id, persisted_count, total_count)
    if persisted_count != total_count:
        logger.error(
            "upload(links): job %s only persisted %d/%d file(s) — some translated "
            "work was lost to a storage upload failure, see prior exceptions",
            job_id, persisted_count, total_count)
        _activity(f"{display_name}: {persisted_count} of {total_count} file(s) ready — "
                 f"some files failed to save, contact support if any are missing",
                 owner_id=user["id"])
    else:
        _activity(f"{display_name} ready to download", owner_id=user["id"])

    if project_id:
        store = _store()
        try:
            store.set_project_target_lang_if_unset(project_id, lang.code)
        finally:
            store.close()

    return report


@app.get("/api/jobs/{job_id}/source")
def get_source(job_id: str, user: dict = Depends(require_user)) -> Response:
    job = _find_owned_job(job_id, user)
    key = str(job["source"])
    if not key.lower().endswith(".pdf"):
        raise HTTPException(status_code=404, detail="no renderable source")
    data = storage.read_bytes(key)
    if data is None:
        raise HTTPException(status_code=404, detail="no renderable source")
    return Response(content=data, media_type="application/pdf")


@app.get("/api/jobs/{job_id}/output")
def get_output(job_id: str, user: dict = Depends(require_user)) -> Response:
    job = _find_owned_job(job_id, user)
    key = _output_pdf_path(str(job["output"]))
    data = storage.read_bytes(key)
    if data is None:
        raise HTTPException(status_code=404, detail="no renderable output pdf")
    return Response(content=data, media_type="application/pdf")


@app.get("/api/jobs/{job_id}/download")
def download_output(job_id: str, format: str | None = None, type: str | None = None,
                     user: dict = Depends(require_user)) -> Response:
    job = _find_owned_job(job_id, user)

    if job.get("job_type") == "links":
        # An independent linked-graphics batch has no single .idml/source to
        # speak of — its whole "output" is the Links bundle. A batch of ONE
        # file has no batch to speak of either: zipping it just makes the
        # user unzip a single file to get the thing they actually asked
        # for, so serve it directly instead (same bytes `links/file/{name}`
        # would give, just under the job's own /download route).
        meta = job.get("meta") or {}
        file_map = _link_file_map(job_id, meta.get("target_lang"))
        if not file_map:
            raise HTTPException(status_code=404, detail="no translated files for this job")
        if len(file_map) == 1:
            name, (key, _translated) = next(iter(file_map.items()))
            data = storage.read_bytes(key)
            if data is None:
                raise HTTPException(status_code=404, detail="no translated files for this job")
            media = _LINK_MEDIA_TYPES.get(os.path.splitext(name)[1].lower(), "application/octet-stream")
            return Response(
                content=data, media_type=media,
                headers={"Content-Disposition": f'attachment; filename="{name}"'},
            )
        stem = os.path.splitext(os.path.basename(str(job.get("original_filename") or job_id)))[0]
        zipped = _links_zip_response(job_id, meta.get("target_lang"), stem, pair_by_stem=False)
        if zipped is None:
            raise HTTPException(status_code=404, detail="no translated files for this job")
        return zipped

    out = str(job["output"])
    fmt = (format or "").lower().strip()
    target_type = (type or "").lower().strip()
    source = str(job.get("source", ""))

    def _serve(key: str, media: str) -> Response:
        data = storage.read_bytes(key)
        if data is None:
            raise HTTPException(status_code=404, detail="file not found")
        return Response(
            content=data, media_type=media,
            headers={"Content-Disposition": f'attachment; filename="{os.path.basename(key)}"'},
        )

    # If source file requested
    if target_type == "source" or fmt == "source":
        if fmt == "idml":
            if source.lower().endswith(".idml"):
                return _serve(source, "application/octet-stream")
            src_idml = os.path.splitext(source)[0] + ".idml"
            if storage.read_bytes(src_idml) is not None:
                return _serve(src_idml, "application/octet-stream")
        if source:
            media = "application/pdf" if source.lower().endswith(".pdf") else "application/octet-stream"
            data = storage.read_bytes(source)
            if data is not None:
                return _serve(source, media)
        raise HTTPException(status_code=404, detail="Source file not found")

    if fmt == "pdf":
        # No review/edit loop exists for IDML jobs (see rebuild_job's
        # docstring) — the draft PDF preview alongside a translated .idml is
        # served exactly as MT produced it, never regenerated on download.
        pdf_key = _output_pdf_path(out)
        if storage.read_bytes(pdf_key) is not None:
            return _serve(pdf_key, "application/pdf")
        if source.lower().endswith(".pdf"):
            data = storage.read_bytes(source)
            if data is not None:
                return _serve(source, "application/pdf")
        raise HTTPException(status_code=404, detail="PDF format not found for this job")

    if fmt == "idml":
        # No review/edit loop exists for IDML jobs (see rebuild_job's
        # docstring) — the .idml is served exactly as MT produced it.
        meta = job.get("meta") or {}
        lang_code = meta.get("target_lang")
        if out.lower().endswith(".idml"):
            zipped = _idml_zip_response(out, job_id, lang_code)
            if zipped is not None:
                return zipped
            if storage.read_bytes(out) is not None:
                return _serve(out, "application/octet-stream")
        idml_key = os.path.splitext(out)[0] + ".idml"
        if storage.read_bytes(idml_key) is not None:
            zipped = _idml_zip_response(idml_key, job_id, lang_code)
            if zipped is not None:
                return zipped
            return _serve(idml_key, "application/octet-stream")
        if source.lower().endswith(".idml") and storage.read_bytes(source) is not None:
            return _serve(source, "application/octet-stream")
        raise HTTPException(status_code=404, detail="IDML format not available for this job")

    data = storage.read_bytes(out)
    if data is None:
        raise HTTPException(status_code=404, detail="output not found")
    return _serve(out, "application/octet-stream")


@app.get("/api/jobs/{job_id}/links")
def download_links(job_id: str, user: dict = Depends(require_user)) -> Response:
    """Just the Links folder for this job, as a .zip — independent of the
    .idml download, for a document whose linked graphics you want without
    the translated file itself."""
    job = _find_owned_job(job_id, user)
    meta = job.get("meta") or {}
    lang_code = meta.get("target_lang")
    stem = os.path.splitext(os.path.basename(str(job.get("original_filename") or job_id)))[0]
    zipped = _links_zip_response(job_id, lang_code, stem)
    if zipped is None:
        raise HTTPException(status_code=404, detail="no linked graphics for this job")
    return zipped



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
        "first_name": profile.get("first_name"),
        "last_name": profile.get("last_name"),
        "full_name": profile.get("full_name"),
    }



class TeamAccept(BaseModel):
    owner_id: UUID4


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
    invalidate_owner_ids_cache(user["id"])
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
    invalidate_owner_ids_cache(user["id"])
    return {"ok": True}


@app.delete("/api/team/{other_user_id}")
def remove_team_member(other_user_id: UUID4, user: dict = Depends(require_user)) -> dict:
    """Removes the relationship in either direction: an owner removing a
    member, or a member leaving a workspace they'd joined.

    Two plain eq. filters rather than one or=(and(...),and(...)) filter —
    FastAPI's UUID4 path type already rejects anything that isn't a
    well-formed UUID, but avoiding hand-built PostgREST filter syntax
    entirely means there's no filter-injection surface to reason about."""
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    headers = _team_headers()
    requests.delete(
        f"{base}/rest/v1/team_members",
        params={"owner_id": f"eq.{user['id']}", "member_id": f"eq.{other_user_id}"},
        headers=headers, timeout=10,
    ).raise_for_status()
    resp = requests.delete(
        f"{base}/rest/v1/team_members",
        params={"owner_id": f"eq.{other_user_id}", "member_id": f"eq.{user['id']}"},
        headers=headers, timeout=10,
    )
    resp.raise_for_status()
    invalidate_owner_ids_cache(user["id"])
    invalidate_owner_ids_cache(str(other_user_id))
    return {"ok": True}
