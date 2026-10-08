"""Short-text translation for the browser extension.

    POST /api/translate/text   {texts: [...], target_lang, context?}
                               -> {translations: [...], target_lang, direction}

Stateless: nothing is stored, no job row is written. The extension sends a
selection (one string) or a page's visible text in batches, and gets the
translations back in the same order. Numbers, URLs, emails and template
placeholders are protected exactly as in the document path (`office.protect`),
so they come back unchanged.

Authenticated like every other route. Because each call spends LLM budget, a
per-user sliding window and a per-request size cap bound it.
"""

from __future__ import annotations

import collections
import logging
import os
import threading
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from pagebirdy import languages
from pagebirdy.auth import require_trial_active, require_user
from pagebirdy.office.adapter import blank_segment
from pagebirdy.office.protect import protect
from pagebirdy.translate.engine import build_engines
from pagebirdy.translate.translator import Translator

logger = logging.getLogger("pagebirdy.text_api")

router = APIRouter()

MAX_ITEMS = 100
MAX_ITEM_CHARS = 5_000


def _int_env(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, default)))
    except ValueError:
        return default


_RATE: dict[str, collections.deque] = {}
_RATE_LOCK = threading.Lock()


def _take_slot(user_id: str) -> bool:
    """True if this user may make a call now (and counts it)."""
    limit = _int_env("PAGEBIRDY_TEXT_RATE_LIMIT", 120)
    window = _int_env("PAGEBIRDY_TEXT_RATE_WINDOW_SEC", 600)
    now = time.monotonic()
    with _RATE_LOCK:
        hits = _RATE.setdefault(user_id, collections.deque())
        while hits and now - hits[0] > window:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        if len(_RATE) > 10_000:
            for k in [k for k, d in _RATE.items() if not d or now - d[-1] > window]:
                del _RATE[k]
    return True


def reset_limits() -> None:
    """Tests only."""
    with _RATE_LOCK:
        _RATE.clear()


class TextRequest(BaseModel):
    texts: list[str] = Field(default_factory=list)
    target_lang: str = ""
    context: str = ""


def _translate(texts: list[str], lang, context: str, engines=None) -> list[str]:
    segments, index = [], {}
    for i, text in enumerate(texts):
        if not text.strip():
            continue
        seg = blank_segment(f"t{i}", text)
        seg.source, seg.placeholders = protect(text)
        segments.append(seg)
        index[i] = seg
    if segments:
        primary, secondary = engines or build_engines(doc_context=context[:120],
                                                      target_lang=lang.code)
        Translator(primary, secondary, target_lang=lang.code).run(segments)
        if getattr(primary, "failures", None):
            raise RuntimeError("engine failed")
    out = []
    for i, text in enumerate(texts):
        seg = index.get(i)
        out.append(text if seg is None else seg.restored_target())
    return out


@router.post("/api/translate/text")
async def translate_text(body: TextRequest, user: dict = Depends(require_user)) -> dict:
    require_trial_active(user)
    if not body.texts:
        raise HTTPException(status_code=400, detail="Nothing to translate.")
    if len(body.texts) > MAX_ITEMS:
        raise HTTPException(status_code=400, detail=f"At most {MAX_ITEMS} texts per request.")
    if any(len(t) > MAX_ITEM_CHARS for t in body.texts):
        raise HTTPException(status_code=400,
                            detail=f"Each text can be at most {MAX_ITEM_CHARS} characters.")
    if not body.target_lang:
        raise HTTPException(status_code=400, detail="Choose a target language.")
    try:
        lang = languages.get(body.target_lang)
    except ValueError:
        raise HTTPException(status_code=400, detail="Unsupported target language.")
    if not _take_slot(user["id"]):
        raise HTTPException(status_code=429,
                            detail="Too many translations in a short time. Please wait a moment.")
    try:
        translations = await run_in_threadpool(_translate, body.texts, lang, body.context)
    except Exception:  # noqa: BLE001 - never leak provider detail
        logger.exception("text translation failed")
        raise HTTPException(status_code=502, detail="The translation service failed. Please try again.")
    return {"translations": translations, "target_lang": lang.code, "direction": lang.direction}
