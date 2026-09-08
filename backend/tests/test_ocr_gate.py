"""Which text found inside a raster image is worth replacing.

Translating burned-in text means covering the original pixels with a flat patch
and drawing over them. That is a good trade for a label a reader is meant to
read — a banner, a callout, a speech bubble — and a bad one for text that is
part of a depicted object, like the motto and mint date struck into a photographed
coin: the patch damages the artwork and buys nothing, because the text was never
addressed to the reader and is far too small to come back legibly.

The measurements below are real OCR output for a Kindergarten family letter whose
figures include photographed pennies. Two independent signals separate the two
classes, and the gate requires both:

    class                             confidence      implied size
    labels (GO!, SAY, speech bubble)  0.968 - 1.000   10.6 - 22.5 pt
    struck into a coin                0.552 - 0.965    6.0 pt (mostly)

A third check catches curved text regardless of how confidently it was read: a
motto following a coin's rim has an axis-aligned box far taller than any
horizontal setting of those characters could be. Measured as box height over the
height one line of that text needs, real labels run 0.76 - 1.03 while text
struck around a rim runs 1.4 and up.

All boxes below are RAW OCR geometry — what the gate sees. Reassembly pads boxes
by 20% afterwards so redaction clears the whole glyph, which inflates them.
"""

import pytest

from babel.ingest.ocr import MIN_IMAGE_CONFIDENCE, MIN_IMAGE_SIZE, worth_translating
from babel.models import Line, Span


def _line(text, w, h, confidence, x0=100.0, y0=100.0):
    bbox = (x0, y0, x0 + w, y0 + h)
    size = max(6.0, min(24.0, h * 0.8))
    return Line(page=0, bbox=bbox,
                spans=[Span(text=text, font="OCR", size=size, color=0, bbox=bbox)],
                from_ocr=True, in_image=True, ocr_confidence=confidence)


# --- real labels: every one must survive ------------------------------------

KEEP = [
    ("GO!", 37.4, 19.4, 0.996),
    ("SAY", 61.1, 27.7, 0.988),
    ("This group has brown", 116.1, 14.8, 0.997),
    ("spoons. There are", 97.2, 14.8, 0.995),
    ("2 brown spoons.", 90.9, 14.8, 1.000),
    ("I see a group of 4 pel", 115.2, 13.2, 0.968),
    ("and a group of 2 pen", 114.5, 13.9, 0.995),
    ("There are 6 pennies i", 114.7, 13.7, 0.993),
]

# --- struck into a coin: every one must be refused ---------------------------

DROP = [
    ("2004", 13.0, 5.3, 0.908),
    ("2064", 12.7, 5.8, 0.831),
    ("APN", 15.4, 4.8, 0.765),
    ("AmPen", 15.1, 4.8, 0.696),
    ("LtREAYY", 15.4, 5.5, 0.644),
    ("LIERTV", 15.1, 5.3, 0.620),
    ("LOCATY", 15.1, 4.3, 0.681),
    ("CRERTY", 16.1, 5.3, 0.591),
    ("CIECRTY", 16.1, 5.3, 0.574),
    ("ATT", 14.9, 4.6, 0.914),
    ("CIERYY", 14.6, 4.6, 0.789),
    ("CMERTY", 14.6, 4.6, 0.767),
    ("LSUERTY", 15.1, 5.8, 0.666),
    ("LERO'Y", 14.4, 4.6, 0.640),
    ("LIAEATY", 14.9, 4.6, 0.600),
    ("CED", 16.8, 9.8, 0.612),
    ("OEN", 17.5, 11.0, 0.552),
]


@pytest.mark.parametrize("text,w,h,conf", KEEP, ids=[k[0][:14] for k in KEEP])
def test_real_labels_are_kept(text, w, h, conf):
    assert worth_translating(_line(text, w, h, conf)) is True


@pytest.mark.parametrize("text,w,h,conf", DROP, ids=[d[0][:14] for d in DROP])
def test_coin_text_is_refused(text, w, h, conf):
    assert worth_translating(_line(text, w, h, conf)) is False


def test_thresholds_sit_in_the_measured_gap():
    """Guard the calibration: the gate must not drift onto either class."""
    assert max(h * 0.8 for _, _, h, _ in DROP if h * 0.8 < 10) < MIN_IMAGE_SIZE
    assert MIN_IMAGE_SIZE <= min(h * 0.8 for _, _, h, _ in KEEP)
    assert MIN_IMAGE_CONFIDENCE <= min(c for *_, c in KEEP)


# --- curved text, caught by geometry rather than confidence ------------------
#
# Boxes measured from the same document's Google Vision pass, where a motto
# arcing over a coin comes back as a tall, near-square box.

# "ONE CENT" (52.8 x 34.3) is deliberately absent: a two-word phrase in a box
# two lines tall is exactly what a real two-line label looks like, so geometry
# cannot refuse it without also refusing legitimate ones. It is left to the
# confidence bar, and is the known residual of this gate.
ARC = [
    ("AMERICA", 18.7, 23.3),
    ("S CALLING", 20.4, 24.9),
    ("ERICA", 10.6, 16.8),
    ("TRUST", 15.4, 11.8),
    # Read at 0.965 — too close to the lowest real label (0.968) for the
    # confidence bar to separate, so the geometry has to.
    ("ONE", 21.8, 17.3),
]


@pytest.mark.parametrize("text,w,h", ARC, ids=[a[0][:12] for a in ARC])
def test_text_curved_around_a_coin_is_refused(text, w, h):
    """A box far taller than the text could be set horizontally is not a label.

    Read with full confidence, so only the geometry can reject it.
    """
    assert worth_translating(_line(text, w, h, 0.99)) is False


STRAIGHT = [
    ("GO !", 33.8, 14.1),
    ("SAY", 48.3, 29.0),
    # A genuine multi-line speech bubble: tall because it holds three lines.
    ("spoons . There are 2 brown spoons .", 94.6, 28.8),
]


@pytest.mark.parametrize("text,w,h", STRAIGHT, ids=[s[0][:12] for s in STRAIGHT])
def test_horizontal_labels_survive_the_geometry_check(text, w, h):
    assert worth_translating(_line(text, w, h, 0.99)) is True


# --- scope -------------------------------------------------------------------


def test_gate_only_applies_to_text_inside_images():
    """Ordinary PDF text is not OCR'd and must never be judged by this gate."""
    line = _line("2004", 15.1, 7.4, 0.908)
    line.in_image = False
    line.from_ocr = False
    assert worth_translating(line) is True


# --- OCR that re-reads live text ---------------------------------------------
#
# `ocr_image_regions` reads a RENDER of the image's region, not the image's own
# bytes, so ordinary PDF text drawn over a photo comes back as if it had been
# burned in. `merge_ocr_lines` drops such re-reads, and the geometry it is given
# below is the real geometry of a Kindergarten speech bubble: OCR returned the
# whole three-line sentence as one line, so no single PDF line accounts for even
# a third of its box even though together they account for three quarters of it.

def _pdf_line(text, bbox):
    return Line(page=0, bbox=bbox,
                spans=[Span(text=text, font="AvenirRdCA-DemiBold", size=11.0,
                            color=0, bbox=bbox)])


def _ocr_line(text, bbox):
    return Line(page=0, bbox=bbox,
                spans=[Span(text=text, font="OCR", size=10.0, color=0, bbox=bbox)],
                from_ocr=True, in_image=True, ocr_confidence=0.99)


BUBBLE_ROWS = [
    ("This group has brown ", (472.4, 322.8, 590.7, 337.0)),
    ("spoons. There are ", (472.4, 336.8, 569.7, 351.0)),
    ("2 brown spoons.", (472.4, 350.8, 560.6, 365.0)),
]


def test_ocr_reread_of_live_text_over_a_photo_is_dropped():
    """One OCR line covering three PDF lines is still a duplicate of them.

    Kept, it is translated a second time and drawn over the first — the two
    Arabic renderings that landed on top of each other in the speech bubble.
    """
    from babel.ingest.ocr import merge_ocr_lines

    base = [_pdf_line(t, b) for t, b in BUBBLE_ROWS]
    reread = _ocr_line("spoons . There are 2 brown spoons .",
                       (466.2, 331.8, 572.2, 372.1))

    assert merge_ocr_lines(base, [reread]) == base


def test_text_burned_into_artwork_beside_a_run_is_kept():
    """"GO !" is struck into the arrow, not a re-reading of the headline.

    It brushes the headline's box — the arrow is painted over the tail of it —
    but covers only a quarter of its own, which is what tells the two apart.
    """
    from babel.ingest.ocr import merge_ocr_lines

    base = [_pdf_line("Math on the Go", (502.0, 78.3, 639.9, 101.1))]
    burned = _ocr_line("GO !", (624.9, 70.4, 664.4, 90.3))

    assert merge_ocr_lines(base, [burned]) == base + [burned]
