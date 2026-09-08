"""PDF → IDML build, preview render, OCR gating, equation detection."""

from __future__ import annotations

import os
import zipfile
from xml.etree import ElementTree as ET

import fitz
import pytest

from babel.idml.build import build_idml, specs_from_lines
from babel.idml.preview import render_idml
from babel.ingest.ocr import detect_image_regions, detect_scanned_pages, ocr_pages, ocr_status
from babel.ingest.pdf import extract_lines
from babel.protect.equations import detect_regions, looks_like_math
from babel.translate.integrity import line_count_ok


@pytest.fixture
def sample_pdf(tmp_path):
    """Two pages: prose, an equation-ish line, and a drawn rectangle."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 100), "Solve each problem. Show your work.", fontsize=11)
    page.insert_text((72, 140), "3 x 4 = 12", fontsize=11)
    page.draw_rect(fitz.Rect(72, 200, 300, 320), color=(0, 0, 0), width=1)
    page2 = doc.new_page(width=612, height=792)
    page2.insert_text((72, 100), "Second page body text.", fontsize=11)
    path = tmp_path / "sample.pdf"
    doc.save(path)
    doc.close()
    return str(path)


# --- IDML build -----------------------------------------------------------

def test_build_idml_package_structure(sample_pdf, tmp_path):
    out = str(tmp_path / "out.idml")
    result = build_idml(sample_pdf, out, backgrounds=False)

    assert result["pages"] == 2
    assert result["frames"] >= 3

    with zipfile.ZipFile(out) as z:
        info = z.infolist()
        # mimetype must come first and be stored uncompressed
        assert info[0].filename == "mimetype"
        assert info[0].compress_type == zipfile.ZIP_STORED
        assert z.read("mimetype").decode() == \
            "application/vnd.adobe.indesign-idml-package"

        names = z.namelist()
        for required in ("designmap.xml", "META-INF/container.xml",
                         "Resources/Graphic.xml", "Resources/Styles.xml",
                         "MasterSpreads/MasterSpread_master.xml"):
            assert required in names

        # every designmap reference resolves
        dm = z.read("designmap.xml").decode()
        root = ET.fromstring(dm[dm.index("<Document"):])
        for el in root:
            src = el.get("src")
            if src:
                assert src in names, f"dangling designmap ref {src}"


def test_build_idml_frames_carry_source_text(sample_pdf, tmp_path):
    out = str(tmp_path / "out.idml")
    build_idml(sample_pdf, out, backgrounds=False)

    with zipfile.ZipFile(out) as z:
        text = " ".join(
            (c.text or "")
            for n in z.namelist() if n.startswith("Stories/")
            for c in ET.fromstring(z.read(n)).iter()
            if c.tag.endswith("Content")
        )
    assert "Solve each problem" in text
    assert "Second page body text." in text


def test_build_idml_geometry_matches_source_bbox(sample_pdf, tmp_path):
    """A frame must land exactly on the bbox of the line it came from."""
    out = str(tmp_path / "out.idml")
    build_idml(sample_pdf, out, backgrounds=False)

    lines = extract_lines(sample_pdf)
    wanted = {
        ln.raw_text.strip(): ln.bbox for ln in lines if ln.raw_text.strip()
    }

    def local(el) -> str:
        # "{ns}Story" -> "Story"; plain "Story" -> "Story". Note idPkg:Story (the
        # package root) and Story (the content node) both end in "Story".
        return el.tag.rsplit("}", 1)[-1]

    with zipfile.ZipFile(out) as z:
        stories = {}
        for n in z.namelist():
            if n.startswith("Stories/"):
                root = ET.fromstring(z.read(n))
                # the idPkg:Story package root shares the localname "Story"
                # with the content node; only the latter carries Self
                story = next(e for e in root.iter()
                             if local(e) == "Story" and e.get("Self"))
                stories[story.get("Self")] = "".join(
                    (c.text or "") for c in root.iter() if local(c) == "Content"
                ).strip()

        checked = 0
        for n in sorted(x for x in z.namelist() if x.startswith("Spreads/")):
            root = ET.fromstring(z.read(n))
            page = next(e for e in root.iter() if local(e) == "Page")
            _, _, height, width = [float(v) for v in page.get("GeometricBounds").split()]

            for tf in (e for e in root.iter() if local(e) == "TextFrame"):
                body = stories.get(tf.get("ParentStory"), "")
                if body not in wanted:
                    continue
                tr = [float(v) for v in tf.get("ItemTransform").split()]
                xs, ys = [], []
                for pt in tf.iter():
                    if local(pt) == "PathPointType":
                        ax, ay = [float(a) for a in pt.get("Anchor").split()]
                        xs.append(ax)
                        ys.append(ay)
                # single-page spread: page-space = spread-space + (W/2, H/2)
                got = (
                    tr[4] + min(xs) + width / 2.0,
                    tr[5] + min(ys) + height / 2.0,
                    tr[4] + max(xs) + width / 2.0,
                    tr[5] + max(ys) + height / 2.0,
                )
                expected = wanted[body]
                assert max(abs(g - e) for g, e in zip(got, expected)) < 0.05
                checked += 1
        assert checked >= 2


def test_build_idml_backgrounds_written(sample_pdf, tmp_path):
    out = str(tmp_path / "bg.idml")
    result = build_idml(sample_pdf, out, backgrounds=True)
    assert result["backgrounds"] == 2
    assert os.path.isdir(result["asset_dir"])
    assert len(os.listdir(result["asset_dir"])) == 2


# --- preview --------------------------------------------------------------

def test_preview_renders_every_page_and_frame(sample_pdf, tmp_path):
    idml = str(tmp_path / "p.idml")
    build_idml(sample_pdf, idml, backgrounds=True)

    preview = str(tmp_path / "p.preview.pdf")
    stats = render_idml(idml, preview)

    assert stats["pages"] == 2
    assert stats["frames"] >= 3
    assert stats["images"] == 2          # one background per page
    assert stats["missing_images"] == 0

    doc = fitz.open(preview)
    try:
        assert "Solve each problem" in doc.load_page(0).get_text()
    finally:
        doc.close()


def test_preview_compresses_page_backgrounds(sample_pdf, tmp_path):
    """Backgrounds are full-page bitmaps; saved without deflate PyMuPDF stores
    them as raw RGB (~11 MB per US-Letter page at 200dpi)."""
    idml = str(tmp_path / "big.idml")
    build_idml(sample_pdf, idml, backgrounds=True)

    preview = str(tmp_path / "big.preview.pdf")
    render_idml(idml, preview)

    raw_rgb_per_page = 612 / 72 * 200 * (792 / 72 * 200) * 3
    assert os.path.getsize(preview) < raw_rgb_per_page  # 2 pages, must beat 1


# --- OCR ------------------------------------------------------------------

def test_ocr_falls_back_to_local_engine_without_credentials(monkeypatch):
    """No Google keys must not mean no OCR — the local engine takes over."""
    from babel.ingest import ocr as ocr_mod

    for var in ("DOCAI_PROJECT_ID", "DOCAI_PROCESSOR_ID",
                "GOOGLE_APPLICATION_CREDENTIALS"):
        monkeypatch.delenv(var, raising=False)

    assert not ocr_mod.docai_status()

    monkeypatch.setattr(ocr_mod, "rapidocr_available", lambda: True)
    assert ocr_mod.active_ocr_engine() == "rapidocr"
    assert ocr_mod.ocr_status()          # usable overall

    monkeypatch.setattr(ocr_mod, "rapidocr_available", lambda: False)
    assert ocr_mod.active_ocr_engine() == "none"
    assert not ocr_mod.ocr_status()


def test_ocr_reports_reason_when_nothing_is_available(sample_pdf, monkeypatch):
    from babel.ingest import ocr as ocr_mod

    for var in ("DOCAI_PROJECT_ID", "DOCAI_PROCESSOR_ID",
                "GOOGLE_APPLICATION_CREDENTIALS"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(ocr_mod, "rapidocr_available", lambda: False)

    lines, note = ocr_mod.ocr_pages(sample_pdf)
    assert lines == []
    assert "skipped" in note


def test_ocr_prefers_vision_over_http_and_rapidocr_when_docai_absent(monkeypatch):
    """Vision slots in ahead of http/rapidocr once its own creds are present."""
    from babel.ingest import ocr as ocr_mod

    for var in ("DOCAI_PROJECT_ID", "DOCAI_PROCESSOR_ID"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/fake-creds.json")
    monkeypatch.setattr(ocr_mod, "_vision_importable", lambda: True)
    monkeypatch.setattr(ocr_mod, "rapidocr_available", lambda: True)

    assert ocr_mod.vision_status()
    assert ocr_mod.active_ocr_engine() == "vision"


def test_ocr_falls_back_past_vision_without_credentials(monkeypatch):
    from babel.ingest import ocr as ocr_mod

    for var in ("DOCAI_PROJECT_ID", "DOCAI_PROCESSOR_ID", "GOOGLE_APPLICATION_CREDENTIALS"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(ocr_mod, "rapidocr_available", lambda: True)

    assert not ocr_mod.vision_status()
    assert ocr_mod.active_ocr_engine() == "rapidocr"


def test_parse_vision_response_converts_pixel_bbox_to_pdf_points():
    from babel.ingest import ocr as ocr_mod

    class _Vertex:
        def __init__(self, x, y):
            self.x, self.y = x, y

    class _Box:
        def __init__(self, verts):
            self.vertices = verts

    class _Symbol:
        def __init__(self, text):
            self.text = text

    class _Word:
        def __init__(self, text):
            self.symbols = [_Symbol(text)]

    class _Paragraph:
        def __init__(self, words, verts, confidence):
            self.words = [_Word(w) for w in words]
            self.bounding_box = _Box(verts)
            self.confidence = confidence

    class _Block:
        def __init__(self, paragraphs):
            self.paragraphs = paragraphs

    class _Page:
        def __init__(self, blocks):
            self.blocks = blocks

    class _Annotation:
        def __init__(self, pages):
            self.pages = pages

    class _Response:
        def __init__(self, annotation):
            self.full_text_annotation = annotation

    # 200 dpi crop, "GO!" spans pixels (100,100)-(300,180) -> 72/200 scale
    verts = [_Vertex(100, 100), _Vertex(300, 100), _Vertex(300, 180), _Vertex(100, 180)]
    paragraph = _Paragraph(["GO!"], verts, confidence=0.95)
    response = _Response(_Annotation([_Page([_Block([paragraph])])]))

    lines = ocr_mod._parse_vision_response(
        response, page=3, clip=fitz.Rect(50, 60, 400, 400), dpi=200
    )

    assert len(lines) == 1
    ln = lines[0]
    assert ln.page == 3
    assert ln.spans[0].text == "GO!"
    assert ln.from_ocr is True
    assert ln.ocr_confidence == pytest.approx(0.95)
    expected_x0 = 50 + 100 * 72.0 / 200
    expected_y0 = 60 + 100 * 72.0 / 200
    assert ln.bbox[0] == pytest.approx(expected_x0)
    assert ln.bbox[1] == pytest.approx(expected_y0)


def test_detect_image_regions_catches_small_banner_but_not_noise(tmp_path):
    """A decorative banner/badge graphic (a "GO!" arrow, ~65x70pt = 4550pt^2)
    must not be filtered out with the diagram-sized art the threshold was
    built for — but a 1-2pt spacer image should still be dropped as noise."""
    src = fitz.open()
    page = src.new_page(width=400, height=400)

    banner_pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 65, 70))
    banner_pix.set_rect(banner_pix.irect, (150, 30, 100))
    page.insert_image(fitz.Rect(300, 10, 365, 80), pixmap=banner_pix)

    noise_pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 2, 2))
    noise_pix.set_rect(noise_pix.irect, (0, 0, 0))
    page.insert_image(fitz.Rect(0, 0, 2, 2), pixmap=noise_pix)

    path = str(tmp_path / "banner.pdf")
    src.save(path)
    src.close()

    regions = detect_image_regions(path)
    assert 0 in regions
    areas = [fitz.Rect(r).get_area() for r in regions[0]]
    assert any(3000 <= a <= 6000 for a in areas)  # banner made it through
    assert not any(a < 100 for a in areas)          # noise still filtered


def test_billing_retry_succeeds_after_transient_failures(monkeypatch):
    """Google's own billing-enabled check has a short propagation cache — a
    call can fail with BILLING_DISABLED for a few seconds after billing was
    actually turned on. Retry through that window instead of failing the job."""
    from babel.ingest import ocr as ocr_mod
    monkeypatch.setattr(ocr_mod.time, "sleep", lambda s: None)

    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("403 ... [reason: \"BILLING_DISABLED\" ...]")
        return "ok"

    assert ocr_mod._call_with_billing_retry(flaky, attempts=3, delay=0) == "ok"
    assert calls["n"] == 3


def test_billing_retry_gives_up_after_max_attempts(monkeypatch):
    from babel.ingest import ocr as ocr_mod
    monkeypatch.setattr(ocr_mod.time, "sleep", lambda s: None)

    def always_billing_disabled():
        raise RuntimeError("BILLING_DISABLED")

    with pytest.raises(RuntimeError):
        ocr_mod._call_with_billing_retry(always_billing_disabled, attempts=2, delay=0)


def test_billing_retry_does_not_retry_unrelated_errors(monkeypatch):
    from babel.ingest import ocr as ocr_mod

    calls = {"n": 0}

    def fails_for_another_reason():
        calls["n"] += 1
        raise ValueError("malformed image")

    with pytest.raises(ValueError):
        ocr_mod._call_with_billing_retry(fails_for_another_reason, attempts=5, delay=0)
    assert calls["n"] == 1  # no retry for a non-billing error


def test_sample_foreground_color_finds_white_text_on_purple_banner():
    """OCR gives text + bbox only, no font/color metadata — the reassembly
    path needs *some* color, and hardcoded black is wrong on a colored banner
    (white-on-purple 'GO!' badge). Sample it from the source pixels instead."""
    from babel.ingest.ocr import _sample_foreground_color

    doc = fitz.open()
    page = doc.new_page(width=100, height=100)
    page.draw_rect(fitz.Rect(10, 10, 90, 90), color=None, fill=(0.6, 0.1, 0.6))
    # a white "glyph" block sitting inside the purple banner
    page.draw_rect(fitz.Rect(30, 30, 70, 70), color=None, fill=(1, 1, 1))

    color = _sample_foreground_color(page, fitz.Rect(20, 20, 80, 80))
    assert color is not None
    r, g, b = (color >> 16 & 255), (color >> 8 & 255), (color & 255)
    assert r > 200 and g > 200 and b > 200  # white, not the purple background


def test_ocr_image_regions_colors_lines_from_the_source_pixels(tmp_path, monkeypatch):
    """The color sampled off the banner must actually reach the returned
    Line, not just exist as an unused helper function."""
    from babel.ingest import ocr as ocr_mod

    if not ocr_mod.rapidocr_available():
        pytest.skip("rapidocr not installed in this environment")
    monkeypatch.setattr(ocr_mod, "active_ocr_engine", lambda: "rapidocr")

    doc = fitz.open()
    page = doc.new_page(width=200, height=100)
    page.draw_rect(fitz.Rect(10, 10, 190, 90), color=None, fill=(0.6, 0.1, 0.6))
    page.insert_text((30, 60), "GO", fontsize=36, fontname="hebo", color=(1, 1, 1))
    path = str(tmp_path / "banner.pdf")
    doc.save(path)
    doc.close()

    lines, _note = ocr_mod.ocr_image_regions(path, regions={0: [(10, 10, 190, 90)]})
    assert lines
    colored = [ln for ln in lines if ln.spans[0].color != 0]
    assert colored  # at least one line got a non-black (sampled) color
    r = colored[0].spans[0].color >> 16 & 255
    assert r > 200  # sampled white, not the purple fill


def test_pad_bbox_grows_by_margin_of_height():
    from babel.ingest.ocr import _pad_bbox

    bbox = (100.0, 50.0, 150.0, 70.0)  # height 20
    padded = _pad_bbox(bbox, fraction=0.2)  # 4pt margin
    assert padded == pytest.approx((96.0, 46.0, 154.0, 74.0))


def test_ocr_image_regions_pads_bboxes_so_redaction_clears_the_full_glyph(tmp_path, monkeypatch):
    """A tight OCR bbox that clips the top of an ascender or an exclamation
    mark's dot leaves a sliver of the original English visible under the
    translation — the exact overlap this test guards against."""
    from babel.ingest import ocr as ocr_mod

    if not ocr_mod.rapidocr_available():
        pytest.skip("rapidocr not installed in this environment")
    monkeypatch.setattr(ocr_mod, "active_ocr_engine", lambda: "rapidocr")

    doc = fitz.open()
    page = doc.new_page(width=200, height=100)
    page.draw_rect(fitz.Rect(10, 10, 190, 90), color=None, fill=(0.6, 0.1, 0.6))
    page.insert_text((30, 65), "GO!", fontsize=40, fontname="hebo", color=(1, 1, 1))
    path = str(tmp_path / "banner3.pdf")
    doc.save(path)
    doc.close()

    clip = fitz.Rect(10, 10, 190, 90)
    png = fitz.open(path).load_page(0).get_pixmap(clip=clip, dpi=300).tobytes("png")
    raw_lines = ocr_mod._rapidocr_lines(png, 0, clip, 300)
    assert raw_lines
    raw_bbox = raw_lines[0].bbox

    lines, _note = ocr_mod.ocr_image_regions(path, regions={0: [(10, 10, 190, 90)]})
    assert lines
    padded_bbox = lines[0].bbox
    # padded box must fully contain the raw OCR box, not just equal it
    assert padded_bbox[0] <= raw_bbox[0] and padded_bbox[1] <= raw_bbox[1]
    assert padded_bbox[2] >= raw_bbox[2] and padded_bbox[3] >= raw_bbox[3]
    assert padded_bbox != raw_bbox


def test_detect_scanned_pages_finds_image_only_page(tmp_path):
    src = fitz.open()
    text_page = src.new_page(width=300, height=300)
    text_page.insert_text((30, 60), "plenty of real selectable text here to pass", fontsize=11)
    pix = text_page.get_pixmap(dpi=72)

    scanned = src.new_page(width=300, height=300)
    scanned.insert_image(scanned.rect, pixmap=pix)

    path = str(tmp_path / "mixed.pdf")
    src.save(path)
    src.close()

    assert detect_scanned_pages(path) == [1]
    assert 1 in detect_image_regions(path)


# --- equations ------------------------------------------------------------

def test_looks_like_math_discriminates(sample_pdf):
    lines = extract_lines(sample_pdf)
    by_text = {ln.raw_text.strip(): ln for ln in lines}
    assert looks_like_math(by_text["3 x 4 = 12"])
    assert not looks_like_math(by_text["Solve each problem. Show your work."])


def test_badge_spans_are_excluded_from_equation_crops(tmp_path):
    """Problem numbers are white knockout glyphs on a dark disc. Including them
    makes the recogniser emit \\oplus / \\stackrel noise for the badge."""
    from babel.models import Line, Span
    from babel.protect.equations import (content_bbox, content_text,
                                         is_badge_span)

    badge = Span(text="1", font="MyriadPro-Semibold", size=11.0,
                 color=0xFFFFFF, bbox=(86.5, 165.0, 92.0, 180.0))
    body = Span(text=" 6", font="MyriadPro-Regular", size=12.0,
                color=0x000000, bbox=(97.4, 165.0, 110.0, 180.0))

    assert is_badge_span(badge)
    assert not is_badge_span(body)

    line = Line(page=0, bbox=(86.5, 165.0, 110.0, 180.0), spans=[badge, body])
    assert content_text(line) == "6"
    assert content_bbox(line)[0] == 97.4       # starts after the badge


def test_pix2tex_renders_smaller_than_mathpix():
    """pix2tex degrades badly on large glyphs; Mathpix improves with detail.
    Measured: at 400dpi '6^4*6^4' comes back as \\textstyle\\bigcap\\cdots."""
    from babel.protect.equations import MATHPIX_DPI, PIX2TEX_DPI

    assert PIX2TEX_DPI < MATHPIX_DPI


def test_structural_engine_leads_and_env_can_force(monkeypatch):
    """Reading the PDF's own layout is exact and free, so it goes first."""
    from babel.protect import equations

    monkeypatch.delenv("BABEL_EQUATION_ENGINE", raising=False)
    monkeypatch.setenv("MATHPIX_APP_ID", "id")
    monkeypatch.setenv("MATHPIX_APP_KEY", "key")
    assert equations.active_engine() == "structural"

    monkeypatch.setenv("BABEL_EQUATION_ENGINE", "pix2tex")
    assert equations.active_engine() == "pix2tex"


def test_fallback_prefers_mathpix_then_pix2tex(monkeypatch):
    from babel.protect import equations

    monkeypatch.setenv("MATHPIX_APP_ID", "id")
    monkeypatch.setenv("MATHPIX_APP_KEY", "key")
    assert equations._fallback_engine() == "mathpix"

    monkeypatch.delenv("MATHPIX_APP_ID")
    monkeypatch.delenv("MATHPIX_APP_KEY")
    monkeypatch.setattr(equations, "pix2tex_available", lambda: True)
    assert equations._fallback_engine() == "pix2tex"

    monkeypatch.setattr(equations, "pix2tex_available", lambda: False)
    assert equations._fallback_engine() == "none"


def test_structural_builder_reads_superscripts_and_operators():
    """The glyph tables and script detection, on synthetic spans."""
    from babel.models import Line, Span
    from babel.protect.latex_builder import build_latex

    # "6^4 x 10^1" as the PDF encodes it: MathematicalPiLTStd-1 '3' draws a
    # multiplication cross, and exponents are smaller spans sitting higher.
    spans = [
        Span(text="6", font="MyriadPro-Regular", size=12.0, color=0,
             bbox=(10, 100, 17, 112)),
        Span(text="4", font="MyriadPro-Regular", size=8.4, color=0,
             bbox=(17, 96, 22, 105)),
        Span(text="3", font="MathematicalPiLTStd-1", size=12.0, color=0,
             bbox=(24, 100, 32, 112)),
        Span(text="10", font="MyriadPro-Regular", size=12.0, color=0,
             bbox=(34, 100, 47, 112)),
        Span(text="1", font="MyriadPro-Regular", size=8.4, color=0,
             bbox=(47, 96, 52, 105)),
    ]
    latex = build_latex([Line(page=0, bbox=(10, 96, 52, 112), spans=spans)])
    assert latex == r"6^{4}\times10^{1}"


def test_detect_regions_returns_boxed_equation(sample_pdf):
    lines = extract_lines(sample_pdf)
    regions = detect_regions(sample_pdf, lines)
    assert len(regions) >= 1
    region = regions[0]
    assert region.page == 0
    assert region.bbox[2] > region.bbox[0]
    assert "4" in region.raw_text


# --- editorial rule -------------------------------------------------------

@pytest.mark.parametrize(
    "source,target,ok",
    [
        ("one line", "una linea", True),
        ("a\nb", "x\ny", True),
        ("a\nb", "x\ny\nz", False),                       # gained a line
        ("short", "a" * 100, False),                       # will wrap
        ("Add the numbers", "Suma los numeros", True),     # normal ES expansion
    ],
)
def test_line_count_rule(source, target, ok):
    assert line_count_ok(source, target)[0] is ok


def test_line_count_failure_explains_why():
    ok, why = line_count_ok("a\nb", "x\ny\nz")
    assert not ok
    assert "2 -> 3" in why
