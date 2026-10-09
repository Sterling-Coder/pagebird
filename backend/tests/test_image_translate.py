"""Image regions go through the shared Translator with protected literals intact."""

import sys
from pathlib import Path

from pagebirdy import languages
from pagebirdy.image import translate as image_translate
from pagebirdy.image.regions import TextRegion
from pagebirdy.image.translate import protect_region_text, translate_regions

sys.path.insert(0, str(Path(__file__).parent))
from image_fixtures import DictEngine  # noqa: E402


def _region(rid, text, action="translate"):
    box = (0.0, 0.0, 100.0, 20.0)
    return TextRegion(id=rid, text=text, bbox=box, confidence=0.99, lines=[box], action=action)


def test_url_and_email_inside_prose_become_placeholders():
    src, ph = protect_region_text("Visit www.shop2.com or mail help@shop2.com")
    assert src == "Visit ⟦~www.shop2.com⟧ or mail ⟦~help@shop2.com⟧"
    assert ph["⟦~www.shop2.com⟧"] == "www.shop2.com"


def test_numbers_and_math_use_the_document_placeholders():
    src, ph = protect_region_text("Solve 3 + 4 = 7 for 50% OFF")
    assert "⟦=3 + 4 = 7⟧" in src and "⟦=50%⟧" in src


def test_only_translate_regions_reach_the_engine_and_targets_restore_literals(tmp_path):
    eng = DictEngine({"Visit ⟦~www.example.com⟧": "Visitez ⟦~www.example.com⟧"})
    regions = [_region("r1", "Visit www.example.com"),
               _region("r2", "SKU-1234", action="protect")]
    segments, meta = translate_regions(regions, languages.get("fr"),
                                       engines=(eng, None))
    assert eng.seen == ["Visit ⟦~www.example.com⟧"]
    assert [s.id for s in segments] == ["r1"]
    assert regions[0].target == "Visitez www.example.com"
    assert regions[0].status == "translated"
    assert regions[1].target is None
    assert meta["engine_primary"] == "dict"


def test_engines_are_built_for_the_requested_target_language(monkeypatch):
    seen = {}

    def fake_build(doc_context="", target_lang=None):
        seen["target_lang"] = target_lang
        return DictEngine({}), None

    monkeypatch.setattr(image_translate, "build_engines", fake_build)
    translate_regions([_region("r1", "Welcome")], languages.get("ar"))
    assert seen["target_lang"] == "ar"
