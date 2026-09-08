"""Math-education glossary: enforces consistent EN->ES terminology.

The glossary feeds two places:
  * the LLM prompt (as an authoritative term list), and
  * an adherence check that flags segments where a source term's expected
    translation is missing from the output (routed to the human reviewer).
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=8)
def load_terms(lang: str = "es") -> dict[str, str]:
    """Glossary for a target language, or empty when none has been authored yet.

    A missing glossary is normal for a newly added language: the LLM still
    translates, it just has no term list to be held to.
    """
    from babel import languages

    name = languages.get(lang).glossary
    if not name:
        return {}
    path = Path(__file__).with_name(name)
    if not path.exists():
        return {}
    terms = json.loads(path.read_text(encoding="utf-8"))["terms"]
    # Longest source term first so "unit rate" wins over "rate" when scanning.
    return dict(sorted(terms.items(), key=lambda kv: len(kv[0]), reverse=True))


def prompt_block(lang: str = "es") -> str:
    """Render the glossary as a compact instruction block for the LLM."""
    return "\n".join(f"  {en} -> {tgt}" for en, tgt in load_terms(lang).items())


def _contains_word(haystack: str, needle: str, inflected: bool = False) -> bool:
    # Spanish inflects for number and gender ("razones equivalentes" for
    # "equivalente"), so a bare \b after the term reports a false miss on every
    # plural. Allow a short inflectional tail when matching the target side.
    tail = r"\w{0,3}" if inflected else ""
    return re.search(rf"\b{re.escape(needle)}{tail}\b", haystack, re.IGNORECASE) is not None


def check_adherence(source_en: str, target: str, lang: str = "es") -> list[str]:
    """Return glossary terms present in the source whose target form is missing
    from the translation. Empty == adherent, or no glossary for this language."""
    misses: list[str] = []
    for en, want in load_terms(lang).items():
        if _contains_word(source_en, en) and not _contains_word(target, want, inflected=True):
            misses.append(f"{en}->{want}")
    return misses
