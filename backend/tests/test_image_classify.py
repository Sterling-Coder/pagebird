"""Which image regions are translated and which keep their original pixels."""

import pytest

from pagebirdy.image.classify import classify
from pagebirdy.image.regions import TextRegion


def _region(text, conf=0.98, h=20.0, angle=0.0):
    box = (10.0, 10.0, 10.0 + 10 * len(text), 10.0 + h)
    return TextRegion(id="r1", text=text, bbox=box, confidence=conf, lines=[box], angle=angle)


def _one(text, **kw):
    [r] = classify([_region(text, **kw)], min_conf=0.8, terms=("Babel Learning",))
    return r


@pytest.mark.parametrize("text,kind", [
    ("www.example.com", "url"),
    ("https://shop.example.org/sale", "url"),
    ("help@example.com", "email"),
    ("50%", "number"),
    ("$19.99", "number"),
    ("2024", "number"),
    ("3 + 4 = 7", "math"),
    ("SKU-4471B", "code"),
    ("A1B2C3", "code"),
    ("Babel Learning", "brand"),
    ("x", "symbol"),
])
def test_protected_content(text, kind):
    r = _one(text)
    assert (r.content_type, r.action, r.status) == (kind, "protect", "protected")


@pytest.mark.parametrize("text,kind", [
    ("Welcome to our store", "text"),
    ("50% OFF", "label"),
    ("Open daily", "label"),
    ("Visit www.example.com for opening hours", "text"),  # URL inside prose: protected inline, not whole
])
def test_translated_content(text, kind):
    r = _one(text)
    assert (r.content_type, r.action) == (kind, "translate")


def test_low_confidence_is_never_translated_and_is_flagged():
    r = _one("Welcome", conf=0.61)
    assert (r.content_type, r.action, r.status) == ("low_confidence", "protect", "needs_human")
    assert any("61%" in w for w in r.warnings)


def test_confidence_threshold_is_configurable(monkeypatch):
    monkeypatch.setenv("BABEL_IMAGE_MIN_CONFIDENCE", "0.5")
    [r] = classify([_region("Welcome", conf=0.61)], terms=())
    assert r.action == "translate"


def test_rotated_and_tiny_text_is_left_alone():
    assert _one("Vertical label", angle=90.0).content_type == "rotated"
    assert _one("Slightly skewed sign", angle=4.0).action == "translate"
    assert _one("tiny print", h=5.0).content_type == "too_small"


def test_a_much_larger_line_is_a_heading():
    regions = [_region("Big Title"), _region("small body text here", h=10),
               _region("more body text here", h=10)]
    regions[0].bbox = (0, 0, 200, 40)
    regions[0].lines = [regions[0].bbox]
    classify(regions, min_conf=0.8, terms=())
    assert regions[0].content_type == "heading"
