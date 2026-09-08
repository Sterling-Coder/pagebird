"""The language catalogue the UI builds its picker from."""

from babel import languages


def test_listing_exposes_direction_for_each_language():
    by_code = {e["code"]: e for e in languages.listing()}
    assert by_code["ar"]["direction"] == "rtl"
    assert by_code["he"]["direction"] == "rtl"
    assert by_code["es"]["direction"] == "ltr"


def test_rtl_languages_are_no_longer_advertised_as_unsupported():
    """The PDF path renders RTL now, so the old refusal note must be gone."""
    rtl = [e for e in languages.listing() if e["direction"] == "rtl"]
    assert rtl
    assert all(e["supported"] for e in rtl)
    assert all("IDML" not in e["note"] for e in rtl)


def test_every_requested_target_is_offered():
    codes = {e["code"] for e in languages.listing()}
    assert {"es", "fr", "de", "it", "pt", "zh", "ja", "ko"} <= codes  # LTR
    assert {"ar", "he", "fa", "ur"} <= codes                          # RTL
