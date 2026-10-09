"""Website translation endpoints, mounted on the main app by `pagebirdy.api`.

    POST /api/translate/website                  {url, target_lang, project_id?, folder_id?}
                                                 -> 202 {job_id, status: "processing"}
    GET  /api/jobs/{job_id}                      (existing) progress: meta.stage = fetching | analyzing
                                                 | extracting | classifying | translating
                                                 | reconstructing | validating;
                                                 a failed job carries `error`
    GET  /api/translate/website/{job_id}/result  the translated page (?download=1 to save it)
    GET  /api/translate/website/{job_id}/source  the fetched original, equally sanitized

Same shape as POST /api/translate and the image endpoints: the job row is
written first, the work runs on the shared job executor, and the page polls the
job. Source and result live in storage under `jobs/<job_id>/`. Errors are `{"detail": <message for a person>, "code": <stable key>}`; a
message never carries an internal address or a stack trace.

Served pages come from this API's origin, so besides being stripped of
everything executable (`web/sanitize.py`) they carry `Content-Security-Policy:
sandbox` with no `allow-scripts`/`allow-same-origin`: the browser gives them an
opaque origin that can reach neither this API nor its storage.
"""

from __future__ import annotations

import collections
import hashlib
import logging
import os
import threading
import time
import uuid
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from pagebirdy import languages, storage
from pagebirdy.auth import require_trial_active, require_user
from pagebirdy.office.pipeline import PipelineFailed
from pagebirdy.web import fetch as web_fetch
from pagebirdy.web import html as web_html
from pagebirdy.web.fetch import FetchError
from pagebirdy.web.pipeline import failure_code, failure_message, rebuild_from_review, translate_website

logger = logging.getLogger("pagebirdy.web_api")

router = APIRouter()

GENERIC_FAILURE = "Website translation failed. Please try again."
RATE_LIMITED = "Too many website translations in a short time. Please wait a few minutes and try again."
BUSY = "The translation service is busy with other websites. Please try again in a minute."


def _core():
    # pagebirdy.api imports this module to mount the router; reach its helpers lazily.
    from pagebirdy import api
    return api


def _int_env(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, default)))
    except ValueError:
        return default


# --- rate limiting ------------------------------------------------------------
# Per user, a sliding window, backed up by a global cap on concurrent website
# jobs.

_RATE: dict[str, collections.deque] = {}
_RATE_LOCK = threading.Lock()
_RUNNING = 0


def _take_slot(key: str) -> str | None:
    """None if this request may start a job (and counts it); else the error code."""
    global _RUNNING
    limit = _int_env("BABEL_WEB_RATE_LIMIT", 10)
    window = _int_env("BABEL_WEB_RATE_WINDOW_SEC", 600)
    max_running = _int_env("BABEL_WEB_MAX_RUNNING", 4)
    now = time.monotonic()
    with _RATE_LOCK:
        hits = _RATE.setdefault(key, collections.deque())
        while hits and now - hits[0] > window:
            hits.popleft()
        if len(hits) >= limit:
            return "rate_limited"
        if _RUNNING >= max_running:
            return "busy"
        hits.append(now)
        _RUNNING += 1
        # Forget sessions that have gone quiet, so the table cannot grow forever.
        if len(_RATE) > 10_000:
            for k in [k for k, d in _RATE.items() if not d or now - d[-1] > window]:
                del _RATE[k]
    return None


def _release_slot() -> None:
    global _RUNNING
    with _RATE_LOCK:
        _RUNNING = max(0, _RUNNING - 1)


def reset_limits() -> None:
    """Tests only."""
    global _RUNNING
    with _RATE_LOCK:
        _RATE.clear()
        _RUNNING = 0


# --- submit ---------------------------------------------------------------------

class WebsiteRequest(BaseModel):
    url: str = ""
    target_lang: str = ""
    project_id: str = ""
    folder_id: str = ""


def _error(status: int, code: str, message: str | None = None) -> JSONResponse:
    return JSONResponse({"detail": message or web_fetch.MESSAGES.get(code, GENERIC_FAILURE),
                         "code": code}, status_code=status)


def _precheck(url: str) -> None:
    """Everything that can be said about the URL without touching the network.
    The full check (DNS, every redirect, the connected peer) runs in the job."""
    parts = urlsplit(url)
    port = parts.port or (443 if parts.scheme == "https" else 80)
    if port not in web_fetch.ALLOWED_PORTS:
        raise FetchError("blocked", "Only websites on the standard ports (80 and 443) "
                                    "can be translated.")
    host = parts.hostname or ""
    web_fetch.check_host(host)
    try:
        import ipaddress
        ipaddress.ip_address(host)
    except ValueError:
        return
    if not web_fetch.ip_allowed(host):
        raise FetchError("blocked")


@router.post("/api/translate/website")
async def create_website_translation(body: WebsiteRequest, user: dict = Depends(require_user)):
    core = _core()
    require_trial_active(user)
    try:
        url = web_fetch.normalize_url(body.url)
        _precheck(url)
    except FetchError as e:
        return _error(400, e.code, str(e))
    if not body.target_lang:
        return _error(400, "invalid_language", "Choose a target language.")
    try:
        lang = languages.get(body.target_lang)
    except ValueError:
        return _error(400, "invalid_language", "Unsupported target language.")

    if body.project_id:
        store = core._store()
        try:
            core._assert_owns_project(store, body.project_id, user)
        finally:
            store.close()

    refused = _take_slot(user["id"])
    if refused == "rate_limited":
        return _error(429, "rate_limited", RATE_LIMITED)
    if refused == "busy":
        return _error(429, "busy", BUSY)

    started = time.time()
    host = urlsplit(url).hostname or url
    meta = {"format": "website", "source_url": url, "source_lang": "en",
            "target_lang": lang.code, "target_language": lang.name,
            "direction": lang.direction, "stage": "fetching"}
    try:
        store = core._store()
        try:
            job_id = store.create_pending_job(
                url, original_filename=url, meta=meta, project_id=body.project_id or None,
                folder_id=body.folder_id or None, created_by=user["id"])
        finally:
            store.close()
    except Exception:
        _release_slot()
        raise
    core._activity(f"Translating website {host} to {lang.name}", owner_id=user["id"])
    logger.info("website submitted: host=%s lang=%s job=%s", host, lang.code, job_id)

    def finish() -> dict:
        return _run(job_id, url, lang.code, meta, started, body.project_id)

    return await core._dispatch_job(finish, job_id, started, "website")


def _fail(job_id: str, message: str, started: float, stage: str | None = None) -> None:
    core = _core()
    store = core._store()
    try:
        if stage:
            store.merge_job_meta(job_id, {"stage": "failed", "failed_stage": stage})
        store.mark_job_failed(job_id, message, duration_sec=time.time() - started)
    finally:
        store.close()


def _run(job_id: str, url: str, lang_code: str, meta: dict, started: float,
         project_id: str) -> dict:
    core = _core()
    job_dir = os.path.join(core._upload_dir(), uuid.uuid4().hex[:12])
    out_dir = os.path.join(core._out_dir(), os.path.basename(job_dir))

    def on_stage(_percent: int, stage: str) -> None:
        try:
            store = core._store()
            try:
                store.merge_job_meta(job_id, {"stage": stage})
            finally:
                store.close()
        except Exception:  # noqa: BLE001 - a missed tick is harmless
            logger.exception("website job %s: progress write failed (non-fatal)", job_id)

    try:
        report = translate_website(url, job_dir, out_dir, target_lang=lang_code,
                                   review_db=core._REVIEW_DB, job_id=job_id, on_stage=on_stage,
                                   extra_meta={k: v for k, v in meta.items() if k != "stage"})
        # Durable copies of the fetched page and its translation.
        source_key = f"jobs/{job_id}/{os.path.basename(report['source'])}"
        output_key = f"jobs/{job_id}/{os.path.basename(report['output'])}"
        core._upload_with_retry(report["source"], source_key)
        core._upload_with_retry(report["output"], output_key)
        store = core._store()
        try:
            store.update_job_paths(job_id, source=source_key, output=output_key)
            if project_id:
                store.set_project_target_lang_if_unset(project_id, lang_code)
        finally:
            store.close()
        report["source"], report["output"] = source_key, output_key
        return report
    except FetchError as e:
        logger.info("website job %s refused: %s", job_id, e.code)
        _fail(job_id, str(e), started, "fetching")
        raise core._JobFailed(str(e)) from e
    except PipelineFailed as e:
        message = failure_message(e) or GENERIC_FAILURE
        if failure_code(e) is None:
            logger.info("website job %s failed in the pipeline: %s", job_id, e)
        _fail(job_id, message, started)  # never the raw exception text
        raise core._JobFailed(message) from e
    except Exception as e:  # noqa: BLE001
        logger.exception("website job %s failed", job_id)
        _fail(job_id, GENERIC_FAILURE, started)
        raise core._JobFailed(GENERIC_FAILURE) from e
    finally:
        _release_slot()


# --- serving ----------------------------------------------------------------------

def _frame_ancestors() -> str:
    origins = os.environ.get("CORS_ORIGINS", "*")
    if origins.strip() == "*":
        return "*"
    return " ".join(["'self'"] + [o.strip() for o in origins.split(",") if o.strip()])


def page_headers(filename: str, download: bool) -> dict:
    csp = ("sandbox; default-src 'none'; script-src 'none'; object-src 'none'; "
           "frame-src 'none'; child-src 'none'; worker-src 'none'; connect-src 'none'; "
           "form-action 'none'; base-uri http: https:; "
           "style-src http: https: data: 'unsafe-inline'; img-src http: https: data: blob:; "
           "font-src http: https: data:; media-src http: https:; "
           f"frame-ancestors {_frame_ancestors()}")
    safe = "".join(c for c in filename if c.isalnum() or c in "-_. ") or "website.html"
    return {
        "Content-Security-Policy": csp,
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store",
        "Content-Disposition": f'{"attachment" if download else "inline"}; filename="{safe}"',
    }


def _website_job(job_id: str, user: dict) -> dict:
    try:
        job = _core()._find_owned_job(job_id, user)
    except Exception:  # HTTPException 404 from the ownership check
        raise _NotFound()
    if (job.get("meta") or {}).get("format") != "website":
        raise _NotFound()
    return job


class _NotFound(Exception):
    pass


def _not_found() -> JSONResponse:
    return _error(404, "not_found", "Website translation not found.")


def serve_result(job: dict, download: bool) -> Response:
    """The translated page, as the last build left it (a reviewer's edit
    rebuilds it through `POST /api/jobs/{id}/rebuild`)."""
    if job["status"] != "complete":
        return _error(409, "not_ready", "The translated website is not ready yet.")
    key = str(job.get("output") or "")
    data = storage.read_bytes(key) if key else None
    if data is None:
        return _error(404, "not_found", "The translated website is no longer available.")
    return Response(data, media_type="text/html; charset=utf-8",
                    headers=page_headers(os.path.basename(key), download))


@router.get("/api/translate/website/{job_id}/result")
def get_website_result(job_id: str, download: bool = False, user: dict = Depends(require_user)):
    try:
        job = _website_job(job_id, user)
    except _NotFound:
        return _not_found()
    return serve_result(job, download)


@router.get("/api/translate/website/{job_id}/source")
def get_website_source(job_id: str, download: bool = False, user: dict = Depends(require_user)):
    import tempfile

    try:
        job = _website_job(job_id, user)
    except _NotFound:
        return _not_found()
    key = str(job.get("source") or "")
    if not key.endswith(".html"):
        return _error(404, "not_found", "The original page is not available.")
    with tempfile.TemporaryDirectory() as tmp:
        local = os.path.join(tmp, os.path.basename(key))
        if not storage.download_to(key, local):
            return _error(404, "not_found", "The original page is not available.")
        try:
            data = web_html.render_source(local)
        except FetchError:
            return _error(404, "not_found", "The original page is not available.")
    return Response(data, media_type="text/html; charset=utf-8",
                    headers=page_headers(os.path.basename(key), download))
