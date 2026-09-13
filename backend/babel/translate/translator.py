"""Translator: wires dual engines + integrity gate + glossary into segments.

Flow per run:
  1. Dedup      — identical sources translated once, fanned back out.
  2. Primary    — LLM translation (or identity offline).
  3. Secondary  — DeepL, if configured; compared for disagreement flags.
  4. Gate       — placeholder integrity; failures -> needs_human, never shipped.
  5. Glossary   — adherence check adds review notes.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor

from babel.glossary import glossary
from babel.models import Segment
from babel.translate import integrity
from babel.translate.engine import Engine

logger = logging.getLogger("babel.translate")

# Matches placeholder tokens so they can be stripped before Latin-word detection.
_PLACEHOLDER_RE = re.compile(r"⟦[^⟧]*⟧")
# Matches sequences of 3+ consecutive ASCII letters — a Latin-script "word".
_LATIN_WORD_RE = re.compile(r"[A-Za-z]{3,}")

# A segment that is nothing but a single Latin letter is a label on a diagram: a
# triangle's vertex, an axis, a variable. There is no word to translate, and a
# non-Latin target transliterates it into something that no longer matches the
# figure it labels ("P" became "पी" on a Hindi geometry page, while the
# drawn shape still said P). The prompt asks the model to leave these alone, but
# that is advisory; not sending them at all is not.
#
# An optional prime or single digit is kept so P', B1 and the like travel with the
# letter rather than being split off.
_LABEL_RE = re.compile(r"[A-Za-z][′']?\d?")


def _is_label(text: str) -> bool:
    """True when the whole segment is one Latin letter used as a label."""
    return bool(_LABEL_RE.fullmatch(_PLACEHOLDER_RE.sub("", text).strip()))


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower()).strip(" .,:;")


class Translator:
    def __init__(self, primary: Engine, secondary: Engine | None,
                 target_lang: str = "es"):
        self.primary = primary
        self.secondary = secondary
        self.target_lang = target_lang

    def run(self, segments: list[Segment], progress_cb=None) -> list[Segment]:
        """`progress_cb(done, total)`, if given, is forwarded to the primary
        engine and called as each of its chunks completes — best-effort,
        advisory progress reporting for the caller (see pipeline.py)."""
        pending: list[Segment] = []

        for s in segments:
            if not s.is_translatable:
                s.target, s.status, s.engine = s.source, "empty", "none"
                continue
            # Diagram labels pass straight through, in every language: sending
            # them to an engine can only corrupt the figure they belong to.
            if _is_label(s.source):
                s.target, s.status, s.engine = s.source, "translated", "label"
                continue
            pending.append(s)

        if not pending:
            return segments

        # Dedup identical protected sources.
        groups: dict[str, list[Segment]] = {}
        for s in pending:
            groups.setdefault(s.source, []).append(s)
        sources = list(groups.keys())

        def _translate_primary(texts: list[str]) -> list[str]:
            # Engine subclasses defined ad hoc in tests predate progress_cb
            # and override translate(self, texts) with no second param — a
            # blind try/except TypeError around the call risks swallowing a
            # real bug from inside translate() and silently re-running (and
            # re-billing) the whole batch, so check the signature instead.
            import inspect

            try:
                accepts_progress = len(inspect.signature(self.primary.translate).parameters) >= 2
            except (TypeError, ValueError):
                accepts_progress = False
            if accepts_progress:
                return self.primary.translate(texts, progress_cb)
            return self.primary.translate(texts)

        with ThreadPoolExecutor(max_workers=2) as ex:
            primary_future = ex.submit(_translate_primary, sources)
            secondary_future = (
                ex.submit(self._safe_secondary_translate, sources) if self.secondary else None
            )
            primary_out = primary_future.result()
            secondary_out = secondary_future.result() if secondary_future else [None] * len(sources)

        # Sources that came back from a failed chunk are still in their original
        # English form — the engine fell back rather than translating them.
        # Retrieve the set from the engine (only _ChunkedEngine subclasses expose it).
        chunk_failures: set[str] = getattr(self.primary, "failed_sources", set())
        # `engine.failures` carries the real exception per chunk (rate limit,
        # malformed JSON, ...) — without logging it here, a chunk failure is
        # only ever visible as the generic "chunk API failure" segment note,
        # which has no diagnostic value on its own.
        for detail in getattr(self.primary, "failures", []):
            logger.warning("translate: %s (%s)", detail, self.primary.name)

        for src, ptext, stext in zip(sources, primary_out, secondary_out):
            if src in chunk_failures:
                # The API call for this chunk failed; the text is the source, not
                # a translation. Mark it for human review so it is not silently
                # left in the source language on the output page.
                for s in groups[src]:
                    s.status = "needs_human"
                    s.target = None
                    s.engine = self.primary.name
                    s.notes.append("chunk API failure — source text returned; re-run to translate")
                continue
            self._apply(groups[src], src, ptext, stext)

        return segments

    def _safe_secondary_translate(self, sources: list[str]) -> list:
        try:
            return self.secondary.translate(sources)
        except Exception:  # the consensus engine is advisory; never fail the job for it
            return [None] * len(sources)

    def _apply(self, group: list[Segment], src: str, ptext: str, stext: str | None) -> None:
        ok, detail = integrity.verify(src, ptext)

        disagree = False
        if stext is not None:
            ok2, _ = integrity.verify(src, stext)
            disagree = ok2 and _normalize(ptext) != _normalize(stext)

        for s in group:
            s.engine = self.primary.name
            s.disagreement = disagree

            if not ok:
                s.status, s.target = "needs_human", None
                s.notes.append(f"placeholder integrity failed: {detail}")
                continue

            s.target = ptext
            real_engine = self.primary.name != "identity"
            misses = glossary.check_adherence(src, ptext, self.target_lang) if real_engine else []
            if misses:
                s.notes.append("glossary miss: " + ", ".join(misses))
            if disagree:
                # Advisory only: two good MT outputs differ on wording constantly.
                # Surface as a flag/note, but don't force review on synonyms.
                s.notes.append(f"engine disagreement (deepl: {stext!r})")

            # Editorial rule: the target must still fit the source's line count.
            fits, why = integrity.line_count_ok(src, ptext)
            if not fits and real_engine:
                s.notes.append(f"line-count risk: {why}")

            # Terminology drift and length risk are REVIEW signals, not ship
            # blockers. Demoting them to needs_human dropped a correct Spanish
            # translation and left the English on the page — the worst outcome of
            # the three. Reassembly refits the text into the source's own line
            # count anyway, so length can no longer break the layout. The only
            # hard gate is placeholder integrity, handled above.
            s.status = "translated"
            if misses or (not fits and real_engine):
                s.notes.append("flagged for review (translation still applied)")
