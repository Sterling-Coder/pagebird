"""Translator: wires TM + dual engines + integrity gate + glossary into segments.

Flow per run:
  1. TM pass    — reuse any prior target for an identical protected source.
  2. Dedup      — identical sources translated once, fanned back out.
  3. Primary    — LLM translation (or identity offline).
  4. Secondary  — DeepL, if configured; compared for disagreement flags.
  5. Gate       — placeholder integrity; failures -> needs_human, never shipped.
  6. Glossary   — adherence check adds review notes.
Clean, agreed translations are written back to TM (unapproved) for reuse.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

from babel import languages as _languages
from babel.glossary import glossary
from babel.models import Segment
from babel.tm.store import TranslationMemory
from babel.translate import integrity
from babel.translate.engine import Engine

# Matches placeholder tokens so they can be stripped before Latin-word detection.
_PLACEHOLDER_RE = re.compile(r"\u27e6[^\u27e7]*\u27e7")
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


def _has_latin_words(text: str) -> bool:
    """True if `text` contains Latin-script words outside ⟦⟧ placeholders.

    Used to detect stale TM entries for non-Latin-script target languages
    (e.g. Korean, Chinese, Japanese, Hindi, Arabic) that were produced
    before the proper-noun transliteration rule was enforced. Such entries
    contain English names like "Cameron" in their target field; re-translating
    them with the current prompt will produce the correct Hangul/CJK/etc. form.
    """
    cleaned = _PLACEHOLDER_RE.sub("", text)
    return bool(_LATIN_WORD_RE.search(cleaned))


def _is_passthrough(source: str, target: str) -> bool:
    """True when a stored target is simply its own source.

    Restricted to strings with at least two real words: a product name or a
    single label reads the same in every language, and re-translating those on
    every run would spend an engine call to get the same answer back.
    """
    src = _PLACEHOLDER_RE.sub("", source)
    tgt = _PLACEHOLDER_RE.sub("", target)
    if len(_LATIN_WORD_RE.findall(src)) < 2:
        return False
    return _normalize(src) == _normalize(tgt)


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower()).strip(" .,:;")


class Translator:
    def __init__(self, primary: Engine, secondary: Engine | None,
                 tm: TranslationMemory | None, target_lang: str = "es"):
        self.primary = primary
        self.secondary = secondary
        self.tm = tm
        self.target_lang = target_lang
        # Resolve the latin_script flag once; used in the TM-hit staleness check.
        lang = _languages.get(target_lang)
        self._latin_script: bool = lang.latin_script

    def run(self, segments: list[Segment]) -> list[Segment]:
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
            hit = self.tm.lookup(s.source) if self.tm else None
            if hit:
                tm_target, approved = hit
                # For non-Latin-script target languages (Korean, Chinese, Japanese,
                # Hindi, Arabic …), reject TM entries whose target still contains
                # Latin-script words. These are stale entries produced before the
                # proper-noun transliteration rule was applied — e.g. "Cameron"
                # instead of the Hangul form. Re-translating them with the current
                # prompt yields the correct native-script rendering.
                if not self._latin_script and _has_latin_words(tm_target):
                    pending.append(s)
                    continue

                # Reject an entry whose target is just its source. Writeback now
                # refuses to memorise passthrough, but entries stored before that
                # guard existed are still in the database -- one failed run, whose
                # engine returned the English unchanged, leaves the English on
                # every later run of every document that shares the sentence. The
                # check is the same in any language: a translation that equals its
                # source translated nothing. Short strings are exempt because a
                # name or a label legitimately reads the same in both.
                if _is_passthrough(s.source, tm_target):
                    pending.append(s)
                    continue

                # Also reject TM entries where a single-letter math variable (e.g. A, B, x)
                # was erroneously transliterated (e.g. A -> 에이) before the prompt rule
                # exempted them.
                if not self._latin_script:
                    cleaned_src = _PLACEHOLDER_RE.sub("", s.source).strip()
                    if len(cleaned_src) == 1 and cleaned_src.isalpha() and cleaned_src.isascii():
                        cleaned_tgt = _PLACEHOLDER_RE.sub("", tm_target).strip()
                        if cleaned_tgt != cleaned_src:
                            pending.append(s)
                            continue

                s.target, s.engine = tm_target, "tm"
                s.status = "tm_hit"
                if not approved:
                    s.notes.append("tm hit (unapproved)")
            else:
                pending.append(s)

        if not pending:
            return segments

        # Dedup identical protected sources.
        groups: dict[str, list[Segment]] = {}
        for s in pending:
            groups.setdefault(s.source, []).append(s)
        sources = list(groups.keys())

        with ThreadPoolExecutor(max_workers=2) as ex:
            primary_future = ex.submit(self.primary.translate, sources)
            secondary_future = (
                ex.submit(self._safe_secondary_translate, sources) if self.secondary else None
            )
            primary_out = primary_future.result()
            secondary_out = secondary_future.result() if secondary_future else [None] * len(sources)

        # Sources that came back from a failed chunk are still in their original
        # English form — the engine fell back rather than translating them.
        # Retrieve the set from the engine (only _ChunkedEngine subclasses expose it).
        chunk_failures: set[str] = getattr(self.primary, "failed_sources", set())

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
            elif self.tm and real_engine and ptext != src:
                # Memorise only clean output, and never memorise passthrough: an
                # identity engine — or a real engine whose chunk failed and fell
                # back to its source — returns the text unchanged, and storing
                # that poisons the TM so every later run answers in the source language.
                self.tm.store(src, ptext, engine=self.primary.name, approved=False)
