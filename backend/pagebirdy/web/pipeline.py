"""Website translation, end to end.

    fetching → analyzing → extracting → classifying → translating → reconstructing → validating

Fetching is this module's; everything after it is `office.pipeline.
translate_document` run on the fetched snapshot with the HTML adapter, so the
job row, its per-stage updates, the engines, the glossary and the review
store are the very ones documents use.
"""

from __future__ import annotations

import logging
import os
from typing import Callable
from urllib.parse import urlsplit

from pagebirdy.office import pipeline as office_pipeline
from pagebirdy.web import html
from pagebirdy.web.fetch import FetchError, fetch

logger = logging.getLogger("pagebirdy.web")

STAGES = ("fetching",) + office_pipeline.STAGES

# Appended to the engine prompt (`build_engines(extra_rules=…)`) for website
# text only: the shared system prompt stays exactly as it is.
WEB_RULES = (
    "\nWEB PAGE TEXT. This text comes from a public web page, not from a mathematics "
    "textbook: translate it as natural website copy for the target language — headings, "
    "navigation labels, buttons, product and article text — in the register a native "
    "website would use. Translate a short label (\"Home\", \"Sign in\", \"Learn more\") as "
    "the label a native site uses, not word for word. Keep brand, product and company "
    "names as written. Never add, drop or reorder protected tokens.\n"
)


def snapshot_name(url: str) -> str:
    """A file name for the fetched page that a person can recognise."""
    host = (urlsplit(url).hostname or "page").replace(":", "_")
    safe = "".join(c for c in host if c.isalnum() or c in ".-_") or "page"
    return f"{safe[:80]}.html"


def translate_website(url: str, job_dir: str, out_dir: str, *, target_lang: str,
                      review_db: str | None = None, job_id: str | None = None,
                      on_stage: Callable[[int, str], None] | None = None, engines=None,
                      extra_meta: dict | None = None) -> dict:
    """Fetch `url`, translate it, write `out_dir/<host>.<lang>.html`.

    A fetch failure raises `FetchError` before any job row exists; anything
    later raises `office.pipeline.PipelineFailed` carrying the row it marked
    failed (with the `FetchError` as its cause when the page itself was the
    problem: no text, too much text)."""
    if on_stage:
        on_stage(0, "fetching")
    page = fetch(url)
    data = html.snapshot(page)
    os.makedirs(job_dir, exist_ok=True)
    src = os.path.join(job_dir, snapshot_name(page.url))
    with open(src, "wb") as f:
        f.write(data)

    report = office_pipeline.translate_document(
        src, out_dir, target_lang=target_lang, review_db=review_db, job_id=job_id,
        original_filename=page.url, on_stage=on_stage, engines=engines,
        fmt=html.FORMAT, adapter=html.ADAPTER, extra_rules=WEB_RULES,
        extra_meta={**(extra_meta or {}), "source_url": url, "final_url": page.url})
    report["source_url"] = url
    report["final_url"] = page.url
    logger.info("web: %s translated to %s (job %s)", urlsplit(page.url).hostname,
                target_lang, report.get("job_id"))
    return report


def rebuild_from_review(job: dict, review_db: str) -> str:
    """The website counterpart of `office.pipeline.rebuild_from_review`."""
    return office_pipeline.rebuild_from_review(job, review_db, fmt=html.FORMAT)


def failure_code(exc: BaseException) -> str | None:
    """The `FetchError` code behind `exc`, if the page was the problem."""
    while exc is not None:
        if isinstance(exc, FetchError):
            return exc.code
        exc = exc.__cause__
    return None


def failure_message(exc: BaseException) -> str | None:
    while exc is not None:
        if isinstance(exc, FetchError):
            return str(exc)
        exc = exc.__cause__
    return None
