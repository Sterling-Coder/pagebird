"""Linked .psd support in the IDML graphics-translation path.

PyMuPDF can't open .psd directly, so `_psd_to_pdf` composites it to a flat
image and wraps that in a synthetic one-page PDF first — everything
downstream (extract_lines, ocr_image_regions, rebuild_pdf) then sees an
ordinary PDF, same as any other linked graphic.
"""

import os

import fitz
import pytest
from PIL import Image

from pagebirdy.idml import graphics
from pagebirdy.models import Line, Span
from pagebirdy.translate.engine import Engine
from pagebirdy.translate.translator import Translator


class MapEngine(Engine):
    name = "fake"

    def __init__(self, mapping):
        self.mapping = mapping

    def translate(self, texts):
        return [self.mapping.get(t, t) for t in texts]


def test_output_filename_swaps_psd_extension_to_pdf():
    name = graphics._output_filename("/Links/L01_RCM06_NA_SW_CA001.psd", "abc123")
    assert name.endswith(".pdf")
    assert not name.endswith(".psd")
    assert name == "L01_RCM06_NA_SW_CA001-abc123.pdf"


def test_output_filename_leaves_ai_extension_alone():
    name = graphics._output_filename("/Links/SAY.ai", "abc123")
    assert name.endswith(".ai")


def test_output_filename_same_content_same_name_different_path():
    # The whole point of hashing content instead of path: two jobs whose
    # source path differs (separate upload temp dirs) but whose Links file is
    # byte-identical must land on the same cache key.
    assert (graphics._output_filename("/job1/Links/SAY.ai", "deadbeef")
            == graphics._output_filename("/job2/Links/SAY.ai", "deadbeef"))


def test_psd_to_pdf_composites_and_wraps_in_one_page_pdf(tmp_path, monkeypatch):
    # Stand in for a real .psd: psd-tools' PSDImage.open().composite() is the
    # only interface `_psd_to_pdf` uses, so stubbing that call is enough to
    # test the conversion without needing a real binary .psd fixture.
    image = Image.new("RGB", (200, 100), color="white")

    class FakePSDImage:
        @staticmethod
        def open(path):
            assert path == "fake.psd"
            return FakePSDImage()

        def composite(self):
            return image

    monkeypatch.setattr("psd_tools.PSDImage", FakePSDImage)

    out_pdf = graphics._psd_to_pdf("fake.psd")
    try:
        doc = fitz.open(out_pdf)
        assert doc.page_count == 1
        assert doc[0].rect.width == pytest.approx(200, abs=1)
        assert doc[0].rect.height == pytest.approx(100, abs=1)
        doc.close()
    finally:
        os.remove(out_pdf)


def test_translate_graphic_handles_psd_end_to_end(tmp_path, monkeypatch):
    image = Image.new("RGB", (300, 100), color="white")

    class FakePSDImage:
        @staticmethod
        def open(path):
            return FakePSDImage()

        def composite(self):
            return image

    monkeypatch.setattr("psd_tools.PSDImage", FakePSDImage)

    # A PSD never has live text objects (extract_lines on the synthetic PDF
    # finds nothing) — OCR is the only source, so stub it with a canned Line,
    # matching this codebase's own convention of not invoking real OCR
    # inference in unit tests (see test_pdf_to_idml.py's OCR tests).
    ocr_line = Line(
        page=0, bbox=(10, 10, 150, 30),
        spans=[Span(text="Hello world", bbox=(10, 10, 150, 30),
                    font="helv", size=14, color=0, flags=0)],
        from_ocr=True, in_image=True,
    )
    monkeypatch.setattr(graphics, "ocr_image_regions", lambda *a, **k: ([ocr_line], "stub"))

    src_psd = str(tmp_path / "source.psd")
    with open(src_psd, "wb") as f:
        f.write(b"not a real psd, never read directly by translate_graphic")
    out_pdf = str(tmp_path / "out" / "translated.pdf")

    from pagebirdy import languages
    lang = languages.get("es")
    eng = MapEngine({"Hello world": "Hola mundo"})

    translated = graphics.translate_graphic(
        src_psd, out_pdf, lang, primary=eng, secondary=None, with_ocr=True
    )

    assert translated is True
    assert os.path.exists(out_pdf)
    doc = fitz.open(out_pdf)
    text = doc[0].get_text()
    doc.close()
    assert "Hola" in text


def test_translate_linked_graphics_reuses_byte_identical_file_across_jobs(tmp_path, monkeypatch):
    """A batch of documents that all attach the same Links folder (a shared
    logo/callout reused across chapters) must OCR+translate each distinct
    graphic once, not once per job — the whole point of hashing by content
    (see `_output_filename`) rather than by the source's own path, which
    differs per upload even when the bytes are identical."""
    # Two jobs' own copies of the byte-identical linked graphic, at different
    # paths — mirrors two separate upload temp dirs attaching the same file.
    job1_dir = tmp_path / "job1" / "Links"
    job2_dir = tmp_path / "job2" / "Links"
    job1_dir.mkdir(parents=True)
    job2_dir.mkdir(parents=True)
    content = b"not a real .ai file, only its bytes matter for the hash"
    job1_file = str(job1_dir / "SAY.ai")
    job2_file = str(job2_dir / "SAY.ai")
    with open(job1_file, "wb") as f:
        f.write(content)
    with open(job2_file, "wb") as f:
        f.write(content)

    monkeypatch.setattr(
        graphics, "find_linked_graphics",
        lambda entries: {"linkuri1": job1_file} if entries == "job1" else {"linkuri2": job2_file},
    )

    calls = {"n": 0}

    def fake_translate_graphic(path, out_path, lang, primary, secondary, with_ocr=True):
        calls["n"] += 1
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(b"translated output")
        return True

    monkeypatch.setattr(graphics, "translate_graphic", fake_translate_graphic)

    from pagebirdy import languages
    lang = languages.get("es")
    out_dir = str(tmp_path / "out")

    mapping1 = graphics.translate_linked_graphics(
        "job1", lang, primary=None, secondary=None, out_dir=out_dir)
    mapping2 = graphics.translate_linked_graphics(
        "job2", lang, primary=None, secondary=None, out_dir=out_dir)

    assert calls["n"] == 1  # second job's byte-identical file hit the cache
    assert mapping1["linkuri1"] == mapping2["linkuri2"]  # same output file reused


def test_translate_linked_graphics_caches_nothing_to_translate_too(tmp_path, monkeypatch):
    """A graphic determined to have no translatable text still costs an OCR
    pass to find that out — that result is cached too, not just a positive
    translation, or a pure-artwork asset shared across a batch would eat one
    OCR pass per job for a result that never changes."""
    links_dir = tmp_path / "Links"
    links_dir.mkdir()
    src_file = str(links_dir / "logo.ai")
    with open(src_file, "wb") as f:
        f.write(b"pure artwork, nothing to translate")

    monkeypatch.setattr(graphics, "find_linked_graphics", lambda entries: {"linkuri": src_file})

    calls = {"n": 0}

    def fake_translate_graphic(path, out_path, lang, primary, secondary, with_ocr=True):
        calls["n"] += 1
        return False  # nothing translatable, no output written

    monkeypatch.setattr(graphics, "translate_graphic", fake_translate_graphic)

    from pagebirdy import languages
    lang = languages.get("es")
    out_dir = str(tmp_path / "out")

    mapping1 = graphics.translate_linked_graphics(
        "e", lang, primary=None, secondary=None, out_dir=out_dir)
    mapping2 = graphics.translate_linked_graphics(
        "e", lang, primary=None, secondary=None, out_dir=out_dir)

    assert calls["n"] == 1
    assert mapping1 == {} and mapping2 == {}
