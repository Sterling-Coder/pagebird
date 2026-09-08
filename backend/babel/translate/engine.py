"""Translation engines.

`Engine.translate(list[str]) -> list[str]` is the whole contract. Every engine
must preserve `⟦m…⟧` placeholders verbatim; the integrity gate enforces it
afterwards regardless.

Engines available:
  * IdentityEngine  — passthrough, no network; makes the pipeline testable offline.
  * AnthropicEngine — LLM primary (glossary-aware, math-safe). Needs ANTHROPIC_API_KEY.
  * DeepLEngine     — secondary, for consensus/disagreement flags. Needs DEEPL_AUTH_KEY.

`build_engines()` returns (primary, secondary) based on available API keys,
falling back to identity so nothing crashes when offline.
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from babel import languages
from babel.glossary import glossary

_CHUNK = 40  # segments per LLM request
_MAX_CONCURRENT_CHUNKS = 2


class Engine:
    name = "base"
    failures: list[str] = []

    def translate(self, texts: list[str]) -> list[str]:  # pragma: no cover
        raise NotImplementedError


class _ChunkedEngine(Engine):
    """Translate in chunks, concurrently, surviving a mid-run API failure.

    A dead key, an exhausted quota or a network blip used to abort the whole job
    with a 500 after the earlier chunks had already been paid for. A failed chunk
    now falls back to its source text: those segments stay in the source language
    and are reported, while every chunk that did succeed still ships.

    `failed_sources` is populated with every source string that came back from a
    failed chunk, so the caller can mark those segments as `needs_human` rather
    than `translated` — preventing the blank-source-equals-blank-target check in
    reassembly from silently leaving them in the source language on the page.

    Chunks run concurrently (bounded pool) since the SDK clients here are
    synchronous, blocking, I/O-bound calls — output order always matches input
    order regardless of which chunk finishes first.
    """

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.failed_sources: set[str] = set()  # sources that came from a failed chunk

    def translate(self, texts: list[str]) -> list[str]:
        chunks = [texts[i:i + _CHUNK] for i in range(0, len(texts), _CHUNK)]
        if not chunks:
            return []
        results: list[list[str]] = [None] * len(chunks)
        with ThreadPoolExecutor(max_workers=_MAX_CONCURRENT_CHUNKS) as ex:
            future_to_idx = {
                ex.submit(self._safe_translate_chunk, i * _CHUNK, chunk): i
                for i, chunk in enumerate(chunks)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                results[idx] = future.result()
        out: list[str] = []
        for r in results:
            out.extend(r)
        return out

    def _safe_translate_chunk(self, start_index: int, chunk: list[str]) -> list[str]:
        try:
            return self._translate_chunk(chunk)
        except Exception as e:  # quota, network, malformed reply
            self.failures.append(f"chunk at {start_index}: {type(e).__name__}: {e}")
            self.failed_sources.update(chunk)  # remember which sources failed
            return list(chunk)

    def _translate_chunk(self, chunk: list[str]) -> list[str]:  # pragma: no cover
        raise NotImplementedError


class IdentityEngine(Engine):
    name = "identity"

    def translate(self, texts: list[str]) -> list[str]:
        return list(texts)


_SYSTEM = (
    "You are a professional translator localizing K-12 mathematics materials "
    "from English into {language}.{context} Rules:\n"
    "1. Translate ONLY natural-language text. Up to three kinds of placeholder "
    "appear and ALL must survive verbatim (same token, same count):\n"
    "   - ⟦m0⟧, ⟦m1⟧ … : opaque math. Never read, translate, or reformat it.\n"
    "   - ⟦=3/4⟧, ⟦=5⟧ … : a protected NUMBER whose value is shown. Keep the token "
    "exactly, but DO inflect surrounding words to agree with that quantity, gender "
    "or counter as the target language requires.\n"
    "   - ⟦br⟧ : a forced line break inside the sentence. Keep it exactly where "
    "it sits, character-for-character — never expand, describe, or substitute it "
    "with a space, newline, or any other character.\n"
    "{glossary}"
    "3. **bold** markers (double asterisks) mark words the source PDF sets in "
    "bold, mid-sentence. Keep exactly the same number of ** pairs, moved onto "
    "whichever translated word(s) carry that emphasis — never onto a different "
    "word, and never drop them.\n"
    "4. LENGTH IS A HARD LAYOUT CONSTRAINT, not a style preference. Each string "
    "is set back into the exact box the English occupied, at the same number of "
    "lines — if your translation runs long, the type shrinks to fit, page after "
    "page, until it is barely legible. Staying near the source length matters "
    "more than a more natural-sounding but longer phrasing.\n"
    "   Keep the same number of sentences and the same number of newline "
    "characters. Target the source's own character count; treat +15% as the "
    "ceiling, not a comfortable typical case — many languages (Portuguese, "
    "Spanish, French, German, Italian, Polish) run longer than English by "
    "default, so deliberately compress: choose the shortest natural wording, "
    "drop redundant articles/pronouns the target allows omitting, prefer a "
    "short synonym over a long one, and never add explanations, clarifications, "
    "hedges, or words the English does not have. If a literal, complete "
    "rendering still runs long, rephrase shorter rather than expanding — a "
    "slightly terser translation that fits beats a fuller one that doesn't.\n"
    "5. Keep tone and capitalization intent, and use the target language's own "
    "punctuation conventions (e.g. Spanish ¿ ¡, French spacing, CJK full-width).\n"
    "6. TRANSLATE EVERY STRING. Never echo the English back. A heading, a single "
    "word, a label and a table cell all get translated. Proper nouns (e.g. personal "
    "names, place names) must be rendered in the target language's own script: "
    "transliterate them phonetically if the target script is non-Latin (e.g. Hangul, "
    "CJK, Devanagari, Arabic). For Latin-script targets keep the original spelling. "
    "Never leave an English word in a non-Latin-script translation, EXCEPT for "
    "single-letter math variables (e.g. A, B, x, y) which MUST remain in Latin script.\n"
    "7. Return STRICT JSON: an object {{\"t\": [ ... ]}} with exactly one translated "
    "string per input, same order. No prose, no code fence.\n"
    "{examples}"
)

# Worked examples are per-language; without one the rules above still stand.
_EXAMPLES = {
    "es": (
        "Examples (register + placeholder handling):\n"
        "  EN: Write the missing digits in the boxes.\n"
        "  ES: Escribe los dígitos que faltan en los recuadros.\n"
        "  EN: Divide ⟦=3/4⟧ by ⟦=2⟧ to find the quotient.\n"
        "  ES: Divide ⟦=3/4⟧ entre ⟦=2⟧ para hallar el cociente.\n"
        "  EN: For problems ⟦=1-6⟧, plot each point on the coordinate plane.\n"
        "  ES: En los problemas ⟦=1-6⟧, ubica cada punto en el plano de coordenadas."
    ),
}


def _system_prompt(doc_context: str, lang) -> str:
    ctx = f" Document context: {doc_context}." if doc_context else ""
    terms = glossary.prompt_block(lang.code)
    block = f"2. Use this glossary authoritatively (source -> target):\n{terms}\n" if terms else ""
    return _SYSTEM.format(
        language=lang.register,
        glossary=block,
        context=ctx,
        examples=_EXAMPLES.get(lang.code, ""),
    )


def _parse_batch(text: str, chunk: list[str]) -> list[str]:
    """Parse a `{"t": [...]}` reply; raise ValueError on malformed output.

    Raising rather than silently returning the source text means the caller
    (_ChunkedEngine.translate) can catch the failure, record the affected
    sources in `failed_sources`, and let the translator mark those segments
    as `needs_human` for a re-run — instead of silently leaving them in the
    source language on the output page.
    """
    try:
        data = json.loads(_strip_fence(text))
        result = data["t"]
        if len(result) == len(chunk):
            return [str(x) for x in result]
        raise ValueError(
            f"LLM returned {len(result)} items for {len(chunk)}-item chunk"
        )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise ValueError(f"LLM batch parse failed: {e}; raw={text[:200]!r}") from e


class OpenAIEngine(_ChunkedEngine):
    def __init__(self, model: str = "gpt-5.2", doc_context: str = "", lang=None):
        import openai  # lazy: optional dep

        super().__init__()
        # Default SDK retry count (2, short backoff) gives up too soon under a
        # sustained 429 burst — e.g. several PDFs uploaded back-to-back exhaust
        # the account's rate limit for tens of seconds, not one blip.
        self.client = openai.OpenAI(max_retries=8)
        self.model = model
        self.name = f"openai:{model}"
        self._system = _system_prompt(doc_context, lang or languages.get(None))

    def _translate_chunk(self, chunk: list[str]) -> list[str]:
        # gpt-5 family only supports the default temperature (1) — passing 0
        # (wanted for deterministic translation) raises invalid_request_error.
        kwargs = {} if self.model.startswith("gpt-5") else {"temperature": 0}
        resp = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self._system},
                {"role": "user", "content": json.dumps({"inputs": chunk}, ensure_ascii=False)},
            ],
            **kwargs,
        )
        return _parse_batch(resp.choices[0].message.content or "", chunk)


class AnthropicEngine(_ChunkedEngine):
    def __init__(self, model: str = "claude-sonnet-5", doc_context: str = "", lang=None):
        import anthropic  # imported lazily so the dep is optional

        super().__init__()
        self.client = anthropic.Anthropic()
        self.model = model
        self.name = f"anthropic:{model}"
        self._system = _system_prompt(doc_context, lang or languages.get(None))

    def _translate_chunk(self, chunk: list[str]) -> list[str]:
        payload = json.dumps({"inputs": chunk}, ensure_ascii=False)
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=self._system,
            messages=[{"role": "user", "content": payload}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return _parse_batch(text, chunk)


class DeepLEngine(_ChunkedEngine):
    def __init__(self, lang=None):
        import deepl  # optional dep

        super().__init__()
        self.lang = lang or languages.get(None)
        if not self.lang.deepl:
            raise ValueError(f"DeepL has no target for {self.lang.code}")
        self.name = f"deepl:{self.lang.deepl}"
        self.client = deepl.Translator(os.environ["DEEPL_AUTH_KEY"])
        self._glossary = self._ensure_glossary()

    def _ensure_glossary(self):
        """Register our math glossary as a native DeepL glossary (best-effort)."""
        try:
            entries = glossary.load_terms(self.lang.code)
            if not entries:
                return None
            return self.client.create_glossary(
                f"babel-math-{self.lang.code}", source_lang="EN",
                target_lang=self.lang.deepl.split("-")[0],
                entries=deepl_entries(dict(entries)),
            )
        except Exception:
            return None  # translate without glossary rather than fail

    def _translate_chunk(self, chunk: list[str]) -> list[str]:
        # DeepL leaves ⟦…⟧ untouched (unknown tokens are copied verbatim).
        kwargs = dict(source_lang="EN", target_lang=self.lang.deepl,
                      preserve_formatting=True)
        if self._glossary is not None:
            kwargs["glossary"] = self._glossary
        results = self.client.translate_text(chunk, **kwargs)
        if isinstance(results, list):
            return [r.text for r in results]
        return [results.text]


def deepl_entries(entries: dict[str, str]):
    import deepl

    return deepl.GlossaryEntries(entries)


def _strip_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.rstrip().endswith("```"):
            t = t.rsplit("```", 1)[0]
    return t.strip()


def build_engines(doc_context: str = "", target_lang: str | None = None
                  ) -> tuple[Engine, Optional[Engine]]:
    """(primary, secondary) chosen from available API keys; identity fallback.

    Provider selection: `BABEL_LLM_PROVIDER` (openai|anthropic) forces one;
    otherwise OpenAI is preferred when its key is present, then Anthropic."""
    lang = languages.get(target_lang)
    primary: Engine = IdentityEngine()
    secondary: Optional[Engine] = None

    provider = os.environ.get("BABEL_LLM_PROVIDER", "").lower()
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not provider:
        provider = "openai" if has_openai else ("anthropic" if has_anthropic else "")

    try:
        if provider == "openai" and has_openai:
            primary = OpenAIEngine(
                os.environ.get("BABEL_LLM_MODEL", "gpt-5.2"),
                doc_context=doc_context, lang=lang,
            )
        elif provider == "anthropic" and has_anthropic:
            primary = AnthropicEngine(
                os.environ.get("BABEL_LLM_MODEL", "claude-sonnet-5"),
                doc_context=doc_context, lang=lang,
            )
    except Exception:  # SDK missing or client init failed — stay offline, don't crash
        primary = IdentityEngine()

    if os.environ.get("DEEPL_AUTH_KEY") and lang.deepl:
        try:
            secondary = DeepLEngine(lang=lang)
        except Exception:  # deepl missing, bad key, or no target — run single-engine
            secondary = None

    return primary, secondary
