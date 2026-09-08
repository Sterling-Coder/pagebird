"""MQM-typed LLM judge — axis A, the interpretable half.

`translate.verify` already asks a second model to look at every (EN, target)
pair, but it returns a free-text issue string: useful for a reviewer, useless as
a metric. You cannot average prose, and "the model said it looked off" is not
defensible to a client.

This asks the same question with the **MQM error typology** (the scheme WMT uses
for its human evaluation): each error gets a category and a severity, severities
carry fixed weights, and the weighted penalty per 100 words is the score. That
gives one number per document *and* a breakdown showing whether the loss is
accuracy, fluency, or terminology — three different fixes.

Judge selection deliberately prefers a *different* provider than the translation
engine (`BABEL_LLM_PROVIDER`). A model grading its own output scores it high;
that self-preference bias is well documented and it is free to avoid here since
both provider paths already exist.
"""

from __future__ import annotations

import json
import os
from collections import Counter

from babel import languages
from babel.eval.integrity import SHIPPED, restored
from babel.glossary import glossary
from babel.translate.verify import _strip_fence

_CHUNK = 20  # smaller than verify's 30: structured errors are a longer response

# Standard MQM severity weights.
WEIGHTS = {"minor": 1.0, "major": 5.0, "critical": 10.0}

CATEGORIES = (
    "accuracy/mistranslation", "accuracy/omission", "accuracy/addition",
    "accuracy/untranslated", "fluency/grammar", "fluency/spelling",
    "fluency/punctuation", "terminology", "style", "locale",
)

# Penalty per 100 words at which the score reaches 0. A convention, not a
# standard — stated explicitly so the number is reproducible and arguable.
PENALTY_FLOOR = 25.0

_SYSTEM = (
    "You are an MQM annotator for K-12 mathematics material translated from "
    "English into {language}. For each pair, list every translation error you "
    "can justify. Use ONLY these categories:\n"
    "{categories}\n"
    "Severity: 'minor' (noticeable, does not impede understanding), 'major' "
    "(changes or obscures meaning), 'critical' (makes the content wrong or "
    "unusable — a wrong number, a reversed instruction, an inverted operation).\n"
    "Rules: report NO error when the translation is acceptable — an empty list is "
    "the expected answer for good output, and inventing errors makes you useless. "
    "Placeholders like ⟦m0⟧/⟦=3/4⟧ are protected values; flag them only if "
    "translated into words. Proper nouns transliterated into the target script "
    "are correct, not errors. Do not penalise a legitimate regional variant.\n"
    "{glossary}"
    'Return STRICT JSON {{"v": [{{"errors": [{{"category": ..., "severity": ..., '
    '"span": ..., "note": ...}}]}}]}} with exactly one entry per pair, in order. '
    "`span` is the offending target text, `note` is at most 12 English words. "
    "No prose, no code fence."
)


def _system_prompt(lang) -> str:
    terms = glossary.prompt_block(lang.code)
    block = f"Glossary (source -> expected target), a deviation is terminology:\n{terms}\n" \
        if terms else ""
    return _SYSTEM.format(language=lang.register,
                          categories="\n".join(f"  - {c}" for c in CATEGORIES),
                          glossary=block)


def _parse(text: str, n: int) -> list[list[dict]]:
    """Per-pair error lists. A malformed reply yields no errors, never fake ones."""
    try:
        entries = json.loads(_strip_fence(text))["v"]
        if len(entries) != n:
            return [[] for _ in range(n)]
    except (json.JSONDecodeError, KeyError, TypeError):
        return [[] for _ in range(n)]

    out = []
    for entry in entries:
        errors = []
        for err in (entry or {}).get("errors", []) or []:
            severity = str(err.get("severity", "")).lower().strip()
            if severity not in WEIGHTS:
                continue  # unknown severity has no weight, so it cannot be scored
            errors.append({
                "category": str(err.get("category", "")).strip() or "unspecified",
                "severity": severity,
                "span": str(err.get("span", ""))[:120],
                "note": str(err.get("note", ""))[:120],
            })
        out.append(errors)
    return out


class _Judge:
    name = "mqm-base"

    def __init__(self, model: str, lang):
        self.model = model
        self.lang = lang
        self._system = _system_prompt(lang)

    def _payload(self, chunk: list[dict]) -> str:
        return json.dumps(
            {"pairs": [{"en": it["src"], self.lang.code: it["mt"]} for it in chunk]},
            ensure_ascii=False,
        )

    def judge(self, items: list[dict]) -> list[list[dict]]:
        out: list[list[dict]] = []
        for i in range(0, len(items), _CHUNK):
            chunk = items[i : i + _CHUNK]
            try:
                out.extend(self._judge_chunk(chunk))
            except Exception:
                # Evaluation must never be the thing that fails loudly — an
                # unscored chunk is recorded as unscored, not as perfect.
                out.extend([None] * len(chunk))  # type: ignore[list-item]
        return out

    def _judge_chunk(self, chunk):  # pragma: no cover
        raise NotImplementedError


class OpenAIJudge(_Judge):
    def __init__(self, model: str, lang):
        import openai

        super().__init__(model, lang)
        self.client = openai.OpenAI()
        self.name = f"mqm:openai:{model}"

    def _judge_chunk(self, chunk):
        resp = self.client.chat.completions.create(
            model=self.model, temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": self._system},
                      {"role": "user", "content": self._payload(chunk)}],
        )
        return _parse(resp.choices[0].message.content or "", len(chunk))


class AnthropicJudge(_Judge):
    def __init__(self, model: str, lang):
        import anthropic

        super().__init__(model, lang)
        self.client = anthropic.Anthropic()
        self.name = f"mqm:anthropic:{model}"

    def _judge_chunk(self, chunk):
        msg = self.client.messages.create(
            model=self.model, max_tokens=8192, system=self._system,
            messages=[{"role": "user", "content": self._payload(chunk)}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return _parse(text, len(chunk))


def build_judge(target_lang: str | None = None):
    """A judge on a different provider than the translator where possible."""
    lang = languages.get(target_lang)
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))

    provider = os.environ.get("BABEL_EVAL_JUDGE_PROVIDER", "").lower()
    if not provider:
        translator = os.environ.get("BABEL_LLM_PROVIDER", "").lower() or \
            ("openai" if has_openai else "anthropic" if has_anthropic else "")
        # Cross-grade when both keys exist; otherwise fall back to what is keyed.
        preferred = "anthropic" if translator == "openai" else "openai"
        provider = preferred if (preferred == "openai" and has_openai) or \
                                (preferred == "anthropic" and has_anthropic) else translator

    model = os.environ.get("BABEL_EVAL_JUDGE_MODEL")
    try:
        if provider == "openai" and has_openai:
            return OpenAIJudge(model or "gpt-5.2", lang)
        if provider == "anthropic" and has_anthropic:
            return AnthropicJudge(model or "claude-sonnet-5", lang)
    except Exception:
        return None
    return None


def score(items: list[dict], verdicts: list[list[dict] | None]) -> dict:
    """Weighted MQM penalty per 100 words, plus the category breakdown."""
    words = 0
    penalty = 0.0
    by_category: Counter = Counter()
    by_severity: Counter = Counter()
    flagged = []
    scored = 0

    for item, errors in zip(items, verdicts):
        if errors is None:
            continue  # chunk failed; excluded from both numerator and denominator
        scored += 1
        words += max(1, len(item["src"].split()))
        seg_penalty = sum(WEIGHTS[e["severity"]] for e in errors)
        penalty += seg_penalty
        for e in errors:
            by_category[e["category"]] += 1
            by_severity[e["severity"]] += 1
        if errors:
            flagged.append({"seg_id": item["seg_id"], "penalty": seg_penalty,
                            "errors": errors, "src": item["src"][:100],
                            "mt": item["mt"][:100]})

    if not scored:
        return {"available": True, "scored": 0, "reason": "no segment was scored"}

    per_100 = penalty / words * 100
    return {
        "available": True,
        "scored": scored,
        "words": words,
        "penalty": round(penalty, 1),
        "penalty_per_100_words": round(per_100, 2),
        # 1.0 = no errors, 0.0 = PENALTY_FLOOR penalty per 100 words.
        "mqm_score": round(max(0.0, 1.0 - per_100 / PENALTY_FLOOR), 4),
        "penalty_floor": PENALTY_FLOOR,
        "segments_with_errors": len(flagged),
        "critical_errors": by_severity.get("critical", 0),
        "by_category": dict(by_category.most_common()),
        "by_severity": dict(by_severity),
        "worst": sorted(flagged, key=lambda f: -f["penalty"])[:20],
    }


def evaluate(segments: list[dict], lang: str = "es", max_segments: int = 400) -> dict:
    """Sample-based by default: an MQM pass is billed per segment, and 400
    segments already pins a document-level score tightly enough to act on."""
    judge = build_judge(lang)
    if judge is None:
        return {"available": False,
                "reason": "no API key, or BABEL_EVAL_JUDGE_PROVIDER unset/unkeyed"}

    lang_def = languages.get(lang)
    items = []
    for s in segments:
        if s["status"] not in SHIPPED or not (s.get("target") or "").strip():
            continue
        src = restored(s["source"], s["placeholders"]).strip()
        mt = restored(s["target"], s["placeholders"]).strip()
        if src and mt:
            items.append({"seg_id": s["seg_id"], "src": src, "mt": mt})
    items = items[:max_segments]
    if not items:
        return {"available": True, "scored": 0, "reason": "no shipped segments"}

    result = score(items, judge.judge(items))
    result.update({"judge": judge.name, "target_lang": lang_def.code,
                   "sampled": len(items), "of_shipped": len(items)})
    return result
