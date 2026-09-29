"""Which script a piece of text is in, and which way it reads.

The questions that decide two things elsewhere: whether a run needs the target
language's face (`idml.package.apply`) and whether it has to be pinned
left-to-right inside an Arabic paragraph (`idml.rtl.preserve_ltr_content`).
"""

from pagebirdy import script

ARABIC = "الرياضيات"
HEBREW = "מתמטיקה"
CHINESE = "理解比率"
HINDI = "गणित"


def test_arabic_reads_right_to_left():
    assert script.detect_language_direction(ARABIC) == "rtl"


def test_hebrew_reads_right_to_left():
    assert script.detect_language_direction(HEBREW) == "rtl"


def test_english_reads_left_to_right():
    assert script.detect_language_direction("Understanding Ratios") == "ltr"


def test_an_equation_reads_left_to_right():
    assert script.detect_language_direction("10x + 15y = 150") == "ltr"


def test_a_url_reads_left_to_right():
    assert script.detect_language_direction("https://example.org/a") == "ltr"


def test_punctuation_alone_has_no_direction():
    """A slash or a space takes its direction from its neighbours.

    Pinning it either way would decide for the line around it rather than for
    itself, which is how a fraction bar ends up on the wrong side.
    """
    assert script.detect_language_direction(" / ") == "neutral"
    assert script.detect_language_direction("​") == "neutral"


def test_mixed_arabic_and_latin_reads_right_to_left():
    """One Arabic letter is enough: the run has to inherit the paragraph and be
    placed by bidi, not pinned."""
    assert script.detect_language_direction(f"{ARABIC} 10x") == "rtl"
    assert not script.is_ltr_only(f"{ARABIC} 10x")


# ---- what needs the target language's face ---------------------------------


def test_arabic_needs_a_non_latin_face():
    assert script.contains_non_latin_letters(ARABIC)


def test_chinese_needs_a_non_latin_face():
    assert script.contains_non_latin_letters(CHINESE)


def test_devanagari_needs_a_non_latin_face():
    assert script.contains_non_latin_letters(HINDI)


def test_plain_english_does_not_need_a_non_latin_face():
    assert not script.contains_non_latin_letters("Understanding Ratios")


def test_accented_latin_does_not_need_a_non_latin_face():
    """Spanish, French and Vietnamese stay in the designer's face."""
    assert not script.contains_non_latin_letters("Comprender las razones")
    assert not script.contains_non_latin_letters("Chia 3 cho 4 — nửa")


def test_digits_and_symbols_do_not_need_a_non_latin_face():
    """The fraction furniture between two math-font runs — the exact 322 runs
    that were being retyped in the grade-8 sample."""
    for text in ("5", "/", "​", "10x + 15y = 150", "(4)"):
        assert not script.contains_non_latin_letters(text), text
