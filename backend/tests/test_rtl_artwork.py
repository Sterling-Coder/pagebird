"""Artwork and vertical fit on the RTL draft-PDF path.

Three defects observed on a real Arabic edition, each with a measured cause:

* A brand wordmark drawn as VECTOR art survives redaction untouched (measured:
  0% of its ink removed), so the translation was drawn on top of an intact
  logo — and the page mirror then reflected the logo into backwards glyphs.
* Type size was fitted on width and line count only. Noto Naskh occupies
  1.703 em vertically against Arial's 1.117, so Arabic set at the source's own
  size on the source's own baselines overlapped the line beneath it.
* An OCR read of burned-in text and the real text run underneath it are the
  same content, but a typo in the OCR ("Math on tha go") defeated the exact
  substring test that suppresses the duplicate, so both were drawn.
"""

import re

import fitz
import pytest

from babel.models import Segment
from babel.reassemble.pdf import rebuild_pdf

AR_BODY = "ابحث عن فرص لوصف أماكن الأشياء في مواقف من الحياة الواقعية"
# Long enough to fill all three of its source rows, so the block reaches the
# neighbour below it.
AR_LONG_A = ("أخبر طفلك أنك تبحث عن شيء معين واطلب منه وصف مكانه بدقة شديدة "
             "ثم تناوبا في وضع الأشياء في أماكن مختلفة حول المنزل وصفا كل موضع معا بالتفصيل")
AR_LONG_B = ("واطلب منه وصف مكانه بدقة ثم تناوبا في وضع الأشياء في أماكن مختلفة "
             "حول المنزل وصفها معا")


def _spans(path, pno=0):
    doc = fitz.open(path)
    out = [
        (fitz.Rect(s["bbox"]), s["text"])
        for b in doc.load_page(pno).get_text("dict")["blocks"]
        for line in b.get("lines", [])
        for s in line["spans"]
        if s["text"].strip()
    ]
    doc.close()
    return out


def _overlapping_pairs(path, pno=0, tolerance=0.15):
    """Span pairs sharing more than `tolerance` of the smaller one's area."""
    spans = _spans(path, pno)
    bad = []
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            a, b = spans[i][0], spans[j][0]
            smaller = min(a.get_area(), b.get_area())
            if smaller > 0 and (a & b).get_area() / smaller > tolerance:
                bad.append((spans[i][1], spans[j][1]))
    return bad


# --- vertical fit ------------------------------------------------------------


def _paragraph_pdf(path, rows=3, pitch=13.5, size=11.0):
    """An English paragraph set on `rows` baselines at a Latin line pitch."""
    doc = fitz.open()
    page = doc.new_page(width=400, height=200)
    boxes = []
    for i in range(rows):
        y = 40 + i * pitch
        page.insert_text((40, y), "Look for opportunities to describe",
                         fontsize=size, fontname="helv")
        boxes.append((40, y - size * 0.81, 300, y + size * 0.19))
    doc.save(path)
    doc.close()
    return boxes


def test_arabic_lines_do_not_overlap_each_other(tmp_path):
    """The size must respect the vertical room between baselines.

    Noto Naskh needs 1.703 em per line. Set at the source's 11pt on a 13.5pt
    pitch it occupies 18.7pt and runs 5pt into the line below, every time.
    """
    src = str(tmp_path / "in.pdf")
    boxes = _paragraph_pdf(src)
    seg = Segment(id="p0-l0", page=0, bbox=(40, 31, 300, 69), bboxes=boxes,
                  font="helv", size=11, color=0,
                  source="Look for opportunities to describe where things are",
                  target=AR_BODY, status="translated")
    out = str(tmp_path / "out.pdf")
    rebuild_pdf(src, [seg], out, target_lang="ar")

    assert _overlapping_pairs(out) == []


def test_latin_target_is_not_shrunk_by_the_vertical_rule(tmp_path):
    """Arial fits 1.117 em into the same 1.2 em pitch, so nothing should move.

    The vertical constraint must bind only where the face actually needs the
    room — a Spanish edition should be byte-for-byte what it was before.
    """
    src = str(tmp_path / "in.pdf")
    boxes = _paragraph_pdf(src)
    seg = Segment(id="p0-l0", page=0, bbox=(40, 31, 300, 69), bboxes=boxes,
                  font="helv", size=11, color=0,
                  source="Look for opportunities to describe where things are",
                  target="Busca oportunidades para describir donde estan",
                  status="translated")
    out = str(tmp_path / "out.pdf")
    outcomes = rebuild_pdf(src, [seg], out, target_lang="es")

    assert [o.action for o in outcomes] == ["replaced"]
    assert "size=11.00" in outcomes[0].detail
    assert _overlapping_pairs(out) == []


def _stacked_pdf(path):
    """Two bulleted blocks whose source boxes interleave.

    Real geometry from the document: the first block's box runs to y=218 while
    the second starts at y=217, so `_room_below` reads the second as "not below"
    the first and reports no ceiling at all. Latin absorbs that; Arabic does not.
    """
    doc = fitz.open()
    page = doc.new_page(width=400, height=320)
    first, second = [], []
    for i in range(3):  # box runs 176.7 -> 218.5
        top = 176.7 + i * 14.0
        page.insert_text((40, top + 11.2), "Tell your child you are looking",
                         fontsize=10, fontname="helv")
        first.append((40, top, 300, top + 13.8))
    for i in range(3):  # box starts at 217.1, ABOVE the first block's bottom
        top = 217.1 + i * 14.0
        page.insert_text((40, top + 11.2), "and have them describe where it is",
                         fontsize=10, fontname="helv")
        second.append((40, top, 300, top + 13.8))
    doc.save(path)
    doc.close()
    return first, second


def test_interleaved_neighbours_do_not_collide(tmp_path):
    """A block must give up type size rather than run into the one below it."""
    src = str(tmp_path / "in.pdf")
    first, second = _stacked_pdf(src)
    segs = [
        Segment(id="p0-a", page=0, bbox=(40, first[0][1], 300, first[-1][3]),
                bboxes=first, font="helv", size=10, color=0,
                source="Tell your child you are looking for something",
                target=AR_LONG_A, status="translated"),
        Segment(id="p0-b", page=0, bbox=(40, second[0][1], 300, second[-1][3]),
                bboxes=second, font="helv", size=10, color=0,
                source="and have them describe where it is placed",
                target=AR_LONG_B, status="translated"),
    ]
    out = str(tmp_path / "out.pdf")
    rebuild_pdf(src, segs, out, target_lang="ar")

    assert _overlapping_pairs(out) == []


def test_text_inside_an_image_is_never_shrunk_for_a_neighbour(tmp_path):
    """Burned-in text is sized to the artwork it sits on, not to its neighbours.

    Shrinking it would leave the translation floating inside a cover patch cut
    for the original, so a colliding neighbour gives way instead.
    """
    src = str(tmp_path / "in.pdf")
    first, second = _stacked_pdf(src)
    banner = Segment(id="p0-img", page=0, bbox=(40, second[0][1], 300, second[-1][3]),
                     bboxes=second, font="OCR", size=10, color=0,
                     source="and have them describe where it is placed",
                     target=AR_LONG_B, status="translated", in_image=True, from_ocr=True)
    text = Segment(id="p0-a", page=0, bbox=(40, first[0][1], 300, first[-1][3]),
                   bboxes=first, font="helv", size=10, color=0,
                   source="Tell your child you are looking for something",
                   target=AR_LONG_A, status="translated")
    out = str(tmp_path / "out.pdf")
    outcomes = {o.segment_id: o for o in rebuild_pdf(src, [text, banner], out,
                                                    target_lang="ar")}

    assert "size=10.00" in outcomes["p0-img"].detail, "the in-image run was resized"


# --- unerasable artwork ------------------------------------------------------


def _vector_wordmark_pdf(path, page_width=400):
    """A logo: an asymmetric mark drawn as vector art, with no text layer.

    Shaped like an "L" so a reflection is detectable — a symmetric mark would
    look identical mirrored and prove nothing.
    """
    doc = fitz.open()
    page = doc.new_page(width=page_width, height=200)
    page.draw_rect(fitz.Rect(100, 40, 110, 90), color=None, fill=(0, 0, 0))
    page.draw_rect(fitz.Rect(100, 80, 160, 90), color=None, fill=(0, 0, 0))
    doc.save(path)
    doc.close()
    return (100, 40, 160, 90)


def test_unerasable_vector_wordmark_is_not_drawn_over(tmp_path):
    """Redaction cannot remove vector art, so the translation must not be set.

    Drawing it anyway doubles the target on top of an untouched logo — the
    measured behaviour on the real document.
    """
    src = str(tmp_path / "in.pdf")
    bbox = _vector_wordmark_pdf(src)
    seg = Segment(id="p0-l0", page=0, bbox=bbox, font="helv", size=11, color=0,
                  source="i-Ready Connect", target="آي-ريدي كونيكت",
                  status="translated")
    out = str(tmp_path / "out.pdf")
    outcomes = rebuild_pdf(src, [seg], out, target_lang="ar")

    assert [o.action for o in outcomes] == ["skipped_graphic"]
    assert _spans(out) == []  # nothing was set over the logo


def _ink(path, rect, pno=0, dpi=200):
    """Column-wise ink profile of a region, left to right."""
    doc = fitz.open(path)
    pix = doc.load_page(pno).get_pixmap(clip=fitz.Rect(rect), dpi=dpi,
                                        colorspace=fitz.csGRAY)
    doc.close()
    return [sum(1 for y in range(pix.height) if pix.pixel(x, y)[0] < 128)
            for x in range(pix.width)]


def test_mirrored_page_does_not_reflect_the_wordmark(tmp_path):
    """The mark must read the same way round after the page is mirrored.

    The "L" is bottom-heavy on its left. Reflected, it becomes bottom-heavy on
    its right — so comparing the two halves' ink detects the flip.
    """
    src = str(tmp_path / "in.pdf")
    bbox = _vector_wordmark_pdf(src)
    seg = Segment(id="p0-l0", page=0, bbox=bbox, font="helv", size=11, color=0,
                  source="i-Ready Connect", target="آي-ريدي كونيكت",
                  status="translated")
    out = str(tmp_path / "out.pdf")
    rebuild_pdf(src, [seg], out, target_lang="ar")

    # mirrored position of the mark on a 400pt page
    mirrored = (400 - bbox[2], bbox[1], 400 - bbox[0], bbox[3])
    profile = _ink(out, mirrored)
    half = len(profile) // 2
    assert sum(profile[:half]) > sum(profile[half:]) * 1.5, (
        "the tall stroke should still be on the left; it reads as reflected"
    )


def test_ordinary_text_is_still_replaced_and_mirrored(tmp_path):
    """The erase check must not turn into a blanket refusal.

    Real text redacts cleanly, so it keeps going down the replace path.
    """
    src = str(tmp_path / "in.pdf")
    doc = fitz.open()
    page = doc.new_page(width=400, height=200)
    page.insert_text((40, 60), "Conversation Starter", fontsize=11, fontname="helv")
    doc.save(src)
    doc.close()

    seg = Segment(id="p0-l0", page=0, bbox=(40, 51, 150, 64), font="helv",
                  size=11, color=0, source="Conversation Starter",
                  target="بداية محادثة", status="translated")
    out = str(tmp_path / "out.pdf")
    outcomes = rebuild_pdf(src, [seg], out, target_lang="ar")

    assert [o.action for o in outcomes] == ["replaced"]
    assert _spans(out), "the Arabic should have been set"


# --- OCR-tolerant duplicate suppression --------------------------------------


def test_ocr_typo_still_counts_as_a_duplicate_of_the_real_text(tmp_path):
    """"Math on tha go" (OCR) and "Math on the Go" (real run) are one headline.

    Exact substring matching missed this and drew both, so the two Arabic
    renderings landed on top of each other.
    """
    from babel.reassemble.pdf import _image_shadowed_duplicates

    ocr = Segment(id="ocr", page=0, bbox=(509, 82, 583, 98), font="OCR",
                  size=12, color=0, source="Math on tha go",
                  target="الرياضيات أثناء التنقل", status="translated",
                  in_image=True)
    real = Segment(id="real", page=0, bbox=(502, 78, 640, 101), font="helv",
                   size=12, color=0, source="Math on the Go",
                   target="الرياضيات أثناء التنقل", status="translated")

    assert _image_shadowed_duplicates([ocr, real]) == {"real"}


def test_unrelated_overlapping_text_is_not_suppressed():
    """Different content that happens to overlap must both survive."""
    from babel.reassemble.pdf import _image_shadowed_duplicates

    ocr = Segment(id="ocr", page=0, bbox=(500, 80, 600, 100), font="OCR",
                  size=12, color=0, source="GO !", target="انطلق!",
                  status="translated", in_image=True)
    real = Segment(id="real", page=0, bbox=(502, 78, 640, 101), font="helv",
                   size=12, color=0, source="Conversation Starter",
                   target="بداية محادثة", status="translated")

    assert _image_shadowed_duplicates([ocr, real]) == set()


# --- text the source hid under artwork ---------------------------------------

AR_HEADLINE = "الرياضيات أثناء التنقل"


def _covered_headline_pdf(path, cover="over", page_width=400):
    """A banner headline whose last word is hidden under an arrow graphic.

    The real page sets "Math on the Go" across a pink panel and then paints a
    "GO!" arrow over the tail of it, so only "Math on the" is ever read. The
    text run still measures the whole phrase, and that full-width box is what
    reassembly is handed.

    `cover` is "over" (arrow painted on top of the text, as the document has
    it), "under" (arrow painted first, text visible across it) or "none".
    """
    text, size = "Math on the Go", 18.0
    width = fitz.Font("helv").text_length(text, size)
    arrow = fitz.Rect(40 + width * 0.78, 40, 40 + width * 1.4, 82)
    doc = fitz.open()
    page = doc.new_page(width=page_width, height=140)
    page.draw_rect(fitz.Rect(30, 44, page_width - 30, 78), color=None,
                   fill=(0.77, 0.0, 0.46))  # the panel the headline sits on
    if cover == "under":
        page.draw_rect(arrow, color=None, fill=(0.55, 0.0, 0.32))
    page.insert_text((40, 62), text, fontsize=size, fontname="helv",
                     color=(1, 1, 1))
    if cover == "over":
        page.draw_rect(arrow, color=None, fill=(0.55, 0.0, 0.32))
    doc.save(path)
    doc.close()
    bbox = (40.0, 62 - size * 0.81, 40 + width, 62 + size * 0.19)
    return bbox, tuple(arrow)


def _headline_run(tmp_path, cover):
    """Set the Arabic headline on that page; return its outcome and spans."""
    src = str(tmp_path / f"in-{cover}.pdf")
    bbox, arrow = _covered_headline_pdf(src, cover=cover)
    seg = Segment(id="p0-l0", page=0, bbox=bbox, font="helv", size=18,
                  color=0xFFFFFF, source="Math on the Go",
                  target=AR_HEADLINE, status="translated")
    out = str(tmp_path / f"out-{cover}.pdf")
    outcomes = rebuild_pdf(src, [seg], out, target_lang="ar")
    return outcomes[0], _spans(out), fitz.Rect(400 - arrow[2], arrow[1],
                                               400 - arrow[0], arrow[3])


def _size_of(outcome):
    return float(re.search(r"size=([\d.]+)", outcome.detail).group(1))


def test_headline_is_not_set_under_the_artwork_that_hid_it(tmp_path):
    """The tail of the box was never visible, so nothing may be set there.

    Fitting the translation to the full box runs it under the arrow — the
    measured behaviour on the Arabic edition, where the Arabic headline
    overlapped the "GO!" callout on every activity page.
    """
    _, spans, arrow = _headline_run(tmp_path, "over")

    assert spans, "the Arabic should have been set"
    assert all((rect & arrow).is_empty for rect, _ in spans), (
        f"the headline runs under the arrow: {[tuple(r) for r, _ in spans]}"
    )


def test_an_unobstructed_headline_keeps_its_size(tmp_path):
    """The clip binds only where artwork actually hides part of the box."""
    covered, _, _ = _headline_run(tmp_path, "over")
    plain, _, _ = _headline_run(tmp_path, "none")

    assert _size_of(plain) > _size_of(covered)


def test_text_drawn_on_top_of_artwork_is_not_clipped(tmp_path):
    """Artwork the source text is set OVER leaves the whole box usable.

    Only a box whose own ink stops short of the artwork was hidden by it.
    """
    on_top, _, _ = _headline_run(tmp_path, "under")
    plain, _, _ = _headline_run(tmp_path, "none")

    assert _size_of(on_top) == _size_of(plain)


# --- artwork sitting in a merged block's indent -------------------------------

AR_TOOLS = "أدوات الرياضيات الرقمية: عدّادات ومكعبات متصلة"


def _panel_with_an_icon_pdf(path, icon=True, page_width=200):
    """A heading and an indented two-line item, with an icon in the indent.

    The real page sets "Digital Math Tools" flush against the panel and
    "Counters and / Connecting Cubes" indented past a counters icon. The two are
    close enough vertically that they merge into one paragraph, whose union box
    therefore spans the indent — and the icon standing in it.
    """
    font = fitz.Font("helv")
    rows, doc = [], fitz.open()
    page = doc.new_page(width=page_width, height=100)
    page.draw_rect(fitz.Rect(10, 5, page_width - 10, 95), color=None,
                   fill=(0.93, 0.97, 1.0))
    for text, x, y, size in (("Digital Math Tools", 20, 25, 12.0),
                             ("Counters and", 60, 42, 11.0),
                             ("Connecting Cubes", 60, 55, 11.0)):
        page.insert_text((x, y), text, fontsize=size, fontname="helv")
        rows.append((x, y - size * 0.81, x + font.text_length(text, size),
                     y + size * 0.19))
    art = fitz.Rect(22, 34, 52, 56)
    if icon:
        page.draw_rect(art, color=(0, 0.5, 0.8), width=1.2)
        for cx in (28, 36, 44):
            for cy in (40, 50):
                page.draw_circle(fitz.Point(cx, cy), 3.2, color=None,
                                 fill=(0.1, 0.55, 0.85))
    doc.save(path)
    doc.close()
    union = (min(r[0] for r in rows), min(r[1] for r in rows),
             max(r[2] for r in rows), max(r[3] for r in rows))
    return union, rows, tuple(art)


def _panel_run(tmp_path, icon):
    src = str(tmp_path / f"panel-{icon}.pdf")
    union, rows, art = _panel_with_an_icon_pdf(src, icon=icon)
    seg = Segment(id="p0-l0", page=0, bbox=union, bboxes=rows, font="helv",
                  size=12, color=0,
                  source="Digital Math Tools Counters and Connecting Cubes",
                  target=AR_TOOLS, status="translated")
    out = str(tmp_path / f"panel-{icon}-out.pdf")
    outcomes = rebuild_pdf(src, [seg], out, target_lang="ar")
    return outcomes[0], _spans(out), fitz.Rect(200 - art[2], art[1],
                                               200 - art[0], art[3])


def test_merged_block_is_not_set_over_the_icon_in_its_indent(tmp_path):
    """The indent belongs to the icon, not to the translation.

    The block's own rows leave that space empty; only the union of them claims
    it. Reflowing into the union is what ran the Arabic across the counters
    icon on the resource panel.

    The block is allowed to sit flush against the icon — that is the space the
    design left free — so the icon is measured half a point in.
    """
    _, spans, icon = _panel_run(tmp_path, True)

    assert spans, "the Arabic should have been set"
    assert all((rect & (icon + (0.5, 0, -0.5, 0))).is_empty for rect, _ in spans), (
        f"the block runs over the icon: {[tuple(r) for r, _ in spans]}"
    )


def test_the_same_block_without_an_icon_uses_the_whole_indent(tmp_path):
    """An empty indent is the block's to use, so nothing should be given up.

    The clip has to bind on the artwork, not on the shape of the rows — a
    merged block whose rows are ragged is the ordinary case, not a defect.
    """
    _, spans, icon = _panel_run(tmp_path, False)

    assert any(not (rect & icon).is_empty for rect, _ in spans), (
        "the block gave up space nothing was standing in"
    )


# --- what the page mirror must not flip --------------------------------------


def _grid(path, rect, pno=0, dpi=300):
    """A region of the page as rows of grey values."""
    doc = fitz.open(path)
    pix = doc.load_page(pno).get_pixmap(clip=fitz.Rect(rect), dpi=dpi,
                                        colorspace=fitz.csGRAY)
    doc.close()
    return [[pix.samples[y * pix.stride + x] for x in range(pix.width)]
            for y in range(pix.height)]


def _mismatch(a, b) -> float:
    """Mean per-pixel difference between two grids, 0 (same) to 1.

    The two clips land on different pixel boundaries and can differ by a row or
    column, so only the overlap of the two is compared.
    """
    h, w = min(len(a), len(b)), min(len(a[0]), len(b[0]))
    if w < 2 or h < 2:
        return 1.0
    return sum(abs(a[y][x] - b[y][x]) for y in range(h) for x in range(w)) / (255 * w * h)


def _reflected(grid):
    return [row[::-1] for row in grid]


def _reads_the_same_way_round(src, out, rect, page_width=400):
    """Is `rect` on the output the source's own region, or a reflection of it?

    Answered by comparing the output against the source both ways round rather
    than against a threshold: whichever it resembles more is the way it is set.
    """
    before = _grid(src, rect)
    after = _grid(out, (page_width - rect[2], rect[1], page_width - rect[0], rect[3]))
    return _mismatch(after, before) * 2 < _mismatch(after, _reflected(before))


def _badge_and_fraction_pdf(path, page_width=400):
    """A numbered disc and a stacked fraction, in the geometry the packets use.

    The numeral is "12", not "1": two digits of different widths make the
    knockout lopsided, so a reflection of the disc is detectable rather than
    looking like itself.

    The fraction is set the way the source PDF sets one — numerator, bar,
    denominator, the parenthesis around them and the exponent outside it, as
    separate runs whose boxes overlap. That fragmentation is the point of the
    test, and the boxes below are the real ones from the grade 8 exponents
    page, moved onto this one.
    """
    doc = fitz.open()
    page = doc.new_page(width=page_width, height=100)
    page.draw_circle(fitz.Point(51, 51), 11, color=None, fill=(0.39, 0.39, 0.40))
    page.insert_text((43, 56), "12", fontsize=15, fontname="helv", color=(1, 1, 1))
    page.insert_text((40, 22), "Rewrite each expression as a power",
                     fontsize=11, fontname="helv")
    page.insert_text((150, 50), "(6", fontsize=13, fontname="helv")
    page.draw_line(fitz.Point(156, 54), fitz.Point(174, 54), width=0.8)
    page.insert_text((157, 66), "12", fontsize=13, fontname="helv")
    page.insert_text((173, 45), ")2", fontsize=8, fontname="helv")
    doc.save(path)
    doc.close()
    disc = (40.0, 40.0, 62.0, 62.0)
    pieces = [(150.0, 38.0, 166.5, 67.2), (153.9, 48.3, 174.7, 67.5),
              (154.3, 40.9, 176.0, 68.8), (173.5, 39.5, 177.8, 49.0)]
    return disc, pieces, (150.0, 38.0, 177.8, 68.8)


def _badge_run(tmp_path):
    src = str(tmp_path / "badge.pdf")
    disc, pieces, whole = _badge_and_fraction_pdf(src)
    segs = [Segment(id="p0-prose", page=0, bbox=(40, 12, 220, 26), font="helv",
                    size=11, color=0, source="Rewrite each expression as a power",
                    target="أعد كتابة كل تعبير على صورة قوة", status="translated")]
    # The fraction's runs are digits and brackets: no engine changes them, so
    # reassembly leaves them alone and the mirror is all that touches them.
    for i, box in enumerate(pieces):
        segs.append(Segment(id=f"p0-m{i}", page=0, bbox=box, font="helv", size=11,
                            color=0, source="x", target="x", status="translated"))
    out = str(tmp_path / "badge-out.pdf")
    rebuild_pdf(src, segs, out, target_lang="ar")
    return src, out, disc, whole


def test_problem_badge_comes_back_the_same_way_round(tmp_path):
    """The numbered disc is artwork, so the mirror may move it but not flip it.

    `mathguard` drops badges from the text the pipeline translates, so no
    segment carries one and nothing protected them: every problem number on the
    Arabic edition of the fluency packets came out written backwards.
    """
    src, out, disc, _ = _badge_run(tmp_path)

    assert _reads_the_same_way_round(src, out, disc)


def test_a_fragmented_expression_keeps_its_order(tmp_path):
    """An expression split across several runs must be lifted as one picture.

    Stamped one run at a time, each lands at its own mirrored position and
    their order reverses — which is what turned (6⁴/12⁴)² into ²6⁴/12⁴)²⁴.
    """
    src, out, _, whole = _badge_run(tmp_path)

    assert _reads_the_same_way_round(src, out, whole)


def test_pieces_of_one_expression_are_merged():
    """Real geometry of (6⁴/12⁴)² from the grade 8 exponents page."""
    from babel.reassemble.pdf import _merged

    pieces = [fitz.Rect(435.6, 282.4, 452.1, 311.6),   # "(6" and its exponent
              fitz.Rect(439.5, 292.7, 460.3, 311.9),   # the fraction bar
              fitz.Rect(439.9, 285.3, 461.6, 313.2),   # "12" and the ")"
              fitz.Rect(459.1, 283.9, 463.4, 293.4)]   # the outer exponent

    assert [tuple(round(v, 1) for v in r) for r in _merged(pieces)] == [
        (435.6, 282.4, 463.4, 313.2)
    ]


def test_separate_lines_are_stamped_separately():
    """Merging keys on overlap, which stacked lines of text do not have.

    Left unbounded it would swallow the page and stamp the whole of it back
    unmirrored.
    """
    from babel.reassemble.pdf import _merged

    lines = [fitz.Rect(40, 100, 300, 114), fitz.Rect(40, 116, 300, 130),
             fitz.Rect(40, 132, 300, 146)]

    assert len(_merged(lines)) == 3
