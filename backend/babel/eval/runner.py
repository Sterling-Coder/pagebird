"""Orchestration: score a job that is already in the review DB.

Evaluation is a read-only observer of the pipeline, so anything that has ever
been translated can be scored after the fact — no re-translation, no engine
calls, no API keys for the deterministic tier. That property is what makes this
usable as a regression harness: freeze a corpus of jobs, re-score on every
change, diff the scorecards.
"""

from __future__ import annotations

import json
import os
import re
import time

from babel import languages
from babel.eval import integrity as eval_integrity
from babel.eval import layout_idml, layout_pdf, mqm, quality, scorecard
from babel.review.store import ReviewStore

# Outputs are named `<base>.<lang>.<ext>` by pipeline.translate_pdf /
# translate_idml, which is the only place the target language survives — the
# review DB's meta blob does not record it.
_LANG_IN_NAME = re.compile(r"\.([a-z]{2})\.(?:pdf|idml|indd)$", re.IGNORECASE)


def _infer_lang(*paths: str | None) -> str:
    for path in paths:
        if not path:
            continue
        match = _LANG_IN_NAME.search(os.path.basename(path))
        if match:
            try:
                return languages.get(match.group(1)).code
            except ValueError:
                continue
    return languages.get(None).code


def _infer_format(job: dict) -> str:
    fmt = (job.get("meta") or {}).get("format")
    if fmt:
        return str(fmt)
    ext = os.path.splitext(job.get("source") or "")[1].lower()
    return "idml" if ext in (".idml", ".indd") else "pdf"


def _load_report(path: str | None) -> dict | None:
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def _find_job(store: ReviewStore, job_id: str) -> dict:
    for job in store.list_jobs():
        if job["id"] == job_id:
            return job
    raise KeyError(f"job {job_id!r} not found in review DB")


def evaluate_job(
    job_id: str,
    review_db: str = "babel_review.db",
    *,
    lang: str | None = None,
    report_json: str | None = None,
    export_json: str | None = None,
    gold_path: str | None = None,
    neural: bool = False,
    with_mqm: bool = False,
    with_bleu: bool = False,
    dpi: int = 100,
    pages: int | None = None,
    baseline_pdf: str | None = None,
    gpus: int = 0,
    max_segments: int = 2000,
) -> dict:
    """Full scorecard for one job.

    Defaults are the cheap tier: integrity + layout only, no downloads and no
    network. `neural=True` adds COMET/COMET-KIWI, `with_mqm=True` adds the LLM
    judge. `baseline_pdf` is the same document run through the identity engine —
    supplying it splits layout loss into reconstruction vs text growth (see
    `scorecard.baseline_delta`).
    """
    store = ReviewStore(review_db)
    try:
        job = _find_job(store, job_id)
        segments = store.get_segments(job_id)
    finally:
        store.close()

    source, output = job.get("source"), job.get("output")
    fmt = _infer_format(job)
    lang = lang or _infer_lang(output, source)

    result: dict = {
        "job_id": job_id,
        "format": fmt,
        "target_lang": lang,
        "source": source,
        "output": output,
        "created_at": job.get("created_at"),
        # Stamped so a downloaded report says when it was produced. Results are
        # cached, so "now" at read time would be a lie about older scorecards.
        "evaluated_at": time.time(),
        "original_filename": job.get("original_filename"),
        "duration_sec": job.get("duration_sec"),
        "engine_primary": (job.get("meta") or {}).get("engine_primary"),
        "integrity": eval_integrity.evaluate(segments, lang),
    }

    missing = [p for p in (source, output) if not p or not os.path.exists(p)]
    if missing:
        result["layout"] = {
            "available": False,
            "reason": f"document(s) not on disk: {missing}. Layout metrics need "
                      f"both files; integrity metrics above are unaffected.",
        }
    elif fmt == "idml":
        result["layout"] = layout_idml.evaluate(source, output, export_json=export_json)
        result["layout"]["note"] = (
            "IDML is XML, not a rendered page — raster fidelity for this path is "
            "measured by running the PDF evaluator on (source PDF, "
            "InDesign-exported PDF)."
        )
        # Glyph coverage is deliberately NOT scored here. InDesign sets these
        # runs in `Language.idml_font` (a font resolved inside InDesign), not in
        # the face `languages.py` hands the PDF reassembler. Checking IDML text
        # against the PDF path's Arial failed real jobs on ornament characters
        # the target font renders perfectly well.
        font = languages.get(lang).idml_font or "the run's own AppliedFont"
        result["layout"]["tofu"] = {
            "rate": None, "available": False,
            "reason": f"InDesign sets this text in {font}; glyph coverage is only "
                      f"observable in the exported PDF",
        }
    else:
        result["layout"] = layout_pdf.evaluate(
            source, output, segments=segments, lang=lang, dpi=dpi, pages=pages,
            report=_load_report(report_json),
        )

    if neural or gold_path:
        result["quality"] = quality.evaluate(
            segments, lang, gold_path=gold_path, neural=neural,
            with_bleu=with_bleu, gpus=gpus, max_segments=max_segments,
        )
    if with_mqm:
        result["mqm"] = mqm.evaluate(segments, lang)

    result["layout_score"] = scorecard.layout_score(result["layout"], fmt=fmt)
    if baseline_pdf and source and os.path.exists(baseline_pdf):
        base_layout = layout_pdf.evaluate(source, baseline_pdf, lang=lang, dpi=dpi,
                                          pages=pages)
        result["baseline"] = {"pdf": baseline_pdf,
                              "layout_score": scorecard.layout_score(base_layout)}
        result["baseline_delta"] = scorecard.baseline_delta(
            result["layout_score"], result["baseline"]["layout_score"])

    result["gates"] = scorecard.run_gates(result)
    # Computed last: it summarises the sections above and carries the gate
    # verdict with it.
    result["overall"] = scorecard.overall_score(result)
    # The same definitions the downloadable PDF prints, so the review panel and
    # the report cannot describe a number differently.
    from babel.eval import report_pdf

    result["explanations"] = report_pdf.glossary_entries(
        result["gates"], result["layout"], result["integrity"],
        result.get("quality"), result.get("mqm"),
    )
    result["score_formulas"] = [
        "Overall accuracy = 0.60 x Content + 0.40 x Structure",
        "Content = average of the content checks below",
        ("Structure = average of the IDML structural checks"
         if result["layout_score"].get("structural_only") else
         "Structure = 0.45 x Vector art + 0.30 x Pixel similarity"
         " + 0.25 x Text blocks"),
    ]
    return result


def evaluate_pdf_pair(src_pdf: str, out_pdf: str, *, lang: str | None = None,
                      dpi: int = 100, pages: int | None = None,
                      report_json: str | None = None) -> dict:
    """Layout-only scoring of two PDFs, with no review DB involved.

    Use when the job predates the review store or was run with `review_db=None`.
    Content-integrity and quality metrics need per-segment source/target pairs,
    so they are unavailable here — the rendered PDF alone cannot tell you which
    text was supposed to be a translation of what.
    """
    lang = lang or _infer_lang(out_pdf)
    layout = layout_pdf.evaluate(src_pdf, out_pdf, lang=lang, dpi=dpi, pages=pages,
                                 report=_load_report(report_json))
    result = {
        "format": "pdf", "target_lang": lang, "source": src_pdf, "output": out_pdf,
        "layout": layout,
        "layout_score": scorecard.layout_score(layout),
        "integrity": {"available": False,
                      "reason": "needs segment pairs from the review DB — "
                                "use `evaluate_job` instead"},
    }
    result["gates"] = scorecard.run_gates(result)
    result["overall"] = scorecard.overall_score(result)
    return result


def evaluate_idml_pair(src_idml: str, out_idml: str, *, export_json: str | None = None,
                       lang: str | None = None) -> dict:
    """Structural scoring of two IDML packages, with no review DB involved."""
    lang = lang or _infer_lang(out_idml)
    layout = layout_idml.evaluate(src_idml, out_idml, export_json=export_json)
    result = {
        "format": "idml", "target_lang": lang, "source": src_idml, "output": out_idml,
        "layout": layout,
        "layout_score": scorecard.layout_score(layout),
        "integrity": {"available": False,
                      "reason": "needs segment pairs from the review DB — "
                                "use `evaluate_job` instead"},
    }
    result["gates"] = scorecard.run_gates(result)
    result["overall"] = scorecard.overall_score(result)
    return result


def freeze_gold(review_db: str = "babel_review.db", out_path: str = "docs/eval/gold.jsonl",
                *, lang: str | None = None) -> dict:
    """Snapshot human-approved segments as a JSONL gold corpus.

    Every approval in the review UI writes an approved TM entry, so the review DB
    accumulates reference translations as a by-product of normal operation. This
    is where reference-based COMET and chrF++ get their references.

    Read from the review DB rather than the TM because TM rows hold *protected*
    text with no placeholder map attached, and a model handed `⟦=3/4⟧` scores the
    placeholder rather than the number. Review rows carry the map, so both sides
    can be restored to what a human would read.

    Snapshot and commit the result. Scoring against a live, growing TM makes the
    numbers move underneath you between runs for reasons unrelated to the code.
    """
    store = ReviewStore(review_db)
    try:
        rows: dict[str, dict] = {}
        skipped_lang = 0
        for job in store.list_jobs():
            job_lang = _infer_lang(job.get("output"), job.get("source"))
            if lang and job_lang != languages.get(lang).code:
                skipped_lang += 1
                continue
            for seg in store.get_segments(job["id"], status="approved"):
                src = eval_integrity.restored(seg["source"], seg["placeholders"]).strip()
                tgt = eval_integrity.restored(seg["target"], seg["placeholders"]).strip()
                if not src or not tgt:
                    continue
                # Later approvals win: a re-reviewed segment supersedes the old one.
                rows[src] = {"source": src, "target": tgt, "lang": job_lang,
                             "job_id": job["id"], "seg_id": seg["seg_id"]}
    finally:
        store.close()

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows.values():
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {"output": out_path, "entries": len(rows), "jobs_skipped_wrong_lang": skipped_lang,
            "lang": languages.get(lang).code if lang else "all"}
