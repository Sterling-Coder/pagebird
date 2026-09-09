"""Target-language registry — the single place a language is described.

Everything that has to change per language is declared here once: the register
the LLM is asked to write in, the DeepL code for the consensus engine, the
glossary file, and the font script needed to actually render the glyphs. Adding
a language is one entry, not a grep across the pipeline.

`wrapping` records how the reassembly stage can set the text:
  * "space"    — words separated by spaces; wrap at spaces (Latin, Cyrillic…).
  * "char"     — no word spaces; wrap between characters (Chinese, Japanese).
  * "rtl"      — right-to-left; the draft PDF path cannot shape or reorder these
                 runs, so they are refused up front rather than rendered wrongly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Language:
    code: str
    name: str  # shown in the UI
    register: str  # the instruction handed to the LLM
    wrapping: str = "space"
    direction: str = "ltr"
    latin_script: bool = True  # False for languages whose native script is not Latin
                               # (Hangul, CJK, Devanagari, Arabic, …). Used to
                               # detect stale TM entries that contain un-transliterated
                               # Latin proper nouns.
    deepl: str | None = None  # DeepL target code, None = no consensus engine
    glossary: str | None = None  # filename in babel/glossary/
    fonts: dict[str, list[str]] = field(default_factory=dict)  # style -> candidates
    idml_font: str | None = None  # AppliedFont override for the IDML write-back path


# Full-Unicode faces per script. First existing path wins; Windows / macOS /
# Linux are all listed so the same code runs anywhere.
_LATIN = {
    "regular": [
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "bold": [
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "italic": [
        "C:/Windows/Fonts/ariali.ttf",
        "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
    ],
    "bolditalic": [
        "C:/Windows/Fonts/arialbi.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    ],
    # Used when the source PDF declares a face as serif in its font descriptor.
    # Substituting a sans for a serif display face is the most visible way a
    # translated page stops looking like the original.
    "serifregular": [
        "C:/Windows/Fonts/times.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ],
    "serifbold": [
        "C:/Windows/Fonts/timesbd.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ],
    "serifitalic": [
        "C:/Windows/Fonts/timesi.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
    ],
    "serifbolditalic": [
        "C:/Windows/Fonts/timesbi.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
    ],
}


def _script(*paths: str) -> dict[str, list[str]]:
    """One face used for every style — these families ship no synthetic italics."""
    return {style: list(paths) for style in ("regular", "bold", "italic", "bolditalic")}


def _script_with_bold(regular: list[str], bold: list[str]) -> dict[str, list[str]]:
    """Map regular and bold CJK/complex faces. Italics fall back to upright."""
    return {
        "regular": regular,
        "italic": regular,
        "bold": bold,
        "bolditalic": bold,
    }


# Real bold faces per script (rather than reusing the regular weight for both):
# a heading set in Korean or Hebrew comes out visibly bold instead of flat.
_CJK_SC = _script_with_bold(
    ["NotoSansSC-Regular.ttf",
     "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simsun.ttc",
     "/System/Library/Fonts/PingFang.ttc",
     "/System/Library/Fonts/STHeiti Medium.ttc",
     "/System/Library/Fonts/Hiragino Sans GB.ttc"],
    ["NotoSansSC-Bold.ttf",
     "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simsun.ttc",
     "/System/Library/Fonts/PingFang.ttc"],
)
_CJK_JP = _script_with_bold(
    ["C:/Windows/Fonts/YuGothM.ttc", "C:/Windows/Fonts/msgothic.ttc",
     "/System/Library/Fonts/Hiragino Sans GB.ttc"],
    ["C:/Windows/Fonts/YuGothB.ttc", "C:/Windows/Fonts/msgothic.ttc",
     "/System/Library/Fonts/Hiragino Sans GB.ttc"],
)
_CJK_KR = _script_with_bold(
    ["C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc"],
    ["C:/Windows/Fonts/malgunbd.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc"],
)
# Simplified Chinese, Devanagari, and the RTL scripts below lead with a
# vendored face (see babel/fonts/README.md) so output does not depend on
# what the host OS happens to have installed. System paths stay as a last
# resort; `fonts.resolve` always prefers the bundled entry. (Japanese/Korean
# above still lean on system fonts only — no vendored face for those yet,
# so they'll hit the same "no installed font" error on a bare Linux host.)
_DEVANAGARI = _script_with_bold(
    ["NotoSansDevanagari-Regular.ttf", "C:/Windows/Fonts/Nirmala.ttf",
     "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc",
     "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf"],
    ["NotoSansDevanagari-Bold.ttf", "C:/Windows/Fonts/NirmalaB.ttf",
     "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc",
     "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf"],
)
_ARABIC = _script_with_bold(
    ["NotoNaskhArabic-Regular.ttf", "C:/Windows/Fonts/tahoma.ttf"],
    ["NotoNaskhArabic-Bold.ttf", "C:/Windows/Fonts/tahomabd.ttf"],
)
_HEBREW = _script_with_bold(
    ["NotoSansHebrew-Regular.ttf", "C:/Windows/Fonts/arial.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    ["NotoSansHebrew-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"],
)
# Urdu is properly set in Nastaliq — but we cannot render it. Nastaliq composes
# nearly the whole script through OpenType GSUB substitution and leaves its base
# glyphs empty, and MuPDF does not apply those rules: with Noto Nastaliq Urdu
# every letter draws blank while the digits come through, so the page renders as
# numbers floating on nothing. Naskh is the wrong style for Urdu but sets it
# correctly and legibly, which beats a blank page. See fonts/README.md;
# tests/test_rtl.py counts the ink so this cannot regress unnoticed.
_URDU = _ARABIC


LANGUAGES: dict[str, Language] = {
    "es": Language(
        "es", "Spanish",
        "Spanish (es-419, Latin American, US bilingual-education register)",
        deepl="ES", glossary="math_es419.json", fonts=_LATIN,
    ),
    "fr": Language("fr", "French", "French (fr-FR)", deepl="FR", fonts=_LATIN),
    "pt": Language("pt", "Portuguese", "European Portuguese (pt-PT)",
                   deepl="PT-PT", glossary="math_ptpt.json", fonts=_LATIN),
    "de": Language("de", "German", "German (de-DE)", deepl="DE", fonts=_LATIN),
    "it": Language("it", "Italian", "Italian (it-IT)", deepl="IT", fonts=_LATIN),
    "pl": Language("pl", "Polish", "Polish (pl-PL)", deepl="PL", fonts=_LATIN),
    "vi": Language("vi", "Vietnamese", "Vietnamese (vi-VN)", fonts=_LATIN),
    "tl": Language("tl", "Tagalog", "Tagalog / Filipino (fil-PH)", fonts=_LATIN),
    "zh": Language("zh", "Chinese (Simplified)", "Simplified Chinese (zh-CN)",
                   wrapping="char", latin_script=False, deepl="ZH", fonts=_CJK_SC,
                   idml_font="Noto Sans SC"),
    "ja": Language("ja", "Japanese", "Japanese (ja-JP)",
                   wrapping="char", latin_script=False, deepl="JA", fonts=_CJK_JP,
                   idml_font="Noto Sans JP"),
    "ko": Language("ko", "Korean", "Korean (ko-KR)",
                   latin_script=False, deepl="KO", fonts=_CJK_KR, idml_font="Noto Sans KR"),
    "hi": Language("hi", "Hindi", "Hindi (hi-IN)",
                   latin_script=False, fonts=_DEVANAGARI, idml_font="Noto Sans Devanagari"),
    "ar": Language("ar", "Arabic", "Modern Standard Arabic",
                   direction="rtl", latin_script=False, fonts=_ARABIC,
                   idml_font="Noto Sans Arabic"),
    "he": Language("he", "Hebrew", "Modern Hebrew (he-IL)",
                   direction="rtl", latin_script=False, fonts=_HEBREW,
                   idml_font="Noto Sans Hebrew"),
    "fa": Language("fa", "Persian", "Persian / Farsi (fa-IR)",
                   direction="rtl", latin_script=False, fonts=_ARABIC,
                   idml_font="Noto Sans Arabic"),
    "ur": Language("ur", "Urdu", "Urdu (ur-PK)",
                   direction="rtl", latin_script=False, fonts=_URDU,
                   idml_font="Noto Sans Arabic"),
}

DEFAULT = "es"


def get(code: str | None) -> Language:
    """Resolve a language code, falling back to the configured default."""
    code = (code or os.environ.get("BABEL_TARGET_LANG") or DEFAULT).lower().strip()
    code = code.split("-")[0]  # accept "es-419", "pt-BR"
    if code not in LANGUAGES:
        raise ValueError(
            f"unsupported target language {code!r}; choose one of "
            + ", ".join(sorted(LANGUAGES))
        )
    return LANGUAGES[code]


def listing() -> list[dict]:
    """UI-facing catalogue: code, name, reading direction.

    `direction` is what the review UI needs to set `dir` on the target pane;
    without it the caret jumps and trailing punctuation drifts to the wrong end
    while editing, which reviewers report as a translation bug.

    Every registered language is renderable — the PDF path shapes and reorders
    RTL text itself, so the old "use the IDML path instead" note is gone.
    """
    return [
        {
            "code": lang.code,
            "name": lang.name,
            "direction": lang.direction,
            "supported": True,
            "note": (
                "set in Naskh, not the expected Nastaliq — the PDF renderer "
                "draws Nastaliq faces blank; legible but the wrong style"
                if lang.code == "ur" else ""
            ),
        }
        for lang in sorted(LANGUAGES.values(), key=lambda x: x.name)
    ]
