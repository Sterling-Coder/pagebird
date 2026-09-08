import fitz

from babel.models import Segment
from babel.reassemble.pdf import (
    _border_average_color,
    _image_shadowed_duplicates,
    _rows,
    rebuild_pdf,
)


def _make_pdf(path, text="Write the missing digits"):
    doc = fitz.open()
    page = doc.new_page(width=300, height=100)
    page.insert_text((20, 40), text, fontsize=11, fontname="helv")
    doc.save(path)
    doc.close()
    return (20, 30, 20 + fitz.get_text_length(text, fontsize=11) + 5, 44)


def test_prose_line_is_replaced_with_spanish(tmp_path):
    src = str(tmp_path / "in.pdf")
    bbox = _make_pdf(src)
    s = Segment(id="p0-l0", page=0, bbox=bbox, font="helv", size=11, color=0,
                source="Write the missing digits",
                target="Escribe los dígitos que faltan", status="translated")
    out = str(tmp_path / "out.pdf")
    outcomes = rebuild_pdf(src, [s], out)

    assert any(o.action in ("replaced", "overflow") for o in outcomes)
    doc = fitz.open(out)
    page_text = doc.load_page(0).get_text().replace("\xa0", " ")
    doc.close()
    assert "Escribe los dígitos" in page_text
    assert "Write the missing" not in page_text  # original was redacted


def test_ocr_image_text_is_blanked_and_translation_drawn_over_it(tmp_path):
    """Text baked into a raster image (a banner, e.g. "GO!") has no real PDF
    glyphs to redact — the original pixels must still be masked before the
    translation is drawn, or the English shows through underneath.

    A same-color cover over the banner's own background is, by design,
    indistinguishable from the untouched original at any point that isn't
    part of a former glyph stroke — so the fake "burned-in text" patch here
    uses a color distinct from the banner fill, the same way real burned-in
    English glyphs (a different color from their background) would."""
    src = str(tmp_path / "in.pdf")
    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    banner = fitz.Rect(20, 20, 120, 70)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 50))
    pix.set_rect(pix.irect, (200, 50, 150))  # distinct color stands in for the banner art
    # a lighter patch standing in for burned-in white "GO!" glyphs
    pix.set_rect(fitz.IRect(20, 15, 70, 35), (240, 240, 240))
    page.insert_image(banner, pixmap=pix)
    doc.save(src)
    doc.close()

    s = Segment(id="p0-ocr0", page=0, bbox=tuple(banner), font="helv", size=20,
                color=0, source="GO!", target="VAMOS!", status="translated",
                from_ocr=True, in_image=True)
    out = str(tmp_path / "out.pdf")
    outcomes = rebuild_pdf(src, [s], out)

    assert any(o.action in ("replaced", "overflow") for o in outcomes)
    result = fitz.open(out)
    page_out = result.load_page(0)
    # the fake "burned-in text" patch's own distinct color must be gone —
    # sampled where no drawn translation glyph would plausibly land
    patch_spot = page_out.get_pixmap(dpi=72).pixel(25, 22)
    assert patch_spot != (240, 240, 240)
    assert "VAMOS" in page_out.get_text()
    result.close()


def _img_seg(sid, bbox, **kw):
    base = dict(id=sid, page=0, bbox=bbox, font="helv", size=11, color=0,
                source="GO!", target="VAMOS!", status="translated",
                from_ocr=True, in_image=True)
    base.update(kw)
    return Segment(**base)


def _text_seg(sid, bbox, **kw):
    base = dict(id=sid, page=0, bbox=bbox, font="helv", size=11, color=0,
                source="Go", target="ir", status="translated")
    base.update(kw)
    return Segment(**base)


def test_image_shadowed_duplicates_suppresses_overlapping_real_text():
    image_seg = _img_seg("img", (100, 100, 160, 130))
    real_text_seg = _text_seg("real", (98, 102, 155, 128))  # closely overlaps
    hidden = _image_shadowed_duplicates([image_seg, real_text_seg])
    assert hidden == {"real"}


def test_image_shadowed_duplicates_ignores_non_overlapping_text():
    image_seg = _img_seg("img", (100, 100, 160, 130))
    unrelated_seg = _text_seg("elsewhere", (0, 0, 20, 20))
    hidden = _image_shadowed_duplicates([image_seg, unrelated_seg])
    assert hidden == set()


def test_image_shadowed_duplicates_never_suppresses_image_segments():
    image_a = _img_seg("img-a", (100, 100, 160, 130))
    image_b = _img_seg("img-b", (98, 102, 155, 128))  # overlaps image_a heavily
    hidden = _image_shadowed_duplicates([image_a, image_b])
    assert hidden == set()  # only ordinary segments get suppressed, never in_image ones


def test_ocr_banner_overlap_with_hidden_real_text_suppresses_the_real_text(tmp_path):
    """The banner's raster image can sit on top of an ordinary (invisible,
    by virtue of z-order) PDF text run for the same word. Once OCR-based
    redaction blanks the image, that previously-hidden text would surface
    and overlap the OCR-recovered translation unless it's suppressed."""
    src = str(tmp_path / "in.pdf")
    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    banner = fitz.Rect(20, 20, 120, 70)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 50))
    pix.set_rect(pix.irect, (200, 50, 150))
    # a real (would-be-invisible-under-the-image) text run at roughly the same spot
    page.insert_text((30, 55), "Go", fontsize=14, fontname="helv")
    page.insert_image(banner, pixmap=pix)  # drawn after the text -> covers it
    doc.save(src)
    doc.close()

    image_seg = Segment(id="p0-ocr0", page=0, bbox=tuple(banner), font="helv", size=20,
                        color=0, source="GO!", target="VAMOS!", status="translated",
                        from_ocr=True, in_image=True)
    real_seg = Segment(id="p0-l0", page=0, bbox=(30, 45, 55, 65), font="helv", size=14,
                       color=0, source="Go", target="ir", status="translated")
    out = str(tmp_path / "out.pdf")
    rebuild_pdf(src, [image_seg, real_seg], out)

    result = fitz.open(out)
    page_text = result.load_page(0).get_text()
    result.close()
    assert "VAMOS" in page_text
    assert "ir" not in page_text.split()  # the shadowed duplicate's own translation never drew


def test_border_average_color_reads_the_banner_fill():
    doc = fitz.open()
    page = doc.new_page(width=100, height=100)
    page.draw_rect(fitz.Rect(0, 0, 100, 100), color=None, fill=(0.6, 0.1, 0.6))
    color = _border_average_color(page, fitz.Rect(10, 10, 90, 90))
    r, g, b = (color >> 16 & 255), (color >> 8 & 255), (color & 255)
    assert abs(r - 153) < 15 and abs(g - 26) < 15 and abs(b - 153) < 15


def test_in_image_segment_gets_an_opaque_cover_before_the_translation_draws(tmp_path):
    """Some images (soft-masked, common for rounded-corner/drop-shadow
    graphics) are not actually cleared by `apply_redactions()` even though it
    reports success — a real bug hit on a production PDF. `in_image`
    segments therefore cannot rely on redaction alone to hide the original;
    they must get an explicit opaque cover drawn first. Verify the mechanism
    fires directly (recording `draw_rect` calls) rather than via pixel
    color, since a same-color cover is intentionally near-invisible against
    the original — a color-diff assertion can't reliably tell them apart."""
    src = str(tmp_path / "in.pdf")
    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    banner = fitz.Rect(20, 20, 120, 70)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 50))
    pix.set_rect(pix.irect, (200, 50, 150))
    page.insert_image(banner, pixmap=pix)
    doc.save(src)
    doc.close()

    calls = []
    real_draw_rect = fitz.Page.draw_rect

    def recording_draw_rect(self, rect, **kw):
        calls.append((fitz.Rect(rect), kw.get("fill")))
        return real_draw_rect(self, rect, **kw)

    original = fitz.Page.draw_rect
    fitz.Page.draw_rect = recording_draw_rect
    try:
        s = Segment(id="p0-ocr0", page=0, bbox=tuple(banner), font="helv", size=20,
                    color=0, source="GO!", target="VAMOS!", status="translated",
                    from_ocr=True, in_image=True)
        out = str(tmp_path / "out.pdf")
        rebuild_pdf(src, [s], out)
    finally:
        fitz.Page.draw_rect = original

    covers = [(rect, fill) for rect, fill in calls if rect.contains(fitz.Rect(banner)) or rect == fitz.Rect(banner)]
    assert covers, f"expected an opaque cover rect for the in_image segment, got calls={calls}"
    assert covers[0][1] is not None  # filled, not just an outline


def test_math_line_is_left_untouched(tmp_path):
    src = str(tmp_path / "in.pdf")
    bbox = _make_pdf(src, "3 divided by 4")
    s = Segment(id="p0-l0", page=0, bbox=bbox, font="helv", size=11, color=0,
                source="⟦m0⟧ divided by ⟦m1⟧", target="⟦m0⟧ dividido entre ⟦m1⟧",
                placeholders={"⟦m0⟧": "3", "⟦m1⟧": "4"}, has_math_font=True,
                status="translated")
    out = str(tmp_path / "out.pdf")
    outcomes = rebuild_pdf(src, [s], out)
    assert outcomes and outcomes[0].action == "skipped_math"
    doc = fitz.open(out)
    page_text = doc.load_page(0).get_text()
    doc.close()
    assert "3 divided by 4" in page_text  # untouched, math not corrupted


def _seg(**kw):
    base = dict(id="s", page=0, bbox=(0, 0, 100, 14), font="helv", size=11,
                color=0, source="x", target="y", status="translated")
    base.update(kw)
    return Segment(**base)


def test_side_by_side_fragments_count_as_one_line():
    # A TOC row "12 | Understanding … | 18": three PyMuPDF "lines", one baseline.
    s = _seg(bbox=(20, 100, 300, 114),
             bboxes=[(20, 100, 30, 114), (50, 100, 250, 114), (280, 100, 300, 114)])
    assert len(_rows(s)) == 1


def test_two_line_cell_with_centred_neighbour_counts_as_two():
    # The "12" cell is vertically centred and so overlaps BOTH title lines.
    s = _seg(bbox=(20, 100, 300, 128),
             bboxes=[(50, 100, 250, 114), (20, 107, 30, 121), (50, 114, 200, 128)])
    assert len(_rows(s)) == 2


def _rendered(path):
    doc = fitz.open(path)
    spans = [sp for b in doc.load_page(0).get_text("dict")["blocks"]
             for ln in b["lines"] for sp in ln["spans"]]
    doc.close()
    return spans


def test_target_keeps_the_source_line_count(tmp_path):
    # Spanish is much longer, and there is empty page below, but a one-line
    # source stays one line: growing the block would change the page's shape.
    src = str(tmp_path / "in.pdf")
    bbox = _make_pdf(src)
    s = Segment(id="p0-l0", page=0, bbox=bbox, font="helv", size=11, color=0,
                bboxes=[bbox], source="Write the missing digits",
                target="Escribe los dígitos que faltan en todos los recuadros",
                status="translated")
    out = str(tmp_path / "out.pdf")
    assert rebuild_pdf(src, [s], out)[0].action == "replaced"

    doc = fitz.open(out)
    lines = doc.load_page(0).get_text("dict")["blocks"][0]["lines"]
    doc.close()
    assert len(lines) == 1


def test_shrinks_when_the_block_below_leaves_no_room(tmp_path):
    # Same text, but a neighbour sits immediately underneath. Growing would
    # collide, so the size gives way and the source's line count is held.
    src = str(tmp_path / "in.pdf")
    bbox = _make_pdf(src)
    below = (bbox[0], bbox[3] + 2, bbox[2], bbox[3] + 16)
    s = Segment(id="p0-l0", page=0, bbox=bbox, font="helv", size=11, color=0,
                bboxes=[bbox], source="Write the missing digits",
                target="Escribe los dígitos que faltan en todos los recuadros",
                status="translated")
    neighbour = Segment(id="p0-l1", page=0, bbox=below, font="helv", size=11,
                        color=0, bboxes=[below], source="x", target="x",
                        status="translated")
    out = str(tmp_path / "out.pdf")
    rebuild_pdf(src, [s, neighbour], out)
    placed = [sp for sp in _rendered(out) if "Escribe" in sp["text"]]
    assert placed and all(sp["size"] < 11 for sp in placed)


def test_unrenderable_characters_fall_back_to_plain_equivalents():
    """A character the face lacks prints as an empty box.

    The text layer still reads correctly, so it survives every text-level check
    and shows up only on the page. Two real cases: U+2011 non-breaking hyphen
    missing from Nirmala on a Hindi page, U+2212 minus sign missing from Malgun
    Gothic in Korean maths worksheets.
    """
    import os

    from babel.reassemble.pdf import _drawable, _font

    for path in ("C:/Windows/Fonts/Nirmala.ttf", "C:/Windows/Fonts/malgun.ttf"):
        if not os.path.exists(path):
            continue
        font = _font(path)
        if not font.has_glyph(0x2011):
            assert _drawable("One‑Variable", font) == "One-Variable"
        if not font.has_glyph(0x2212):
            assert _drawable("3 − 2", font) == "3 - 2"


def test_characters_the_font_can_draw_are_left_alone():
    """The substitution is font coverage, not a blanket rewrite: a face that
    carries the real dash keeps it rather than being flattened to ASCII."""
    import os

    from babel.reassemble.pdf import _drawable, _font

    path = "C:/Windows/Fonts/arial.ttf"
    if not os.path.exists(path):
        return
    font = _font(path)
    for text in ("a – b", "“quoted”", "wait…"):
        if all(font.has_glyph(ord(c)) for c in text):
            assert _drawable(text, font) == text
