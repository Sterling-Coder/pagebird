"""One driver for every office/plain-text format.

    analyzing → extracting → classifying → translating → reconstructing → validating

Adapters only extract and write back. Protection, the engines, the glossary
and the review store are the same objects the PDF and IDML paths use. The
caller creates the job row up front (`ReviewStore.create_pending_job`) and
passes its id; this driver reports each stage through `on_stage`, and a
failure is recorded on that same row rather than as a second one.
"""

from __future__ import annotations

import inspect
import logging
import os
import time
from collections import Counter
from typing import Callable

from pagebirdy import languages
from pagebirdy.office import formats
from pagebirdy.office.adapter import writable
from pagebirdy.office.classify import should_translate
from pagebirdy.office.protect import protect, visible
from pagebirdy.office.runs import TAG_RULES
from pagebirdy.translate.engine import build_engines
from pagebirdy.translate.translator import Translator

logger = logging.getLogger("pagebirdy.office")

STAGES = ("analyzing", "extracting", "classifying", "translating", "reconstructing", "validating")
# Share of the run each stage has finished when it starts, for `progress_cb`.
_STAGE_PERCENT = {name: int(100 * i / (len(STAGES) + 1)) for i, name in enumerate(STAGES)}


class PipelineFailed(RuntimeError):
    """A run that failed after its job row was written; `job_id` is that row."""

    def __init__(self, message: str, job_id: str | None):
        super().__init__(message)
        self.job_id = job_id


def prepare(segments):
    """Protect what will be sent; set aside what never is.

    Deterministic, so `rebuild_from_review` re-derives the exact placeholder
    map a stored target was written against. Text read from a picture
    (`in_image`) arrives already classified and protected by the image
    pipeline's own rules (`office.images`), and goes as it is."""
    todo, kept = [], []
    for s in segments:
        if s.in_image:
            todo.append(s)
        elif should_translate(visible(s.source)):
            s.source, s.placeholders = protect(s.source)
            todo.append(s)
        else:
            s.status = "protected"
            kept.append(s)
    return todo, kept


def _output_path(src: str, out_dir: str, lang_code: str) -> str:
    stem, ext = os.path.splitext(os.path.basename(src))
    return os.path.join(out_dir, f"{stem}.{lang_code}{ext.lower()}")


def translate_document(src: str, out_dir: str, *, target_lang: str,
                       review_db: str | None = None, job_id: str | None = None,
                       original_filename: str | None = None,
                       on_stage: Callable[[int, str], None] | None = None, engines=None,
                       fmt: formats.Format | None = None, adapter=None,
                       extra_rules: str = "", extra_meta: dict | None = None) -> dict:
    """`job_id`, if given, is a row made by `ReviewStore.create_pending_job`;
    it is filled in with `finalize_job` on success or `mark_job_failed` on
    failure. `on_stage(percent, stage)` is advisory progress for the caller.

    `fmt`/`adapter` drive a format that is not an upload (the website path);
    `extra_rules` is appended to the engine prompt and `extra_meta` to the job
    row. Left out, every office upload runs exactly as before."""
    started = time.time()
    lang = languages.get(target_lang)
    fmt = fmt or formats.lookup(src)
    if fmt is None:
        raise formats.UnsupportedFile(f"no office adapter for {os.path.basename(src)}")
    adapter = adapter or formats.adapter_for(fmt)
    os.makedirs(out_dir, exist_ok=True)
    out = _output_path(src, out_dir, lang.code)
    meta = {"format": fmt.key, "source_lang": "en", "target_lang": lang.code,
            "target_language": lang.name, "direction": lang.direction, **(extra_meta or {})}
    return _run(src, out, fmt, adapter, lang, review_db, job_id, started, on_stage, engines,
                extra_rules, meta)


def _run(src, out, fmt, adapter, lang, review_db, job_id, started, on_stage, engines,
         extra_rules, job_meta) -> dict:
    """The stages of one run."""
    stage = STAGES[0]

    def enter(name: str) -> None:
        nonlocal stage
        stage = name
        if on_stage:
            on_stage(_STAGE_PERCENT[name], name)

    def fail(message: str, at: str) -> PipelineFailed:
        if job_id:
            from pagebirdy.review.store import ReviewStore

            store = ReviewStore(review_db)
            try:
                store.merge_job_meta(job_id, {"stage": "failed", "failed_stage": at})
                store.mark_job_failed(job_id, message, duration_sec=time.time() - started)
            finally:
                store.close()
        return PipelineFailed(message, job_id)

    try:
        enter("analyzing")
        units = adapter.units(src)
        enter("extracting")
        segments = adapter.extract(src)
        dupes = [k for k, n in Counter(s.id for s in segments).items() if n > 1]
        if dupes:
            raise RuntimeError(f"the document repeats segment address {dupes[0]}")
        enter("classifying")
        todo, kept = prepare(segments)
        enter("translating")
        if engines is None:
            tagged = any("⟦r" in s.source or "⟦x" in s.source for s in todo)
            context = visible(todo[0].source)[:120] if todo else ""
            primary, secondary = build_engines(doc_context=context, target_lang=lang.code,
                                               extra_rules=extra_rules + (TAG_RULES if tagged else ""))
        else:
            primary, secondary = engines
        Translator(primary, secondary, target_lang=lang.code).run(todo)
        enter("reconstructing")
        issues = adapter.rebuild(src, segments, out, lang)
        enter("validating")
        issues += adapter.validate(src, out)
    except Exception as e:
        logger.exception("office: %s failed while %s", src, stage)
        raise fail(str(e), stage) from e

    errors = [i.as_dict() for i in issues if i.level == "error"]
    warnings = [i.as_dict() for i in issues if i.level != "error"]
    if errors:
        raise fail(f"{errors[0]['where']}: {errors[0]['detail']}", "validating")

    status_counts = Counter(s.status for s in todo)
    report = {
        "job_id": job_id, "source": src, "output": out,
        "format": fmt.key, "source_lang": "en", "target_lang": lang.code,
        "target_language": lang.name, "direction": lang.direction,
        "units": units,
        "images_translated": len({s.id.rsplit(".", 1)[0] for s in todo
                                  if s.in_image and writable(s)}),
        "segments_total": len(segments),
        "segments_translated": status_counts.get("translated", 0),
        "segments_protected": len(kept),
        "status_counts": dict(status_counts),
        "overflow": [w for w in warnings if w["code"] == "overflow"],
        "reconstruction_issues": [i.as_dict() for i in issues],
        "warnings": warnings, "errors": errors,
        "engine_primary": primary.name,
        "engine_secondary": secondary.name if secondary else None,
        "engine_failures": list(getattr(primary, "failures", []))[:10],
        "has_output_pdf": False,
        "duration_sec": round(time.time() - started, 2),
    }
    if job_id:
        from pagebirdy.review.store import ReviewStore

        store = ReviewStore(review_db or "")
        try:
            summary = {k: report[k] for k in (
                "units", "segments_total", "segments_translated", "segments_protected",
                "status_counts", "overflow", "reconstruction_issues", "warnings",
                "engine_primary", "engine_secondary", "engine_failures")}
            # `finalize_job` replaces the row's meta wholesale, so the run's
            # own meta (format, languages, direction) is written back with it.
            store.finalize_job(job_id, out, todo, {**job_meta, **summary, "stage": "complete"},
                               duration_sec=report["duration_sec"], status="complete")
        except Exception as e:
            # Saving is part of the run: a failure here marks this same row
            # failed instead of escaping without a job id.
            logger.exception("office: %s failed while saving", src)
            raise fail(str(e), "saving") from e
        finally:
            store.close()
    logger.info("office: %s done (%s, %d segments, job %s)", src, fmt.key, len(segments), job_id)
    return report


def rebuild_from_review(job: dict, review_db: str, fmt: formats.Format | None = None) -> str:
    """Re-extract the source, re-protect it identically, lay the review rows
    over it by segment id, and rewrite the output: the office counterpart of
    `pipeline.regenerate_idml_from_review`."""
    from pagebirdy.review.store import ReviewStore

    src, out = str(job["source"]), str(job["output"])
    lang = languages.get((job.get("meta") or {}).get("target_lang"))
    fmt = fmt or formats.lookup(src)
    if fmt is None:
        raise formats.UnsupportedFile(f"no office adapter for {os.path.basename(src)}")
    adapter = formats.adapter_for(fmt)
    # Never OCR again on a rebuild: pictures come from the first run's cache.
    if "allow_ocr" in inspect.signature(adapter.extract).parameters:
        segments = adapter.extract(src, allow_ocr=False)
    else:
        segments = adapter.extract(src)
    prepare(segments)
    store = ReviewStore(review_db)
    try:
        rows = {r["seg_id"]: r for r in store.get_segments(job["id"])}
    finally:
        store.close()
    for s in segments:
        r = rows.get(s.id)
        if r is not None:
            s.target, s.status = r["target"], r["status"]
    adapter.rebuild(src, segments, out, lang)
    return out
