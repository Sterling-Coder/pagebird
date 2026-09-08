"""Font resolution: a vendored face must always beat a system one.

Missing-glyph fallback is not tested here — MuPDF handles it inside TextWriter.
See tests/test_rtl.py for the assertion that guards it.
"""

import fitz
import pytest

from babel import fonts, languages
from babel.models import Segment
from babel.reassemble.pdf import _font_for



def test_bundled_returns_a_real_path_for_a_vendored_face():
    path = fonts.bundled("NotoSansHebrew-Regular.ttf")
    assert path and path.endswith("NotoSansHebrew-Regular.ttf")
    assert fitz.Font(fontfile=path).name == "Noto Sans Hebrew Regular"


def test_bundled_returns_none_for_an_unknown_face():
    assert fonts.bundled("NoSuchFont-Regular.ttf") is None


def test_resolve_prefers_a_bundled_face_over_a_system_path():
    chosen = fonts.resolve(["C:/Windows/Fonts/arial.ttf", "NotoSansHebrew-Regular.ttf"])
    assert chosen == fonts.bundled("NotoSansHebrew-Regular.ttf")


def _seg(**kw):
    base = dict(id="s", page=0, bbox=(0, 0, 100, 14), font="", size=11,
                color=0, source="x")
    base.update(kw)
    return Segment(**base)


@pytest.mark.parametrize("code,face", [
    ("ar", "NotoNaskhArabic-Regular.ttf"),
    ("fa", "NotoNaskhArabic-Regular.ttf"),
    ("he", "NotoSansHebrew-Regular.ttf"),
    # Urdu belongs in Nastaliq, but MuPDF draws that face blank — see the note
    # in languages.py. Naskh is the wrong style and the only one that renders.
    ("ur", "NotoNaskhArabic-Regular.ttf"),
])
def test_rtl_languages_resolve_to_their_bundled_face(code, face):
    assert _font_for(_seg(), languages.get(code)) == fonts.bundled(face)


def test_bundled_face_wins_even_when_a_system_face_is_listed_first():
    """Arabic still lists Tahoma as a fallback; it must never be chosen here."""
    assert "Windows" not in (_font_for(_seg(), languages.get("ar")) or "")
