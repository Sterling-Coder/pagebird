"""Which script a piece of text is written in, and which way it reads.

Format-agnostic on purpose: the IDML path asks these questions to decide
whether a run needs the target language's face and whether it must be pinned
left-to-right inside a right-to-left paragraph, and the PDF path can ask the
same questions of a line.

The questions are deliberately about the *text*, not about the job's target
language. A translated document is never wholly one script: an Arabic lesson
still carries `10x + 15y = 150`, a URL, a variable name and a page number, and
every one of those has to keep the font and the reading order it had. Deciding
per run is what keeps them.
"""

from __future__ import annotations

# Every block whose letters read right-to-left. Hebrew, Arabic, Syriac, Thaana,
# NKo, Samaritan, Mandaic, Arabic Extended-A, the Hebrew and Arabic
# presentation forms, and the historical RTL planes.
_RTL_RANGES = (
    (0x0590, 0x05FF), (0x0600, 0x06FF), (0x0700, 0x074F), (0x0750, 0x077F),
    (0x07C0, 0x07FF), (0x0800, 0x083F), (0x0840, 0x085F), (0x08A0, 0x08FF),
    (0xFB1D, 0xFB4F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF),
    (0x10800, 0x10FFF), (0x1E800, 0x1EFFF),
)

# Every block a Latin face is expected to carry: ASCII and Latin-1 letters,
# Latin Extended-A/B, IPA, Latin Extended Additional and the later Latin
# extensions, plus the "ﬁ"/"ﬂ" ligatures.
_LATIN_RANGES = (
    (0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x024F), (0x0250, 0x02AF),
    (0x1E00, 0x1EFF), (0x2C60, 0x2C7F), (0xA720, 0xA7FF), (0xAB30, 0xAB6F),
    (0xFB00, 0xFB06),
)


def _in(ranges, code: int) -> bool:
    return any(lo <= code <= hi for lo, hi in ranges)


def is_rtl_char(ch: str) -> bool:
    """True for a letter that reads right-to-left."""
    return _in(_RTL_RANGES, ord(ch))


def is_latin_letter(ch: str) -> bool:
    """True for a letter any Latin text face is expected to carry."""
    return ch.isalpha() and _in(_LATIN_RANGES, ord(ch))


def contains_rtl(text: str) -> bool:
    """True when any character reads right-to-left."""
    return any(is_rtl_char(c) for c in text or "")


def contains_non_latin_letters(text: str) -> bool:
    """True when the text has a letter a Latin face cannot be assumed to carry.

    This is the question that decides a font substitution. A Latin face renders
    Latin letters, digits and punctuation perfectly well, so a run that holds
    only those keeps the face the designer chose; a run holding Arabic, Han,
    Devanagari or Hangul needs the target language's face or it prints as
    missing-glyph boxes.
    """
    return any(c.isalpha() and not is_latin_letter(c) for c in text or "")


def is_ltr_only(text: str) -> bool:
    """True for text that reads left-to-right and holds nothing that does not.

    Numbers, equations, URLs, variable names, file names: the content that has
    to keep its order inside a right-to-left paragraph. Text with no strong
    character either way -- a lone bullet, a space, a slash -- is *not*
    ltr-only, because it takes its direction from its surroundings and pinning
    it would break the surrounding line rather than protect it.
    """
    text = text or ""
    if contains_rtl(text):
        return False
    return any(c.isalpha() or c.isdigit() for c in text)


def detect_language_direction(text: str) -> str:
    """`"rtl"`, `"ltr"` or `"neutral"` for a piece of text.

    `neutral` is a real answer, not a failure: a run of punctuation or spaces
    has no direction of its own and must inherit one, so a caller that forced
    it either way would be inventing a decision the text does not carry.
    """
    if contains_rtl(text):
        return "rtl"
    if is_ltr_only(text):
        return "ltr"
    return "neutral"


# Every character a mathematical expression is allowed to be written with,
# beyond digits and whitespace. Split in two because the two sets answer
# different questions.
#
# `_MATH_OPERATORS` is the whole vocabulary an expression may use, negative
# signs, slashes and decimal separators included. `_MATH_SIGNALS` is the
# narrower set that is *evidence* an expression is there at all: a relation or
# a binary arithmetic operator. The hyphen and the slash are deliberately not
# signals -- a hyphen is how English writes a compound word and a date, a
# slash is how it writes a path -- so they may appear in an expression but may
# never be the only reason something is read as one.
_MATH_SIGNALS = "=≠<>≤≥≈+×✕⋅·÷∙*±"
_MATH_OPERATORS = _MATH_SIGNALS + "/–—−-"
# Brackets, separators, and the marks that carry an exponent, a subscript, a
# degree, a percentage, a factorial or a price -- all of which appear in these
# books' arithmetic. `_` is here because a fill-in-the-blank is drawn as a run
# of them, and a blank is part of the expression it sits in.
_MATH_PUNCTUATION = "()[]{}.,:;'\"^_|°%!$"
# Two or more of these in a row is an answer blank -- "____", "-----" -- which
# is evidence of an expression the same way a digit is.
_BLANK_CHARS = "_–—-"


def _is_math_char(ch: str) -> bool:
    if ch.isspace() or ch.isnumeric():
        return True
    if ch in _MATH_OPERATORS or ch in _MATH_PUNCTUATION:
        return True
    # A single letter is a variable ("x", "n"); a run of them is a word, which
    # `is_math_expression` rejects separately -- this only says the character
    # itself is one an expression may contain.
    return is_latin_letter(ch)


def _has_blank(text: str) -> bool:
    run = 0
    for ch in text:
        run = run + 1 if ch in _BLANK_CHARS else 0
        if run >= 2:
            return True
    return False


def contains_math_operator(text: str) -> bool:
    """True when the text carries a relation or a binary arithmetic operator.

    The evidence test, not the membership test: `is_math_expression` says a
    piece of text *could* be part of an expression, and this says something
    in it could only be one. `"12"` passes the first and fails this.
    """
    return any(c in _MATH_SIGNALS for c in text or "")


def is_math_expression(text: str) -> bool:
    """True for text that is a mathematical expression and nothing else.

    `"3"`, `"·"`, `"= 12"`, `"-8"`, `"____"`, `"2(x + 3) = 10"`, `"3/4"`: the
    pieces a designer sets in separate frames to build an equation on a page,
    each of which has to keep the place it was drawn in when the page turns
    round. Prose fails, in any script -- one Latin word of two letters or more
    is enough, and so is a single right-to-left letter -- and so does text
    with no mathematical content at all: a lone `"."` or `"("` has no order of
    its own to protect and would only let two unrelated things chain together.

    Deliberately stricter than `is_ltr_only`, which this does not replace:
    that question is about one run of text inside a paragraph and is answered
    for a URL and a file name too, both of which are prose furniture rather
    than mathematics.
    """
    text = (text or "").strip()
    if not text or contains_rtl(text):
        return False
    letters = 0
    for ch in text:
        if not _is_math_char(ch):
            return False
        if is_latin_letter(ch):
            letters += 1
            if letters >= 2:
                # Two letters running is a word, not a variable -- "cm",
                # "or", "Add". Two variables in one expression are fine:
                # something separates them ("x + y", "a · b"), which resets
                # the count below.
                return False
        else:
            letters = 0
    return (any(c.isnumeric() for c in text)
            or any(c in _MATH_OPERATORS for c in text)
            or _has_blank(text)
            or any(is_latin_letter(c) for c in text))
