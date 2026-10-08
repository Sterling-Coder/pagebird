"""Setting, fitting and RTL drawing of translated text."""

import fitz
import numpy as np
import pytest

from pagebirdy import languages
from pagebirdy.image import rtl
from pagebirdy.image.fit import fit_text
from pagebirdy.image.render import Style, _archive, _html, coverage, font_set, layout
from pagebirdy.models import Segment


def _style(code, align="left", bold=False):
    lang = languages.get(code)
    return Style(font_set(lang), bold, align, rtl.direction(lang))


def _glyphs(text, style, w=400, h=60, px=20):
    """(char, x) for every glyph MuPDF set, in the order it reports them."""
    doc = fitz.open()
    page = doc.new_page(width=w, height=h)
    body, css = _html(text, style, px, 1.2)
    page.insert_htmlbox(fitz.Rect(0, 0, w, h), body, css=css, archive=_archive(style.fonts)[0])
    out = [(c["c"], c["origin"][0]) for b in page.get_text("rawdict")["blocks"]
           for ln in b["lines"] for s in ln["spans"] for c in s["chars"]]
    doc.close()
    return out


def test_text_that_fits_at_source_size_keeps_it():
    fit = fit_text("Willkommen", 200, 40, _style("de"), 24.0)
    assert (fit.font_px, fit.shrunk, fit.forced) == (24.0, False, False)


def test_longer_translation_wraps_before_it_shrinks():
    # Two lines of room: wrapping at the source size beats shrinking.
    fit = fit_text("Willkommen in unserem Geschäft", 200, 70, _style("de"), 24.0)
    assert fit.font_px == 24.0 and not fit.forced


def test_much_longer_translation_shrinks_but_never_leaves_the_box():
    text = "Herzlich willkommen in unserem wunderschönen neuen Geschäft"
    fit = fit_text(text, 160, 30, _style("de"), 24.0)
    assert fit.shrunk
    assert layout(text, 160, 30, _style("de"), fit.font_px, fit.line_height, force=fit.forced).fits


def test_an_unbreakable_word_wider_than_the_box_does_not_count_as_fitting():
    assert not layout("Donaudampfschifffahrt", 60, 40, _style("de"), 20, 1.2).fits


def test_coverage_mask_is_exactly_the_box_size_and_has_ink():
    m = coverage("Bonjour", 120, 30, _style("fr"), 18, 1.2)
    assert m.shape == (30, 120)
    assert m.max() > 0.9


def test_arabic_is_shaped_and_drawn_right_to_left_not_reversed_by_hand():
    word = "مرحبا"  # ends in alef
    glyphs = [(c, x) for c, x in _glyphs(word, _style("ar", "right")) if c.strip()]
    xs = {c: x for c, x in glyphs}
    # MuPDF reports the glyphs it actually set. The alef is the *last* letter
    # in logical order, so it must be the leftmost glyph, and it must be in its
    # joined final form (U+FE8E), which only shaping produces.
    assert "ﺎ" in xs
    assert xs["ﺎ"] == min(x for _, x in glyphs)


def test_arabic_letters_join():
    style = _style("ar")
    joined = coverage("مرحبا", 200, 50, style, 30, 1.2)
    isolated = coverage(" ".join("مرحبا"), 200, 50, style, 30, 1.2)
    # Shaped text is one connected word, narrower than its letters set apart.
    width = lambda m: np.ptp(np.nonzero(m.max(axis=0) > 0.3)[0])  # noqa: E731
    assert width(joined) < width(isolated)


def test_numbers_and_equations_keep_their_order_inside_arabic():
    lang = languages.get("ar")
    seg = Segment(id="r1", page=0, bbox=(0, 0, 1, 1), font="", size=1, color=0,
                  source="", target="احسب ⟦=3 + 4 = 7⟧ خصم ⟦=50%⟧",
                  placeholders={"⟦=3 + 4 = 7⟧": "3 + 4 = 7", "⟦=50%⟧": "50%"})
    text = rtl.restore_target(seg, lang)
    xs = {}
    for c, x in _glyphs(text, _style("ar", "right"), w=500):
        xs.setdefault(c, []).append(x)
    assert xs["3"][0] < xs["4"][0] < xs["="][0] < xs["7"][0]  # reads 3 + 4 = 7
    assert xs["5"][0] < xs["0"][0]  # reads 50, not 05


def test_ltr_targets_are_not_touched_by_the_rtl_layer():
    seg = Segment(id="r1", page=0, bbox=(0, 0, 1, 1), font="", size=1, color=0,
                  source="", target="Résolvez ⟦=3 + 4 = 7⟧",
                  placeholders={"⟦=3 + 4 = 7⟧": "3 + 4 = 7"})
    text = rtl.restore_target(seg, languages.get("fr"))
    assert text == "Résolvez 3 + 4 = 7"
    assert rtl.alignment("left", languages.get("fr")) == "left"
    assert rtl.alignment("left", languages.get("ar")) == "right"
    assert rtl.alignment("center", languages.get("ar")) == "center"


@pytest.mark.parametrize("align,side", [("right", "right"), ("left", "left")])
def test_rtl_alignment_is_physical(align, side):
    m = coverage("مرحبا بكم", 300, 40, _style("ar", align), 20, 1.2)
    cols = np.nonzero(m.max(axis=0) > 0.3)[0]
    assert (cols.max() > 250) if side == "right" else (cols.min() < 50)


def test_latin_inside_arabic_uses_the_latin_face():
    style = _style("ar")
    body, _ = _html("زوروا www.example.com", style, 20, 1.2)
    assert '<span class="lat">www.example.com</span>' in body


@pytest.mark.parametrize("text,size", [("Welcome to our store", 34), ("Open every day", 20),
                                       ("SALE", 48), ("Fresh bread baked each morning", 16)])
@pytest.mark.parametrize("bold", [True, False])
@pytest.mark.parametrize("size_error", [0.92, 1.0, 1.08])
def test_weight_is_detected_despite_a_size_estimate_off_by_8_percent(text, size, bold, size_error):
    # Regression: on real Vision boxes the size estimate ran 8% high and an
    # ink-area test read a bold heading as regular. Stroke width does not.
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from image_fixtures import Scene, TextItem, render_scene

    from pagebirdy.image import background
    from pagebirdy.image.render import looks_bold

    img, regions = render_scene(Scene(width=700, height=200, items=[
        TextItem([text], 40, 90, size=size, bold=bold, color=(30, 30, 30))]))
    arr = np.asarray(img, dtype=np.float32)
    bx0, by0, bx1, by1 = regions[0].bbox
    est = size * size_error
    x0, y0 = int(bx0 - 0.12 * est), int(by0 - 0.22 * est)
    x1, y1 = int(bx1 + 0.12 * est) + 1, int(by1 + 0.22 * est) + 1
    rec = background.reconstruct(arr, (x0, y0, x1, y1), by1 - by0)
    stroke = background.text_style(arr[y0:y1, x0:x1], rec.patch)["stroke"]
    assert looks_bold(text, x1 - x0, y1 - y0, font_set(languages.get("fr")), est, stroke) == bold
