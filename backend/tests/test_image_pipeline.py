"""Image translation end to end, on generated images (see image_fixtures.py).

Each scenario runs the real pipeline — validation, classification, the shared
Translator with its integrity gate, fitting, background reconstruction,
MuPDF rendering and the quality checks — with only the OCR and the engine
replaced by deterministic stand-ins.
"""

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pagebirdy.image.pipeline import ImageTranslationError, translate_image

sys.path.insert(0, str(Path(__file__).parent))
from image_fixtures import DictEngine, Scene, TextItem, fake_ocr, render_scene  # noqa: E402


def _run(tmp_path, scene, table, lang, fmt="PNG", ocr=None, **kw):
    img, regions = render_scene(scene)
    ext = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[fmt]
    src = tmp_path / f"scene{ext}"
    img.save(src, fmt, **({"quality": 95} if fmt == "JPEG" else {}))
    eng = DictEngine(table)
    stages = []
    report, segments = translate_image(
        str(src), str(tmp_path / "out"), lang, engines=(eng, None),
        ocr=ocr or fake_ocr(regions), verify=False,
        progress=lambda stage, pct, detail="": stages.append((stage, pct)), **kw)
    return report, segments, eng, stages, src


def _pixels(path):
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB")).astype(int)


def _info(path):
    """(format, size) without leaving the file open."""
    with Image.open(path) as im:
        return im.format, im.size


def _region(report, rid):
    return next(r for r in report["regions"] if r["id"] == rid)


def _changed(a, b, bbox):
    x, y, w, h = (int(round(bbox[k])) for k in ("x", "y", "width", "height"))
    return np.any(a[y:y + h, x:x + w] != b[y:y + h, x:x + w])


STORE = Scene(width=520, height=300, background="gradient", graphic=True, items=[
    TextItem(["Welcome to our store"], 40, 70, size=30, color=(20, 20, 60), bold=True),
    TextItem(["50% OFF"], 200, 140, size=34, color=(200, 0, 0)),
])


def test_english_to_french(tmp_path):
    report, segments, eng, stages, src = _run(tmp_path, STORE, {
        "Welcome to our store": "Bienvenue dans notre magasin",
        "⟦=50%⟧ OFF": "⟦=50%⟧ DE RÉDUCTION"}, "fr")
    assert report["target_lang"] == "fr" and report["direction"] == "ltr"
    assert [_region(report, r)["target"] for r in ("r1", "r2")] == \
        ["Bienvenue dans notre magasin", "50% DE RÉDUCTION"]
    assert report["quality"]["passed"], report["quality"]
    assert _info(report["output"]) == ("PNG", _info(src)[1])
    assert _region(report, "r1")["render"]["bold"]  # heading weight carried over
    # every stage reported, in order
    order = [s for s, _ in stages]
    assert order.index("validation") < order.index("ocr") < order.index("classification") \
        < order.index("translation") < order.index("reconstruction") < order.index("quality")


def test_english_to_arabic(tmp_path):
    report, *_ = _run(tmp_path, STORE, {
        "Welcome to our store": "مرحبا بكم في متجرنا",
        "⟦=50%⟧ OFF": "خصم ⟦=50%⟧"}, "ar")
    r1 = _region(report, "r1")
    assert report["direction"] == "rtl"
    assert r1["target"] == "مرحبا بكم في متجرنا"
    assert r1["render"]["direction"] == "rtl" and r1["render"]["align"] == "right"
    assert _region(report, "r2")["render"]["align"] == "center"  # centred stays centred
    assert report["quality"]["passed"], report["quality"]


def test_multiple_regions_each_stay_in_their_own_box(tmp_path):
    scene = Scene(items=[TextItem(["Open"], 30, 60), TextItem(["Closed"], 260, 60),
                         TextItem(["Monday to Friday"], 30, 160, size=20)])
    report, segments, *_ = _run(tmp_path, scene, {"Open": "Ouvert", "Closed": "Fermé",
                                                  "Monday to Friday": "Du lundi au vendredi"}, "fr")
    drawn = [r for r in report["regions"] if r["render"].get("drawn")]
    assert len(drawn) == 3 and len(segments) == 3
    boxes = [r["render"]["box"] for r in drawn]
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1], (a, b)


def test_numbers_are_protected_and_their_pixels_untouched(tmp_path):
    scene = Scene(items=[TextItem(["Price"], 30, 60), TextItem(["$19.99"], 30, 140, size=30)])
    report, _, eng, _, src = _run(tmp_path, scene, {"Price": "Prix"}, "fr")
    price = _region(report, "r2")
    assert (price["content_type"], price["status"]) == ("number", "protected")
    assert "$19.99" not in " ".join(eng.seen)
    assert not _changed(_pixels(src), _pixels(report["output"]), price["bbox"])


def test_url_region_is_left_exactly_as_drawn(tmp_path):
    scene = Scene(items=[TextItem(["Shop online"], 30, 60), TextItem(["www.example.com"], 30, 150)])
    report, _, eng, _, src = _run(tmp_path, scene, {"Shop online": "Achetez en ligne"}, "fr")
    url = _region(report, "r2")
    assert url["content_type"] == "url" and url["action"] == "protect"
    assert eng.seen == ["Shop online"]
    assert not _changed(_pixels(src), _pixels(report["output"]), url["bbox"])


def test_graphics_and_everything_outside_text_regions_are_unchanged(tmp_path):
    report, *_ , src = _run(tmp_path, STORE, {"Welcome to our store": "Willkommen in unserem Geschäft",
                                              "⟦=50%⟧ OFF": "⟦=50%⟧ RABATT"}, "de")
    a, b = _pixels(src), _pixels(report["output"])
    outside = np.ones(a.shape[:2], bool)
    for r in report["regions"]:
        if r["render"].get("drawn"):
            x0, y0, x1, y1 = r["render"]["box"]
            outside[y0:y1, x0:x1] = False
    assert not np.any(a[outside] != b[outside])
    # the red circle in the corner, in particular
    assert np.array_equal(a[220:280, 440:500], b[220:280, 440:500])


def test_long_translation_fits_inside_the_original_box(tmp_path):
    scene = Scene(items=[TextItem(["Welcome to our store"], 40, 80, size=30)])
    report, *_ = _run(tmp_path, scene, {
        "Welcome to our store": "Herzlich willkommen in unserem Geschäft"}, "de")
    r1 = _region(report, "r1")
    fit = r1["render"]["fit"]
    assert r1["render"]["drawn"] and r1["render"]["inside_box"]
    assert fit["shrunk"] and not fit["forced"] and fit["font_px"] < fit["natural_px"]
    assert report["quality"]["passed"], report["quality"]


def test_extreme_expansion_is_forced_into_the_box_and_flagged(tmp_path):
    scene = Scene(items=[TextItem(["Sale"], 40, 80, size=36)])
    report, *_ = _run(tmp_path, scene, {"Sale": "Ausverkauf zu stark reduzierten Preisen"}, "de")
    r1 = _region(report, "r1")
    assert r1["render"]["fit"]["forced"] and r1["render"]["inside_box"]
    assert any("scaled below the minimum" in w for w in r1["warnings"])
    check = next(c for c in report["quality"]["checks"] if c["name"] == "no_clipped_or_forced_text")
    assert not check["passed"] and "r1" in check["detail"]
    assert next(c for c in report["quality"]["checks"]
                if c["name"] == "unrelated_pixels_unchanged")["passed"]


def test_low_confidence_text_is_not_translated_and_is_reported(tmp_path):
    scene = Scene(items=[TextItem(["Welcome"], 30, 60),
                         TextItem(["Smudged note"], 30, 160, confidence=0.61)])
    report, segments, eng, _, src = _run(tmp_path, scene, {"Welcome": "Bienvenue"}, "fr")
    low = _region(report, "r2")
    assert (low["content_type"], low["status"], low["target"]) == ("low_confidence", "needs_human", None)
    assert "Smudged note" not in eng.seen
    assert any(w["region"] == "r2" and "61%" in w["message"] for w in report["warnings"])
    assert not _changed(_pixels(src), _pixels(report["output"]), low["bbox"])
    assert not next(c for c in report["quality"]["checks"] if c["name"] == "ocr_confidence")["passed"]


def test_image_with_no_text_returns_the_original_unchanged(tmp_path):
    scene = Scene(graphic=True)
    report, segments, eng, _, src = _run(tmp_path, scene, {}, "fr", ocr=lambda img: [])
    assert segments == [] and eng.seen == []
    assert Path(report["output"]).read_bytes() == src.read_bytes()
    assert any("No text" in w["message"] for w in report["warnings"])


def test_jpeg_stays_jpeg_with_the_same_dimensions(tmp_path):
    report, *_ , src = _run(tmp_path, STORE, {"Welcome to our store": "Bienvenue"}, "fr", fmt="JPEG")
    assert _info(report["output"]) == ("JPEG", _info(src)[1])
    assert report["output"].endswith(".fr.jpg")


def test_webp_stays_webp(tmp_path):
    report, *_ = _run(tmp_path, STORE, {"Welcome to our store": "Bienvenue"}, "fr", fmt="WEBP")
    assert _info(report["output"])[0] == "WEBP"


def test_invalid_image_fails_at_validation(tmp_path):
    bad = tmp_path / "x.png"
    bad.write_bytes(b"not an image")
    with pytest.raises(ImageTranslationError) as e:
        translate_image(str(bad), str(tmp_path), "fr", engines=(DictEngine({}), None),
                        ocr=lambda img: [])
    assert e.value.stage == "validation"


def test_verification_ocr_confirms_the_drawn_translation(tmp_path):
    img, regions = render_scene(STORE)
    src = tmp_path / "s.png"
    img.save(src)
    calls = []

    def ocr(image):
        calls.append(image)
        if len(calls) == 1:
            return fake_ocr(regions)(image)
        # Second call reads the output: report what was drawn.
        out = fake_ocr(regions)(image)
        out[0].text, out[1].text = "Bienvenue dans notre magasin", "50% DE RÉDUCTION"
        return out

    report, _ = translate_image(str(src), str(tmp_path / "o"), "fr", ocr=ocr, verify=True,
                                engines=(DictEngine({"Welcome to our store": "Bienvenue dans notre magasin",
                                                     "⟦=50%⟧ OFF": "⟦=50%⟧ DE RÉDUCTION"}), None))
    v = report["verification"]
    assert v["ran"] and v["verified"] == v["total"] == 2
