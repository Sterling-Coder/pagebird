"""Page mirroring for RTL output."""

import fitz
import pytest

from babel.reassemble.pdf import mirror_bbox, mirror_page


def _ink_x_range(page, dpi=72):
    """Horizontal extent of everything drawn on the page, in points."""
    pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
    scale = dpi / 72
    cols = [x for x in range(pix.width)
            if any(pix.pixel(x, y)[0] < 128 for y in range(pix.height))]
    assert cols, "page is blank"
    return min(cols) / scale, max(cols) / scale


def test_mirror_bbox_reflects_across_the_page_centre():
    # A box 10pt from the left edge of a 600pt page lands 10pt from the right.
    assert mirror_bbox((10, 20, 110, 40), 600) == (490, 20, 590, 40)


def test_mirror_bbox_preserves_width_and_vertical_position():
    box = (72.5, 100.0, 300.25, 140.0)
    x0, y0, x1, y1 = mirror_bbox(box, 612)
    assert x1 - x0 == pytest.approx(box[2] - box[0])
    assert (y0, y1) == (box[1], box[3])


def test_mirror_bbox_is_its_own_inverse():
    box = (33.0, 10.0, 91.0, 25.0)
    assert mirror_bbox(mirror_bbox(box, 612), 612) == box


def test_centred_box_is_unmoved():
    assert mirror_bbox((250, 0, 350, 10), 600) == (250, 0, 350, 10)


def test_mirror_page_moves_existing_ink_to_the_other_side():
    doc = fitz.open()
    page = doc.new_page(width=600, height=200)
    page.draw_rect(fitz.Rect(20, 20, 120, 60), color=None, fill=(0, 0, 0))
    assert _ink_x_range(page) == pytest.approx((20, 120), abs=2)

    page = mirror_page(page)

    assert _ink_x_range(page) == pytest.approx((480, 580), abs=2)


def test_content_drawn_after_mirroring_is_not_mirrored():
    """The whole point of mirroring last: translated text must land untouched.

    Two identical marks near the left edge — one drawn before the mirror, one
    after. Only the first should move.
    """
    doc = fitz.open()
    page = doc.new_page(width=600, height=200)
    page.draw_rect(fitz.Rect(20, 20, 120, 60), color=None, fill=(0, 0, 0))

    page = mirror_page(page)
    page.draw_rect(fitz.Rect(20, 100, 120, 140), color=None, fill=(0, 0, 0))

    lo, hi = _ink_x_range(page)
    assert lo == pytest.approx(20, abs=2)    # the mark drawn after: still left
    assert hi == pytest.approx(580, abs=2)   # the mark drawn before: now right


def test_mirroring_twice_restores_the_original_position():
    doc = fitz.open()
    page = doc.new_page(width=600, height=200)
    page.draw_rect(fitz.Rect(20, 20, 120, 60), color=None, fill=(0, 0, 0))

    page = mirror_page(page)
    page = mirror_page(page)

    assert _ink_x_range(page) == pytest.approx((20, 120), abs=2)
