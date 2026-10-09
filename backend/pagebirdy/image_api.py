"""Image translation endpoints, mounted on the main app by `pagebirdy.api`.

    GET  /api/image-translation/config        formats, limits and stages the UI may offer
    POST /api/image-translation/preview       PNG preview of a picked .ai/.psd (stateless)
    POST /api/image-translation               upload an image; returns 202 {job_id}
    GET  /api/image-translation/{job_id}      persisted job state + report
    GET  /api/image-translation/{job_id}/ocr  detected regions, for read-only review
    GET  /api/image-translation/{job_id}/source   the uploaded image
    GET  /api/image-translation/{job_id}/result   the translated image (?download=1)

Same shape as POST /api/translate: the job row is written before the work
starts, the work runs on the shared job executor, and the page polls
`GET /api/image-translation/{job_id}` for stage progress and the result. Source,
result, previews and the report live in storage under `jobs/<job_id>/`.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from pagebirdy import languages, storage
from pagebirdy.auth import require_trial_active, require_user
from pagebirdy.image import classify as image_classify
from pagebirdy.image.ocr import ocr_engine
from pagebirdy.image.pipeline import STAGES, ImageTranslationError, translate_image
from pagebirdy.image.validate import (ImageValidationError, max_bytes, max_pixels, safe_filename,
                                  supported_formats, validate_image_bytes)

logger = logging.getLogger("pagebirdy.image_api")

router = APIRouter()

_GENERIC_FAILURE = "Image translation failed. Please try again."


def _core():
    # pagebirdy.api imports this module to mount the router; reach its helpers lazily.
    from pagebirdy import api
    return api


def _report_path(output: str) -> str:
    return os.path.splitext(output)[0] + ".report.json"


def _key(job_id: str, local_path: str) -> str:
    return f"jobs/{job_id}/{os.path.basename(local_path)}"


def _json_default(value):
    """numpy scalars reach the report from the pixel measurements; a finished
    job must never fail on writing its own report."""
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


@router.get("/api/image-translation/config")
def image_config() -> dict:
    return {
        "formats": supported_formats(),
        "max_bytes": max_bytes(),
        "max_pixels": max_pixels(),
        "min_confidence": image_classify.min_confidence(),
        "ocr_available": ocr_engine() != "none",
        "stages": [{"key": k, "label": label} for k, label in STAGES],
    }


# Long side of an upload-time preview, in pixels: a thumbnail, not a render.
_PREVIEW_LONG_SIDE = 900


def render_upload_preview(data: bytes, info) -> bytes:
    """A PNG of what the user picked, for formats a browser cannot draw."""
    import io

    import fitz
    from PIL import Image

    if info.format == "AI":
        doc = fitz.open(stream=data, filetype="pdf")
        try:
            page = doc[0]
            zoom = min(4.0, _PREVIEW_LONG_SIDE / max(page.rect.width, page.rect.height))
            return page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False).tobytes("png")
        finally:
            doc.close()
    if info.format == "PSD":
        from psd_tools import PSDImage

        img = PSDImage.open(io.BytesIO(data)).composite()
    else:
        img = Image.open(io.BytesIO(data))
    img.thumbnail((_PREVIEW_LONG_SIDE, _PREVIEW_LONG_SIDE))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


@router.post("/api/image-translation/preview")
async def preview_upload(file: UploadFile | None = File(default=None),
                         user: dict = Depends(require_user)) -> Response:
    """Validate a picked file and return a PNG of it, before any job exists.

    Browsers cannot draw Illustrator or Photoshop files, so without this the
    upload card had nothing to show until the translation finished. Nothing
    is stored; the same validation as the real upload runs, so a bad file is
    rejected the moment it is picked.
    """
    if file is None:
        raise HTTPException(status_code=400, detail="No image uploaded.")
    data = await file.read(max_bytes() + 1)
    try:
        info = validate_image_bytes(data)
    except ImageValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        png = render_upload_preview(data, info)
    except Exception:  # noqa: BLE001
        logger.exception("upload preview failed")
        raise HTTPException(status_code=400, detail="The file could not be previewed.")
    return Response(content=png, media_type="image/png", headers={
        "Cache-Control": "no-store",
        "X-Image-Format": info.format,
        "X-Image-Width": str(info.width),
        "X-Image-Height": str(info.height),
        "X-Image-Units": "pt" if info.kind == "vector" else "px",
        "Access-Control-Expose-Headers": "X-Image-Format, X-Image-Width, X-Image-Height, X-Image-Units",
    })


@router.post("/api/image-translation")
async def create_image_translation(
    file: UploadFile | None = File(default=None),
    target_lang: str = Form(default=""),
    source_lang: str = Form(default="en"),
    project_id: str = Form(default=""),
    folder_id: str = Form(default=""),
    user: dict = Depends(require_user),
):
    core = _core()
    require_trial_active(user)
    if file is None:
        raise HTTPException(status_code=400, detail="No image uploaded.")
    # One byte past the limit is enough to know it is over; never read more.
    data = await file.read(max_bytes() + 1)
    try:
        info = validate_image_bytes(data)
    except ImageValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not target_lang:
        raise HTTPException(status_code=400, detail="Choose a target language.")
    try:
        lang = languages.get(target_lang)
    except ValueError:
        raise HTTPException(status_code=400, detail="Unsupported target language.")
    if (source_lang or "en").lower().split("-")[0] != "en":
        raise HTTPException(status_code=400, detail="Only English source images are supported.")
    # Pixels can only be read by OCR. An .ai's live text needs none (its
    # outlined text does, and the job reports that it went unread).
    if info.kind == "raster" and ocr_engine() == "none":
        raise HTTPException(status_code=503, detail="Image translation is not available: "
                                                    "no OCR engine is configured on this server.")

    if project_id:
        store = core._store()
        try:
            core._assert_owns_project(store, project_id, user)
        finally:
            store.close()

    original_name = safe_filename(file.filename or "image")
    # The extension comes from the decoded content, never from the client.
    stored_name = os.path.splitext(original_name)[0] + info.extension
    job_dir = os.path.join(core._upload_dir(), uuid.uuid4().hex[:12])
    os.makedirs(job_dir, exist_ok=True)
    saved = os.path.join(job_dir, stored_name)
    with open(saved, "wb") as f:
        f.write(data)
    out_dir = os.path.join(core._out_dir(), os.path.basename(job_dir))

    started = time.time()
    meta = {
        "format": "image", "target_lang": lang.code, "target_language": lang.name,
        "direction": lang.direction, "source_lang": "en",
        "image": {"format": info.format, "width": info.width, "height": info.height},
        "stage": "uploading", "stage_progress": {"uploading": 100},
    }
    store = core._store()
    try:
        job_id = store.create_pending_job(
            saved, original_filename=original_name, file_hash=hashlib.sha256(data).hexdigest(),
            file_size=len(data), meta=meta, project_id=project_id or None,
            folder_id=folder_id or None, created_by=user["id"])
    finally:
        store.close()
    core._activity(f"Uploaded {original_name} - translating to {lang.name}", owner_id=user["id"])
    logger.info("image upload: %s (%d bytes, %s %dx%d) -> %s job=%s", original_name, len(data),
                info.format, info.width, info.height, lang.code, job_id)

    def finish() -> dict:
        return _run_job(job_id, saved, out_dir, lang.code, meta, started, project_id)

    return await core._dispatch_job(finish, job_id, started, "image")


def _run_job(job_id: str, saved: str, out_dir: str, target_lang: str, meta: dict,
             started: float, project_id: str) -> dict:
    core = _core()
    stage_progress: dict[str, float] = {"uploading": 100}
    last_write = {"stage": "uploading", "at": 0.0}

    def progress(stage: str, pct: float, detail: str = "") -> None:
        stage_progress[stage] = round(pct, 1)
        # Persist on every stage change, and within a stage at most every
        # second, so a slow reconstruction loop does not hammer the database.
        now = time.time()
        if stage != last_write["stage"] or now - last_write["at"] > 1.0 or pct >= 100:
            last_write.update(stage=stage, at=now)
            try:
                store = core._store()
                try:
                    store.merge_job_meta(job_id, {"stage": stage, "stage_detail": detail,
                                                  "stage_progress": dict(stage_progress)})
                finally:
                    store.close()
            except Exception:  # noqa: BLE001 - a missed tick is harmless
                logger.exception("image job %s: progress write failed (non-fatal)", job_id)

    try:
        report, segments = translate_image(saved, out_dir, target_lang, progress=progress)
        report["job_id"] = job_id
        report_file = _report_path(report["output"])
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=_json_default)
        stage_progress["completed"] = 100

        # Everything durable goes to storage; the local files are scratch.
        source_key, output_key = _key(job_id, saved), _key(job_id, report["output"])
        core._upload_with_retry(saved, source_key)
        core._upload_with_retry(report["output"], output_key)
        core._upload_with_retry(report_file, _key(job_id, report_file))
        previews = {}
        for name in ("source_preview", "output_preview"):
            local = report.get(name)
            if local and os.path.isfile(local):
                core._upload_with_retry(local, _key(job_id, local))
                previews[name] = _key(job_id, local)

        warnings = report.get("warnings", [])
        store = core._store()
        try:
            store.finalize_job(
                job_id, output_key, segments,
                {**meta, "stage": "completed", "stage_progress": stage_progress,
                 "status_counts": report.get("status_counts", {}),
                 "warning_count": len(warnings),
                 "quality_passed": report["quality"]["passed"],
                 "engine_primary": report.get("engine_primary"),
                 "ocr_engine": report.get("ocr_engine"),
                 "output_format": report.get("output_format"), **previews},
                duration_sec=time.time() - started, status="complete")
            store.update_job_paths(job_id, source=source_key, output=output_key)
            if project_id:
                store.set_project_target_lang_if_unset(project_id, target_lang)
        finally:
            store.close()
        return _summary(report)
    except Exception as e:  # noqa: BLE001
        stage = getattr(e, "stage", None) or _current_stage(stage_progress)
        message = str(e) if isinstance(e, ImageTranslationError) else _GENERIC_FAILURE
        if not isinstance(e, ImageTranslationError):
            logger.exception("image job %s failed", job_id)
        else:
            logger.info("image job %s failed at %s: %s", job_id, stage, message)
        store = core._store()
        try:
            store.merge_job_meta(job_id, {"stage": "failed", "failed_stage": stage,
                                          "stage_progress": stage_progress})
            store.mark_job_failed(job_id, message, duration_sec=time.time() - started)
        finally:
            store.close()
        raise core._JobFailed(message) from e


def _current_stage(stage_progress: dict) -> str:
    order = [k for k, _ in STAGES]
    started = [k for k in order if k in stage_progress]
    return started[-1] if started else "uploading"


def _summary(report: dict) -> dict:
    """The report without its per-region detail - what a poll needs."""
    return {k: v for k, v in report.items() if k not in ("regions", "source")}


def _image_job(job_id: str, user: dict) -> dict:
    job = _core()._find_owned_job(job_id, user)
    if (job.get("meta") or {}).get("format") != "image":
        raise HTTPException(status_code=404, detail="Image translation not found.")
    return job


def _load_report(job: dict) -> dict | None:
    out = str(job.get("output") or "")
    data = storage.read_bytes(_report_path(out)) if out else None
    return json.loads(data) if data else None


@router.get("/api/image-translation/{job_id}")
def get_image_translation(job_id: str, user: dict = Depends(require_user)) -> dict:
    job = _image_job(job_id, user)
    meta = job.get("meta") or {}
    body = {
        "job_id": job["id"], "status": job["status"], "error": job.get("error"),
        "original_filename": job.get("original_filename"), "file_size": job.get("file_size"),
        "created_at": job.get("created_at"), "duration_sec": job.get("duration_sec"),
        "stage": meta.get("stage"), "stage_detail": meta.get("stage_detail"),
        "failed_stage": meta.get("failed_stage"),
        "stage_progress": meta.get("stage_progress", {}),
        "image": meta.get("image"), "source_lang": meta.get("source_lang", "en"),
        "target_lang": meta.get("target_lang"), "target_language": meta.get("target_language"),
        "direction": meta.get("direction"),
    }
    if job["status"] == "complete":
        report = _load_report(job)
        if report:
            body["report"] = _summary(report)
    return body


@router.get("/api/image-translation/{job_id}/ocr")
def get_image_ocr(job_id: str, user: dict = Depends(require_user)) -> dict:
    job = _image_job(job_id, user)
    report = _load_report(job) if job["status"] == "complete" else None
    if report is None:
        raise HTTPException(status_code=404, detail="OCR results are not available yet.")
    keys = ("id", "text", "bbox", "confidence", "language", "content_type", "action",
            "reason", "status", "target", "warnings", "notes")
    return {"job_id": job_id, "min_confidence": image_classify.min_confidence(),
            "regions": [{k: r.get(k) for k in keys} for r in report.get("regions", [])]}


_MEDIA = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
          ".webp": "image/webp", ".ai": "application/illustrator",
          ".psd": "image/vnd.adobe.photoshop", ".psb": "image/vnd.adobe.photoshop"}


def _serve(key: str | None, download: bool) -> Response:
    data = storage.read_bytes(key) if key else None
    if data is None:
        raise HTTPException(status_code=404, detail="File not available.")
    name = safe_filename(os.path.basename(key))
    media = _MEDIA.get(os.path.splitext(name)[1].lower(), "application/octet-stream")
    return Response(content=data, media_type=media, headers={
        "Content-Disposition": f'{"attachment" if download else "inline"}; filename="{name}"',
        "Cache-Control": "no-store"})


# Formats a browser cannot draw: viewed through a PNG preview, downloaded as is.
_NOT_VIEWABLE = (".ai", ".psd", ".psb")


def _viewable(job: dict, key: str | None, preview_key: str) -> str | None:
    if key and os.path.splitext(key)[1].lower() in _NOT_VIEWABLE:
        preview = (job.get("meta") or {}).get(preview_key)
        if not preview:
            raise HTTPException(status_code=404, detail="No preview is available yet.")
        return preview
    return key


@router.get("/api/image-translation/{job_id}/source")
def get_image_source(job_id: str, download: bool = False,
                     user: dict = Depends(require_user)) -> Response:
    job = _image_job(job_id, user)
    key = job.get("source")
    return _serve(key if download else _viewable(job, key, "source_preview"), download)


@router.get("/api/image-translation/{job_id}/result")
def get_image_result(job_id: str, download: bool = False,
                     user: dict = Depends(require_user)) -> Response:
    job = _image_job(job_id, user)
    if job["status"] != "complete":
        raise HTTPException(status_code=409, detail="The translated image is not ready yet.")
    key = job.get("output")
    return _serve(key if download else _viewable(job, key, "output_preview"), download)
