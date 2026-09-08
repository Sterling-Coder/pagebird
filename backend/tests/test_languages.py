"""Target-language registry: direction is independent of line-break behaviour."""

import pytest

from babel import languages


def test_arabic_is_rtl_and_wraps_at_spaces():
    """Direction and wrapping are orthogonal.

    Arabic runs right-to-left *and* breaks lines at spaces. The old registry
    stored "rtl" as a `wrapping` mode, which made those two facts mutually
    exclusive and left RTL nowhere to live except as a refusal.
    """
    ar = languages.get("ar")
    assert ar.direction == "rtl"
    assert ar.wrapping == "space"


@pytest.mark.parametrize("code,name", [
    ("he", "Hebrew"), ("fa", "Persian"), ("ur", "Urdu"),
])
def test_rtl_languages_are_registered(code, name):
    lang = languages.get(code)
    assert lang.name == name
    assert lang.direction == "rtl"


@pytest.mark.parametrize("code", ["zh", "ja"])
def test_cjk_wraps_between_characters_but_runs_ltr(code):
    lang = languages.get(code)
    assert lang.wrapping == "char"
    assert lang.direction == "ltr"


def test_no_language_uses_rtl_as_a_wrapping_mode():
    """`wrapping` is now strictly about where lines break."""
    assert {l.wrapping for l in languages.LANGUAGES.values()} == {"space", "char"}


def test_every_language_declares_a_valid_direction():
    assert all(l.direction in ("ltr", "rtl") for l in languages.LANGUAGES.values())
