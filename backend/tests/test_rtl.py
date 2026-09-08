"""Right-to-left rendering in the draft PDF path.

Assertions deliberately avoid comparing extracted text to the source string:
MuPDF writes RTL runs as Arabic Presentation Forms in *visual* order, so
`get_text()` returns neither the original codepoints nor a simple reversal of
them. What is stable — and what actually matters — is that the glyphs come out
shaped, that digit runs keep their reading order, and that the block sits against
the correct edge of its box.
"""

import fitz
import pytest

from babel.models import Segment
from babel.reassemble.pdf import rebuild_pdf

# "page 12 of 25" / "shalom olam 12"
AR = "الصفحة 12 من 25"
HE = "שלום עולם 12"

# A box symmetric about the page centre, so mirroring leaves it in place and
# these assertions stay true once the mirror stage is wired in.
PAGE_W, BOX = 400, (50, 30, 350, 44)


def _source_pdf(path, text="Write the missing digits"):
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=100)
    page.insert_text((BOX[0], 40), text, fontsize=11, fontname="helv")
    doc.save(path)
    doc.close()


def _render(tmp_path, target, lang, source="Write the missing digits"):
    src = str(tmp_path / "in.pdf")
    _source_pdf(src, source)
    seg = Segment(id="p0-l0", page=0, bbox=BOX, bboxes=[BOX], font="helv",
                  size=11, color=0, source=source, target=target,
                  status="translated")
    out = str(tmp_path / "out.pdf")
    outcomes = rebuild_pdf(src, [seg], out, target_lang=lang)
    doc = fitz.open(out)
    page = doc.load_page(0)
    spans = [sp for b in page.get_text("dict")["blocks"]
             for ln in b["lines"] for sp in ln["spans"]]
    text = page.get_text()
    doc.close()
    return outcomes, text, spans


def _is_shaped(text):
    """Arabic Presentation Forms A/B — present only if the run was shaped."""
    return any(0xFB50 <= ord(c) <= 0xFEFF for c in text)


def test_arabic_renders_without_refusing(tmp_path):
    outcomes, _, _ = _render(tmp_path, AR, "ar")
    assert outcomes and outcomes[0].action in ("replaced", "overflow")


def test_arabic_is_shaped_into_presentation_forms(tmp_path):
    _, text, _ = _render(tmp_path, AR, "ar")
    assert _is_shaped(text), f"unshaped output: {text!r}"


def test_digit_runs_keep_their_reading_order(tmp_path):
    """The bidi regression that would otherwise ship silently."""
    _, text, _ = _render(tmp_path, AR, "ar")
    assert "12" in text and "25" in text
    assert "21" not in text and "52" not in text


def test_hebrew_digits_render_despite_the_face_having_none(tmp_path):
    """Noto Sans Hebrew carries no digits, so the glyphs must come from elsewhere.

    Asserting only `"12" in text` would be too weak: extraction reads the
    ToUnicode map, so a character can be reported even when it drew as an empty
    box. A missing glyph shows up as NUL, which is what this really guards.
    """
    _, text, _ = _render(tmp_path, HE, "he")
    assert "12" in text
    assert "\x00" not in text


def test_rtl_block_is_set_flush_right(tmp_path):
    _, _, spans = _render(tmp_path, AR, "ar")
    assert spans
    assert max(sp["bbox"][2] for sp in spans) == pytest.approx(BOX[2], abs=3)


def test_ltr_block_is_still_set_flush_left(tmp_path):
    _, _, spans = _render(tmp_path, "Escribe los dígitos", "es")
    assert spans
    assert min(sp["bbox"][0] for sp in spans) == pytest.approx(BOX[0], abs=3)


# --- full page mirror --------------------------------------------------------

OFFSET_BOX = (20, 30, 150, 44)  # hugs the left margin, so mirroring must move it


def _render_at(tmp_path, box, target, lang):
    src = str(tmp_path / "in.pdf")
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=100)
    page.insert_text((box[0], 40), "Write the missing digits",
                     fontsize=11, fontname="helv")
    doc.save(src)
    doc.close()

    seg = Segment(id="p0-l0", page=0, bbox=box, bboxes=[box], font="helv",
                  size=11, color=0, source="Write the missing digits",
                  target=target, status="translated")
    out = str(tmp_path / "out.pdf")
    rebuild_pdf(src, [seg], out, target_lang=lang)
    doc = fitz.open(out)
    spans = [sp for b in doc.load_page(0).get_text("dict")["blocks"]
             for ln in b["lines"] for sp in ln["spans"]]
    doc.close()
    return spans


def test_rtl_moves_a_left_margin_block_to_the_right_margin(tmp_path):
    """Full page mirror: what sat against the left margin belongs at the right."""
    spans = _render_at(tmp_path, OFFSET_BOX, AR, "ar")
    assert spans
    mirrored_x1 = PAGE_W - OFFSET_BOX[0]          # 380
    assert max(sp["bbox"][2] for sp in spans) == pytest.approx(mirrored_x1, abs=4)


def test_ltr_leaves_a_left_margin_block_where_it_was(tmp_path):
    spans = _render_at(tmp_path, OFFSET_BOX, "Escribe los dígitos", "es")
    assert spans
    assert min(sp["bbox"][0] for sp in spans) == pytest.approx(OFFSET_BOX[0], abs=4)


def test_urdu_letters_actually_put_ink_on_the_page(tmp_path):
    """Noto Nastaliq Urdu resolves fine and reports a glyph id for every Urdu
    letter, yet MuPDF draws nothing for them: Nastaliq composes almost the whole
    script through GSUB substitution and its base glyphs are empty, so an
    unshaped draw yields blanks. Only the digits survived, which no assertion
    about fonts resolving or text extracting would have caught — both passed
    while the page came out empty. Hence: count the ink.
    """
    urdu_words = "صفحہ میں سے"  # no digits
    src = str(tmp_path / "in.pdf")
    _source_pdf(src, "Page in")
    seg = Segment(id="p0-l0", page=0, bbox=BOX, bboxes=[BOX], font="helv",
                  size=14, color=0, source="Page in", target=urdu_words,
                  status="translated")
    out = str(tmp_path / "out.pdf")
    rebuild_pdf(src, [seg], out, target_lang="ur")

    doc = fitz.open(out)
    pix = doc.load_page(0).get_pixmap(dpi=150, colorspace=fitz.csGRAY)
    doc.close()
    inked = sum(1 for x in range(pix.width)
                if any(pix.pixel(x, y)[0] < 200 for y in range(pix.height)))
    assert inked > 40, f"Urdu drew almost nothing: {inked} inked columns"


def test_mixed_prose_and_math_line_is_left_untouched_in_rtl(tmp_path):
    """Setting prose and math glyphs on one RTL line needs bidi across atoms
    drawn in two different faces, which MuPDF cannot do for us — its bidi runs
    over a single appended run, and the math glyph has to keep its original
    face. Rather than approximate the ordering on a mathematics line, leave it
    in the source language and let a reviewer place it.
    """
    src = str(tmp_path / "in.pdf")
    _source_pdf(src, "3 divided by 4")
    math_box = (BOX[0], BOX[1], BOX[0] + 8, BOX[3])
    seg = Segment(id="p0-l0", page=0, bbox=BOX, bboxes=[BOX], font="helv",
                  size=11, color=0,
                  source="⟦m0⟧ divided by ⟦m1⟧", target="⟦m0⟧ مقسوم على ⟦m1⟧",
                  placeholders={"⟦m0⟧": "3", "⟦m1⟧": "4"},
                  math_boxes={"⟦m0⟧": math_box, "⟦m1⟧": math_box},
                  math_widths={"⟦m0⟧": 0.5, "⟦m1⟧": 0.5},
                  has_math_font=True, status="translated")
    out = str(tmp_path / "out.pdf")
    outcomes = rebuild_pdf(src, [seg], out, target_lang="ar")

    assert outcomes and outcomes[0].action == "skipped_math"
    doc = fitz.open(out)
    text = doc.load_page(0).get_text()
    doc.close()
    assert "3 divided by 4" in text  # untouched, not half-translated


def test_rotated_axis_label_is_drawn_right_to_left(tmp_path):
    """A vertical label goes through _place_rotated, which had its own drawing
    call. Hebrew is the probe: its face carries no digits, so only the
    TextWriter path (which falls back per glyph) can render "12" at all —
    insert_text writes NUL. That makes NUL an exact detector for the line
    having been drawn without bidi.
    """
    src = str(tmp_path / "in.pdf")
    box = (40, 20, 58, 90)  # tall and narrow: a turned axis label
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=100)
    page.insert_text((box[0], 80), "Number of pets", fontsize=9,
                     fontname="helv", rotate=90)
    doc.save(src)
    doc.close()

    seg = Segment(id="p0-l0", page=0, bbox=box, bboxes=[box], font="helv",
                  size=9, color=0, rotation=90, source="Number of pets",
                  target=HE, status="translated")
    out = str(tmp_path / "out.pdf")
    rebuild_pdf(src, [seg], out, target_lang="he")

    doc = fitz.open(out)
    text = doc.load_page(0).get_text()
    doc.close()
    assert "\x00" not in text, f"rotated label drawn without bidi: {text!r}"
    assert "12" in text
