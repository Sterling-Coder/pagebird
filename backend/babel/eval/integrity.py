"""Content-integrity metrics — axis B.

"Did the pipeline lose, invent, or fail to translate anything?" Every metric here
is deterministic, needs no model and no network, and reads segment dicts exactly
as `review.store.ReviewStore.get_segments` returns them — so any job already in
the review DB is scoreable without re-translating it.

Two of these exist specifically because the shipping gates do not cover them:

  * `number_preservation` — `translate.integrity.verify` deliberately allows the
    engine to *add* numeric placeholders, and `Segment.restored_target` renders a
    hallucinated `⟦=5⟧` back to a bare `5`. So an invented or drifted number in
    prose ships today with nothing flagged. This counts them.
  * `source_leakage` / `script_conformance` — nothing in the pipeline checks that
    the target is in the target language at all. English left standing in a
    delivered "translated" document is the most visible failure there is.

Every rate is oriented so that **1.0 is good**, and every metric reports the
denominator it used (`applicable`) — a rate over three segments is not evidence,
and hiding the denominator is how eval suites start lying.
"""

from __future__ import annotations

import re
from collections import Counter
from statistics import mean, median

from babel import languages
from babel.glossary import glossary
from babel.translate import integrity as gate

# Statuses that mean "the pipeline produced a target it intends to ship".
# `needs_human` is excluded from quality rates but counted in coverage, because
# reassembly does still place a flagged translation (see verify.run_verification).
SHIPPED = ("translated", "tm_hit", "approved", "edited")

# Mirrors Segment.restored_target's final cleanup: a hallucinated numeric
# placeholder is rendered back as its bare value rather than shipped as ⟦=5⟧.
_HALLUCINATED = re.compile(r"⟦=([^⟧]*)⟧")

# A numeric literal, allowing internal decimal/grouping separators: 3, 3.5,
# 1,234, 1.234,56.
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")

# A "word" substantial enough that leaving it identical means no translation
# happened. Short tokens ("of", "A", "6") legitimately survive untouched.
_WORD = re.compile(r"[^\W\d_]{3,}", re.UNICODE)

# URLs, domains, emails and handles pass through translation verbatim. The bare
# `@` form matters: a real IDML job carried "editor@stockindesign" — an address
# with no TLD, which a dotted-email pattern misses.
_URL = re.compile(
    r"(?:https?://|www\.)\S+"
    r"|\S*@\S+"
    r"|\b\S+\.(?:com|org|net|edu|gov|io|co|uk|de|jp|kr)\b",
    re.IGNORECASE,
)

# An all-caps token this short is an acronym or a product code (PBI, MGMT, ISBN),
# not prose. Capped at 5 characters so a genuinely shouted heading word
# ("ANSWER") still counts as translatable text.
_ACRONYM_MAX = 5


def _rate(good: int, applicable: int) -> float | None:
    """None, not 1.0, when nothing was applicable — an empty rate is not a pass."""
    return round(good / applicable, 4) if applicable else None


def restored(text: str | None, placeholders: dict[str, str]) -> str:
    """Placeholder-free text, matching what actually lands in the document."""
    if not text:
        return ""
    for token, literal in placeholders.items():
        text = text.replace(token, literal)
    return _HALLUCINATED.sub(r"\1", text)


def _shipped(segments: list[dict]) -> list[dict]:
    return [s for s in segments if s["status"] in SHIPPED and (s.get("target") or "").strip()]


def translatable_words(text: str) -> list[str]:
    """Words a translation engine is actually expected to change.

    Measured on a real IDML job, the leakage and script gates failed on
    `www.stockindesign.com`, `PBI` and `MGMT` — a URL and two acronyms, all of
    which are correct exactly as they stand in a Korean document. Left in, they
    made a clean job report as broken, and a gate that cries wolf gets switched
    off. So URLs and short acronyms are removed *before* deciding whether a
    segment contained anything translatable at all.
    """
    return [w for w in _WORD.findall(_URL.sub(" ", text))
            if not (w.isupper() and len(w) <= _ACRONYM_MAX)]


# --- placeholder integrity -------------------------------------------------


def placeholder_integrity(segments: list[dict]) -> dict:
    """Re-run the hard math gate over stored segments. Must be 1.0.

    This is the pipeline's own stated accuracy guarantee, so scoring it is
    partly a regression check on the gate itself: a non-1.0 here means something
    wrote a target into the store that `translate.integrity.verify` rejects.
    """
    failures = []
    applicable = 0
    for s in segments:
        target = s.get("target")
        if target is None:
            continue
        applicable += 1
        ok, detail = gate.verify(s["source"], target)
        if not ok:
            failures.append({"seg_id": s["seg_id"], "page": s["page"], "detail": detail})
    return {
        "rate": _rate(applicable - len(failures), applicable),
        "applicable": applicable,
        "failures": len(failures),
        "examples": failures[:20],
    }


# --- coverage --------------------------------------------------------------


def coverage(segments: list[dict]) -> dict:
    """Fraction of reviewable segments that came back with a target at all.

    Catches silent skips: an engine failure that fell back to source text, or a
    segment that never left `pending`. The store only holds translatable
    segments (`save_job` skips whitespace-only ones), so the denominator is
    already the right one.
    """
    total = len(segments)
    counts = Counter(s["status"] for s in segments)
    with_target = sum(1 for s in segments if (s.get("target") or "").strip())
    return {
        "rate": _rate(with_target, total),
        "applicable": total,
        "with_target": with_target,
        "status_counts": dict(counts),
        "needs_human": counts.get("needs_human", 0),
    }


# --- numbers ---------------------------------------------------------------


def _digit_content(text: str) -> Counter:
    """Numeric literals reduced to bare digit strings.

    Separators are stripped rather than parsed because the decimal-separator
    policy (US `3.5` vs es-419 `3,5`) is still an open client decision — see
    CLAUDE.md. Comparing digit content means a *correctly localized* separator
    does not register as a lost number, while a genuinely changed value does.
    `number_format_changes` below reports the separator swaps separately, which
    is the data needed to actually settle that policy question.
    """
    out: Counter = Counter()
    for m in _NUMBER.finditer(text):
        digits = re.sub(r"[.,]", "", m.group(0)).lstrip("0") or "0"
        out[digits] += 1
    return out


def number_preservation(segments: list[dict]) -> dict:
    """Every number in the source must survive into the target.

    The placeholder gate does not cover this: it permits extra `⟦=…⟧` tokens and
    the restore step renders them to bare digits, so "24 students" can ship as
    "25 estudiantes" with every existing check green.

    **Dropped and added numbers are scored separately, and only drops gate.**
    Measured on real EN→KO output, every single "invented number" was correct
    localization rather than a defect:

        "Five boxes" -> "5상자"    a number word set as a digit
        "a mile"     -> "1마일"    the target states the unit count explicitly
        "January"    -> "1월"      Korean month names *are* numerals

    A metric that fails a job for those is a metric people learn to ignore. A
    number that vanished, though, is always wrong — so `rate` tracks drops, and
    additions are reported for inspection without failing anything.
    """
    dropped, added_only, format_changes = [], [], 0
    applicable = 0
    for s in _shipped(segments):
        src = restored(s["source"], s["placeholders"])
        tgt = restored(s["target"], s["placeholders"])
        src_nums, tgt_nums = _digit_content(src), _digit_content(tgt)
        if not src_nums and not tgt_nums:
            continue
        applicable += 1
        missing = sorted((src_nums - tgt_nums).elements())
        invented = sorted((tgt_nums - src_nums).elements())
        record = {"seg_id": s["seg_id"], "page": s["page"], "missing": missing,
                  "invented": invented, "source": src[:120], "target": tgt[:120]}
        if missing:
            dropped.append(record)
        elif invented:
            added_only.append(record)
        elif set(_NUMBER.findall(src)) != set(_NUMBER.findall(tgt)):
            # Same digits, different punctuation — a localized separator.
            format_changes += 1
    return {
        "rate": _rate(applicable - len(dropped), applicable),
        "applicable": applicable,
        "dropped": len(dropped),
        # Diagnostic only. A spike here is worth a look (an engine padding the
        # target with figures), but it is not a defect on its own.
        "added_only": len(added_only),
        "number_format_changes": format_changes,
        "examples": dropped[:20],
        "examples_added": added_only[:10],
    }


# --- glossary --------------------------------------------------------------


def glossary_adherence(segments: list[dict], lang: str) -> dict:
    """Rate over segments that actually contain a glossary term.

    Scoring over *all* segments would report ~0.99 on any document simply
    because most lines have no glossary term in them, which is why this
    restricts the denominator to segments where the glossary has an opinion.
    """
    terms = glossary.load_terms(lang)
    if not terms:
        return {"rate": None, "applicable": 0, "available": False,
                "reason": f"no glossary authored for {lang!r}"}

    misses, applicable = [], 0
    for s in _shipped(segments):
        src = restored(s["source"], s["placeholders"])
        tgt = restored(s["target"], s["placeholders"])
        # Same presence test the pipeline's own adherence check uses, so
        # "applicable" and "missed" can never disagree about what counts.
        if not any(glossary._contains_word(src, en) for en in terms):
            continue
        applicable += 1
        missed = glossary.check_adherence(src, tgt, lang)
        if missed:
            misses.append({"seg_id": s["seg_id"], "page": s["page"], "missed": missed,
                           "target": tgt[:120]})
    return {
        "rate": _rate(applicable - len(misses), applicable),
        "applicable": applicable,
        "missed": len(misses),
        "available": True,
        "examples": misses[:20],
    }


# --- untranslated text -----------------------------------------------------


# A name is not prose. Product and programme names stay in the source language
# in a correct translation -- a Spanish edition still says "i-Ready Connect" --
# so counting them as untranslated text reports a clean document as broken. On a
# real Spanish job 37 of 38 flagged segments were two brand names repeated.
#
# Shape alone cannot separate a brand from a heading: "Describe Position" and
# "Hungry Guppy" look identical. Repetition can. A product name recurs all
# through a document (24 and 13 times in that job); a heading does not. So a
# plain Title Case string is only excused when it repeats, while an internal
# capital ("i-Ready") is treated as a brand mark on its own.
_NAME_MAX_WORDS = 4
_NAME_MIN_REPEATS = 3
_INTERNAL_CAP = re.compile(r"[A-Za-z][^\sA-Z]*[A-Z]")


def _name_shape(text: str) -> str | None:
    """"brand" for an internal-capital mark, "title" for Title Case, else None."""
    stripped = text.strip()
    if not stripped or stripped[-1] in ".!?:;,":
        return None
    words = stripped.split()
    if not (1 <= len(words) <= _NAME_MAX_WORDS):
        return None
    alpha = [w for w in words if any(c.isalpha() for c in w)]
    if not alpha:
        return None
    if any(_INTERNAL_CAP.search(w) for w in alpha):
        return "brand"
    if all(w[0].isupper() for w in alpha if w[0].isalpha()):
        return "title"
    return None


def is_name_shaped(text: str, repeats: int = 1) -> bool:
    """True when a segment is a product or programme name rather than prose.

    `repeats` is how many times this exact source occurs in the document. Title
    Case needs repetition to qualify, so a one-off heading stays checked.
    """
    shape = _name_shape(text)
    if shape == "brand":
        return True
    return shape == "title" and repeats >= _NAME_MIN_REPEATS


def source_leakage(segments: list[dict]) -> dict:
    """Segments whose target is byte-identical to the source, ignoring case.

    Restricted to segments holding at least two substantial words, because a
    single word or a bare label ("Answers", "Grade 6", a proper noun) can be
    identical in both languages and is not evidence of failure. URLs and
    acronyms are stripped first — see `translatable_words`. Dependency-free and
    the cheapest high-value metric in the suite.
    """
    shipped = _shipped(segments)
    # How often each source occurs, so a repeated name can be told from a heading.
    repeats = Counter(restored(x["source"], x["placeholders"]).strip() for x in shipped)

    leaked, applicable = [], 0
    for s in shipped:
        if s.get("has_math_font"):
            continue  # math runs are deliberately passed through untranslated
        src = restored(s["source"], s["placeholders"]).strip()
        tgt = restored(s["target"], s["placeholders"]).strip()
        if len(translatable_words(src)) < 2:
            continue
        if is_name_shaped(src, repeats[src]):
            continue  # a product name reads the same in every language
        applicable += 1
        if " ".join(src.lower().split()) == " ".join(tgt.lower().split()):
            leaked.append({"seg_id": s["seg_id"], "page": s["page"], "text": src[:120]})
    return {
        "rate": _rate(applicable - len(leaked), applicable),
        "applicable": applicable,
        "leaked": len(leaked),
        "examples": leaked[:20],
    }


# Codepoint ranges that must appear in a target written in a non-Latin script.
_SCRIPTS: dict[str, list[tuple[int, int]]] = {
    "zh": [(0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF)],
    "ja": [(0x3040, 0x30FF), (0x4E00, 0x9FFF), (0x31F0, 0x31FF)],
    "ko": [(0x1100, 0x11FF), (0x3130, 0x318F), (0xAC00, 0xD7AF)],
    "hi": [(0x0900, 0x097F)],
    "ar": [(0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
}


def script_conformance(segments: list[dict], lang: str) -> dict:
    """For non-Latin targets: is the output actually in the target script?

    A far stronger leakage signal than string equality for zh/ja/ko/hi/ar — an
    English sentence lightly reworded still contains zero Hangul. Needs no
    language-ID model, so it runs offline. Latin-script targets fall through to
    `source_leakage` plus the optional `langdetect` check below.
    """
    ranges = _SCRIPTS.get(languages.get(lang).code)
    if not ranges:
        return {"rate": None, "applicable": 0, "available": False,
                "reason": f"{lang!r} is Latin-script; use source_leakage / language_id"}

    def in_script(ch: str) -> bool:
        cp = ord(ch)
        return any(lo <= cp <= hi for lo, hi in ranges)

    offenders, applicable = [], 0
    for s in _shipped(segments):
        if s.get("has_math_font"):
            continue
        src = restored(s["source"], s["placeholders"])
        tgt = restored(s["target"], s["placeholders"])
        if not translatable_words(src):
            # Numeric, symbolic, a URL or a bare acronym — nothing that should
            # have been rendered into the target script in the first place.
            continue
        applicable += 1
        if not any(in_script(ch) for ch in tgt):
            offenders.append({"seg_id": s["seg_id"], "page": s["page"], "target": tgt[:120]})
    return {
        "rate": _rate(applicable - len(offenders), applicable),
        "applicable": applicable,
        "offenders": len(offenders),
        "available": True,
        "examples": offenders[:20],
    }


def language_id(segments: list[dict], lang: str, sample: int = 300) -> dict:
    """Optional per-segment language detection (`langdetect`, if installed).

    Only meaningful for Latin-script targets, where `script_conformance` cannot
    help. Absent the package this reports unavailable rather than failing — the
    zero-dependency tier must stay runnable on a bare checkout.
    """
    try:
        from langdetect import DetectorFactory, detect  # type: ignore
    except ImportError:
        return {"rate": None, "applicable": 0, "available": False,
                "reason": "pip install langdetect"}

    DetectorFactory.seed = 0  # langdetect is stochastic by default
    want = languages.get(lang).code
    wrong, applicable = [], 0
    for s in _shipped(segments)[:sample]:
        tgt = restored(s["target"], s["placeholders"]).strip()
        if len(_WORD.findall(tgt)) < 3:
            continue  # detection on very short strings is noise
        applicable += 1
        try:
            got = detect(tgt).split("-")[0]
        except Exception:
            continue
        if got != want:
            wrong.append({"seg_id": s["seg_id"], "detected": got, "target": tgt[:120]})
    return {
        "rate": _rate(applicable - len(wrong), applicable),
        "applicable": applicable,
        "wrong": len(wrong),
        "available": True,
        "sampled": min(len(_shipped(segments)), sample),
        "examples": wrong[:20],
    }


# --- length ----------------------------------------------------------------


def length_ratio(segments: list[dict]) -> dict:
    """Target/source character-length distribution.

    Diagnostic, not pass/fail. EN→ES should centre near 1.15–1.25; a median far
    outside that means the engine is padding or truncating. This is also the
    measurement that finally calibrates `translate.integrity.LINE_BUDGET_RATIO`,
    which CLAUDE.md still flags as an uncalibrated estimate.
    """
    ratios = []
    for s in _shipped(segments):
        src = restored(s["source"], s["placeholders"]).strip()
        tgt = restored(s["target"], s["placeholders"]).strip()
        if len(src) < 10:
            continue  # percentage growth is meaningless on very short strings
        ratios.append(len(tgt) / len(src))
    if not ratios:
        return {"applicable": 0}
    ratios.sort()
    return {
        "applicable": len(ratios),
        "median": round(median(ratios), 3),
        "mean": round(mean(ratios), 3),
        "p90": round(ratios[int(len(ratios) * 0.9)], 3),
        "over_line_budget": sum(1 for r in ratios if r > gate.LINE_BUDGET_RATIO),
        "line_budget_ratio": gate.LINE_BUDGET_RATIO,
    }


# --- roll-up ---------------------------------------------------------------


def evaluate(segments: list[dict], lang: str = "es") -> dict:
    """Every axis-B metric for one job's segments."""
    return {
        "segments": len(segments),
        "target_lang": languages.get(lang).code,
        "placeholder_integrity": placeholder_integrity(segments),
        "coverage": coverage(segments),
        "number_preservation": number_preservation(segments),
        "glossary_adherence": glossary_adherence(segments, lang),
        "source_leakage": source_leakage(segments),
        "script_conformance": script_conformance(segments, lang),
        "language_id": language_id(segments, lang),
        "length_ratio": length_ratio(segments),
    }
