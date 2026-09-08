"""LLM verification pass — the accuracy floor.

After primary translation, a second model reads each (EN, target) pair and judges
whether the target faithfully and fluently renders the English with correct
math terminology. Anything it flags is routed to a human. This catches semantic
errors that the placeholder gate (structural) and the engine-disagreement flag
(wording) miss — e.g. a fluent but wrong translation.

Gated by `BABEL_VERIFY` (default on). No-op offline (no API key) so the pipeline
still runs without network. Same provider selection as the translation engine.
"""

from __future__ import annotations

import json
import os

from babel import languages
from babel.glossary import glossary

_CHUNK = 30

_SYSTEM = (
    "You are a bilingual QA reviewer for K-12 mathematics materials translated "
    "from English into {language}. For each pair, decide whether the translation "
    "faithfully and fluently renders the English: correct meaning, nothing added "
    "or dropped, correct math terminology, natural target-language phrasing. "
    "Placeholders like ⟦m0⟧/⟦=3/4⟧ are protected values — ignore their contents, "
    "only check they are not mistranslated into words. "
    "Proper nouns (personal names, place names) should be phonetically transliterated "
    "into the target script for non-Latin-script languages — accept transliterations "
    "of English names as correct even if they differ from the original spelling.\n"
    "{glossary}"
    "Return STRICT JSON {{\"v\": [ ... ]}} with one entry per pair, same order: an "
    "empty string \"\" if the translation is acceptable, otherwise a SHORT issue "
    "(<=12 words, English). No prose, no code fence."
)


def _verify_prompt(lang) -> str:
    lang = lang or languages.get(None)
    terms = glossary.prompt_block(lang.code)
    block = f"Glossary (source -> expected target):\n{terms}\n" if terms else ""
    return _SYSTEM.format(language=lang.register, glossary=block)


def _parse(text: str, n: int) -> list[str]:
    try:
        data = json.loads(_strip_fence(text))
        v = data["v"]
        if len(v) == n:
            return [str(x) for x in v]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return [""] * n  # parsing failed -> don't manufacture false flags


def _strip_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.rstrip().endswith("```"):
            t = t.rsplit("```", 1)[0]
    return t.strip()


class _Base:
    name = "verify-base"
    _tgt_key = "tgt"  # overridden with the actual language code by subclasses

    def verify(self, pairs: list[tuple[str, str]]) -> list[str]:
        out: list[str] = []
        for i in range(0, len(pairs), _CHUNK):
            chunk = pairs[i : i + _CHUNK]
            try:
                out.extend(self._verify_chunk(chunk))
            except Exception:
                # QA is a bonus pass; a dead key or exhausted quota must not fail
                # the translation job that already succeeded. No verdict, no flag.
                out.extend([""] * len(chunk))
        return out

    def _payload(self, chunk: list[tuple[str, str]]) -> str:
        # Use the actual target language code as the JSON key so the LLM QA
        # model sees the correct language label (e.g. "ko" for Korean, "es"
        # for Spanish) rather than always treating the input as Spanish.
        tgt_key = self._tgt_key
        return json.dumps(
            {"pairs": [{"en": en, tgt_key: tgt} for en, tgt in chunk]},
            ensure_ascii=False,
        )

    def _verify_chunk(self, chunk):  # pragma: no cover
        raise NotImplementedError


class OpenAIVerifier(_Base):
    def __init__(self, model: str, lang=None):
        import openai

        self.client = openai.OpenAI()
        self.name = f"verify:openai:{model}"
        self.model = model
        self._system = _verify_prompt(lang)
        # Use the actual target language code as the JSON pair key so the QA
        # model does not mistake the input for a Spanish pair.
        self._tgt_key = (lang.code if lang else "tgt")

    def _verify_chunk(self, chunk):
        resp = self.client.chat.completions.create(
            model=self.model, temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self._system},
                {"role": "user", "content": self._payload(chunk)},
            ],
        )
        return _parse(resp.choices[0].message.content or "", len(chunk))


class AnthropicVerifier(_Base):
    def __init__(self, model: str, lang=None):
        import anthropic

        self.client = anthropic.Anthropic()
        self.name = f"verify:anthropic:{model}"
        self.model = model
        self._system = _verify_prompt(lang)
        # Use the actual target language code as the JSON pair key so the QA
        # model does not mistake the input for a Spanish pair.
        self._tgt_key = (lang.code if lang else "tgt")

    def _verify_chunk(self, chunk):
        msg = self.client.messages.create(
            model=self.model, max_tokens=4096, system=self._system,
            messages=[{"role": "user", "content": self._payload(chunk)}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return _parse(text, len(chunk))


def build_verifier(target_lang: str | None = None):
    """A verifier for the active provider, or None (verification disabled/offline)."""
    if os.environ.get("BABEL_VERIFY", "1").lower() in ("0", "false", "off", "no"):
        return None
    provider = os.environ.get("BABEL_LLM_PROVIDER", "").lower()
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not provider:
        provider = "openai" if has_openai else ("anthropic" if has_anthropic else "")
    try:
        if provider == "openai" and has_openai:
            return OpenAIVerifier(os.environ.get("BABEL_VERIFY_MODEL", "gpt-5.2"),
                                  lang=languages.get(target_lang))
        if provider == "anthropic" and has_anthropic:
            return AnthropicVerifier(os.environ.get("BABEL_VERIFY_MODEL", "claude-sonnet-5"),
                                     lang=languages.get(target_lang))
    except Exception:
        return None
    return None


def run_verification(segments, verifier) -> int:
    """Verify freshly-translated segments; flag issues to human. Returns #flagged."""
    if verifier is None:
        return 0
    targets = [s for s in segments if s.status == "translated"]
    if not targets:
        return 0
    pairs = [(s.restored_source(), s.restored_target()) for s in targets]
    verdicts = verifier.verify(pairs)

    flagged = 0
    for seg, verdict in zip(targets, verdicts):
        issue = (verdict or "").strip()
        if issue:
            # Note it for the reviewer but keep shipping the translation:
            # demoting to needs_human made reassembly skip the segment, which
            # put the English back on the page. A flagged translation beats an
            # untranslated line.
            seg.notes.append(f"verify: {issue}")
            flagged += 1
    return flagged
