"""Reading a Vision DOCUMENT_TEXT_DETECTION response into image regions.

The responses are built by hand in Vision's own shape (pages → blocks →
paragraphs → words → symbols), so no test calls the API.
"""

from types import SimpleNamespace as NS

import pytest

from pagebirdy.image import ocr as image_ocr
from pagebirdy.image.ocr import group_lines, parse_vision_response
from pagebirdy.image.regions import Word


def _verts(x0, y0, x1, y1):
    return [NS(x=x0, y=y0), NS(x=x1, y=y0), NS(x=x1, y=y1), NS(x=x0, y=y1)]


def _word(text, box, conf=0.99, last_break=1):
    symbols = [NS(text=c, property=None) for c in text]
    if last_break is not None:
        symbols[-1] = NS(text=text[-1], property=NS(detected_break=NS(type_=last_break)))
    return NS(symbols=symbols, bounding_box=NS(vertices=_verts(*box)), confidence=conf)


def _para(words, box, conf, lang="en"):
    prop = NS(detected_languages=[NS(language_code=lang, confidence=0.9)])
    return NS(words=words, bounding_box=NS(vertices=_verts(*box)), confidence=conf,
              property=prop)


def _response(paragraphs):
    block = NS(paragraphs=paragraphs, property=None)
    page = NS(blocks=[block], property=None)
    return NS(full_text_annotation=NS(pages=[page]))


def test_paragraph_becomes_one_region_with_words_lines_language_and_confidence():
    resp = _response([_para(
        [_word("Welcome", (10, 10, 90, 30)), _word("to", (95, 10, 115, 30)),
         _word("our", (10, 40, 50, 60)), _word("store", (55, 40, 110, 60), last_break=5)],
        (10, 10, 115, 60), conf=0.97)])
    [r] = parse_vision_response(resp)
    assert r.text == "Welcome to our store"
    assert r.bbox == (10, 10, 115, 60)
    assert r.confidence == pytest.approx(0.97)
    assert r.language == "en"
    assert [w.text for w in r.words] == ["Welcome", "to", "our", "store"]
    assert len(r.lines) == 2  # two visual lines
    assert r.lines[0][1] == 10 and r.lines[1][1] == 40
    assert r.angle == pytest.approx(0.0)


def test_boxes_are_scaled_back_to_the_full_resolution_image():
    resp = _response([_para([_word("SALE", (10, 10, 50, 20))], (10, 10, 50, 20), 0.99)])
    [r] = parse_vision_response(resp, scale=0.5)
    assert r.bbox == (20, 20, 100, 40)
    assert r.words[0].bbox == (20, 20, 100, 40)


def test_low_confidence_paragraphs_are_kept_not_dropped():
    # ingest/ocr.py drops these for PDFs; for an image they must reach the
    # classifier so they can be flagged for a person.
    resp = _response([_para([_word("blurry", (0, 0, 40, 10), conf=0.4)], (0, 0, 40, 10), 0.41)])
    [r] = parse_vision_response(resp)
    assert r.confidence == pytest.approx(0.41)


def test_end_of_line_hyphen_break_joins_the_word_halves():
    hyphen = 4
    resp = _response([_para([_word("trans", (0, 0, 40, 10), last_break=hyphen),
                             _word("lation", (0, 12, 40, 22))], (0, 0, 40, 22), 0.95)])
    assert parse_vision_response(resp)[0].text == "translation"


def test_words_with_no_break_marker_run_together():
    # Real Vision output for "50% OFF": "50" carries no break, so "%" follows
    # it directly; "%" carries a SPACE break before "OFF".
    resp = _response([_para([_word("50", (0, 0, 20, 10), last_break=None),
                             _word("%", (20, 0, 28, 10)),
                             _word("OFF", (32, 0, 60, 10))], (0, 0, 60, 10), 0.98)])
    assert parse_vision_response(resp)[0].text == "50% OFF"


def test_vertical_text_reports_its_angle():
    # Reading order runs down the page: first edge goes from (10,10) to (10,60).
    verts = [NS(x=10, y=10), NS(x=10, y=60), NS(x=0, y=60), NS(x=0, y=10)]
    para = _para([_word("AXIS", (0, 10, 10, 60))], (0, 10, 10, 60), 0.99)
    para.bounding_box = NS(vertices=verts)
    [r] = parse_vision_response(_response([para]))
    assert abs(r.angle) == pytest.approx(90.0)


def test_group_lines_splits_on_vertical_position():
    words = [Word("a", (0, 0, 10, 10)), Word("b", (12, 1, 20, 11)), Word("c", (0, 20, 10, 30))]
    assert group_lines(words) == [(0, 0, 20, 11), (0, 20, 10, 30)]


def test_no_engine_is_an_error_not_an_empty_result(monkeypatch):
    from PIL import Image

    monkeypatch.setenv("BABEL_IMAGE_OCR_ENGINE", "none")
    with pytest.raises(image_ocr.OcrError):
        image_ocr.run_ocr(Image.new("RGB", (40, 40)))


def test_engine_prefers_vision_when_configured(monkeypatch):
    monkeypatch.delenv("BABEL_IMAGE_OCR_ENGINE", raising=False)
    monkeypatch.setattr(image_ocr.base_ocr, "vision_status", lambda: image_ocr.base_ocr.OcrStatus(True))
    assert image_ocr.ocr_engine() == "vision"
    monkeypatch.setattr(image_ocr.base_ocr, "vision_status", lambda: image_ocr.base_ocr.OcrStatus(False, "x"))
    monkeypatch.setattr(image_ocr.base_ocr, "rapidocr_available", lambda: True)
    assert image_ocr.ocr_engine() == "rapidocr"
