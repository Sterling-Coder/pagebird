"""Translator: wires the primary engine + glossary into segments.

Flow per run:
  1. Dedup      — identical sources translated once, fanned back out.
  2. Translate  — primary engine (or identity offline).
  3. Glossary   — adherence check adds a note; never blocks shipping.

Every translatable segment ships whatever the engine returned, including a
chunk that failed and fell back to its own source text — there is no
integrity gate, no secondary-engine comparison, and no needs_human routing
here. (`idml.rtl`'s figure-mirror flag in `pipeline.translate_pdf` is a
separate, still-live use of the `needs_human` status — a page mirrored for
RTL that holds a figure, not a translation-quality signal.)
"""

from __future__ import annotations

import logging
import re

from pagebirdy.glossary import glossary
from pagebirdy.models import Segment
from pagebirdy.translate import integrity
from pagebirdy.translate.engine import Engine

logger = logging.getLogger("pagebirdy.translate")

# Matches placeholder tokens so they can be stripped before Latin-word detection.
_PLACEHOLDER_RE = re.compile(r"⟦[^⟧]*⟧")

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


class Translator:
    def __init__(self, primary: Engine, secondary: Engine | None = None,
                 target_lang: str = "es"):
        # `secondary` is accepted (and still threaded through by every
        # caller, and still reported as `engine_secondary`) for backward
        # compatibility with callers that configure a DeepL key, but it is
        # never invoked here — its only use was the disagreement flag.
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

        # Engine subclasses defined ad hoc in tests predate progress_cb and
        # override translate(self, texts) with no second param — a blind
        # try/except TypeError around the call risks swallowing a real bug
        # from inside translate() and silently re-running (and re-billing)
        # the whole batch, so check the signature instead.
        import inspect

        try:
            accepts_progress = len(inspect.signature(self.primary.translate).parameters) >= 2
        except (TypeError, ValueError):
            accepts_progress = False
        primary_out = (self.primary.translate(sources, progress_cb) if accepts_progress
                       else self.primary.translate(sources))

        # Sources that came back from a failed chunk are still in their original
        # English form — the engine fell back rather than translating them.
        # Retrieve the set from the engine (only _ChunkedEngine subclasses expose it).
        chunk_failures: set[str] = getattr(self.primary, "failed_sources", set())
        # `engine.failures` carries the real exception per chunk (rate limit,
        # malformed JSON, ...) — without logging it here, a chunk failure is
        # only ever visible as the generic note on the segment, which has no
        # diagnostic value on its own.
        for detail in getattr(self.primary, "failures", []):
            logger.warning("translate: %s (%s)", detail, self.primary.name)

        for src, ptext in zip(sources, primary_out):
            self._apply(groups[src], src, ptext, chunk_failed=src in chunk_failures)

        return segments

    def _apply(self, group: list[Segment], src: str, ptext: str, *,
              chunk_failed: bool = False) -> None:
        for s in group:
            s.engine = self.primary.name
            s.target = ptext
            s.status = "translated"

        if chunk_failed:
            # The API call for this chunk failed and `ptext` is the source
            # text, not a translation — noted so a re-run is traceable, but
            # still shipped rather than left as a gap on the page.
            for s in group:
                s.notes.append("chunk API failure — source text returned untranslated")
            return

        real_engine = self.primary.name != "identity"
        misses = glossary.check_adherence(src, ptext, self.target_lang) if real_engine else []
        # Editorial rule: the target must still fit the source's line count.
        fits, why = integrity.line_count_ok(src, ptext)
        for s in group:
            if misses:
                s.notes.append("glossary miss: " + ", ".join(misses))
            if not fits and real_engine:
                s.notes.append(f"line-count risk: {why}")
