"""Image translation, end to end.

    validation ─► OCR ─► classification ─► translation ─► reconstruction ─► quality

`translate_image` is the whole pipeline; the API runs it in a background task
and persists each `progress` call, the CLI and the tests call it directly. It
never touches `pagebirdy.pipeline` — the document paths do not know it exists.
"""

from __future__ import annotations

import io
import logging
import math
import os
import time
from collections import Counter
from dataclasses import dataclass
from typing import Callable

import numpy as np
from PIL import Image

from pagebirdy import languages
from pagebirdy.image import background, rtl
from pagebirdy.image.classify import classify
from pagebirdy.image.fit import fit_text
from pagebirdy.image.ocr import OcrError, ocr_engine, run_ocr
from pagebirdy.image.quality import run_checks, verify_with_ocr
from pagebirdy.image.regions import TextRegion
from pagebirdy.image.render import (Style, composite, coverage, estimate_font_px, font_set,
                                looks_bold, missing_glyphs)
from pagebirdy.image.translate import translate_regions
from pagebirdy.image.validate import ImageValidationError, validate_image_bytes

logger = logging.getLogger("pagebirdy.image.pipeline")

# (key, label) in run order — the UI renders this list as the progress steps.
STAGES = [
    ("uploading", "Uploading"),
    ("validation", "Validating image"),
    ("ocr", "Reading text (OCR)"),
    ("classification", "Classifying text"),
    ("translation", "Translating"),
    ("reconstruction", "Reconstructing image"),
    ("quality", "Quality check"),
    ("completed", "Completed"),
]

Progress = Callable[[str, float, str], None]


class ImageTranslationError(Exception):
    """A failure whose message is safe to show the user, tagged with its stage."""

    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage


def verify_enabled() -> bool:
    return os.getenv("BABEL_IMAGE_VERIFY_OCR", "1").lower() not in ("0", "false", "no", "off")


# --- geometry -----------------------------------------------------------------


def _work_boxes(regions: list[TextRegion], draw: list[TextRegion],
                width: int, height: int) -> dict[str, tuple[int, int, int, int]]:
    """The pixel box each redrawn region may rewrite: its OCR box grown to the
    line box the type sat in.

    OCR boxes hug the ink, and a line of type needs its leading too — without
    it, text the same size as the source would not fit the source's own box.
    The growth stops halfway to any neighbouring region, so two boxes never
    overlap and a protected region's pixels are never touched.
    """
    out = {}
    for r in draw:
        px = float(r.render["font_px"])
        x0, y0, x1, y1 = r.bbox
        gx0, gy0 = x0 - 0.12 * px, y0 - 0.22 * px
        gx1, gy1 = x1 + 0.12 * px, y1 + 0.22 * px
        for o in regions:
            if o is r:
                continue
            ox0, oy0, ox1, oy1 = o.bbox
            if oy0 < y1 and oy1 > y0:  # beside us
                if ox1 <= x0:
                    gx0 = max(gx0, (ox1 + x0) / 2)
                elif ox0 >= x1:
                    gx1 = min(gx1, (x1 + ox0) / 2)
            if ox0 < x1 and ox1 > x0:  # above or below us
                if oy1 <= y0:
                    gy0 = max(gy0, (oy1 + y0) / 2)
                elif oy0 >= y1:
                    gy1 = min(gy1, (y1 + oy0) / 2)
        box = (max(0, math.floor(gx0)), max(0, math.floor(gy0)),
               min(width, math.ceil(gx1)), min(height, math.ceil(gy1)))
        if box[2] - box[0] >= 2 and box[3] - box[1] >= 2:
            out[r.id] = box
    return out


def source_alignment(r: TextRegion, image_width: int) -> str:
    """How the source set its lines: left, right or centre.

    Several lines tell by which edge they share. One line has no edge to
    share, so it reads as centred only when it sits on the image's own centre
    line — a banner, a title — and as left otherwise.
    """
    if len(r.lines) >= 2:
        def spread(vals):
            return float(np.std(vals))
        lefts = spread([b[0] for b in r.lines])
        rights = spread([b[2] for b in r.lines])
        centres = spread([(b[0] + b[2]) / 2 for b in r.lines])
        best = min((lefts, "left"), (centres, "center"), (rights, "right"))
        return best[1]
    centre = (r.bbox[0] + r.bbox[2]) / 2
    return "center" if abs(centre - image_width / 2) <= 0.03 * image_width else "left"


# --- output -------------------------------------------------------------------


def _save(img: Image.Image, path, fmt: str, info: dict, from_source: bool) -> str:
    """Write in the source's own format; returns a note on how.

    JPEG reuses the source's own quantisation tables and chroma subsampling
    when the pixels were pasted back into the decoded JPEG itself, so the
    re-encode costs as little as a JPEG re-encode can. WEBP is written
    lossless, so it degrades nothing further.
    """
    extra = {k: info[k] for k in ("icc_profile", "exif", "dpi") if info.get(k)}
    if fmt == "JPEG":
        if from_source:
            try:
                img.save(path, "JPEG", quality="keep", subsampling="keep", qtables="keep", **extra)
                return "JPEG re-encoded with the source's own quality tables"
            except (ValueError, OSError):
                pass
        img.convert("RGB").save(path, "JPEG", quality=95, **extra)
        return "JPEG re-encoded at quality 95"
    if fmt == "WEBP":
        img.save(path, "WEBP", lossless=True, exact=True, **extra)
        return "WEBP written lossless"
    img.save(path, "PNG", **extra)
    return "PNG (lossless)"


def _load_raster(data: bytes, meta) -> Image.Image:
    """The pixels to translate. A PSD is flattened to its composite — what
    Photoshop shows — with psd-tools, as `idml/graphics.py` does for a linked
    .psd."""
    if meta.format == "PSD":
        from psd_tools import PSDImage

        img = PSDImage.open(io.BytesIO(data)).composite()
        return img if img.mode in ("RGB", "RGBA") else img.convert("RGBA")
    img = Image.open(io.BytesIO(data))
    img.load()
    return img


def _translate_vector(src_path, out_path, meta, lang, *, source_lang, emit,
                      engines, started) -> tuple[dict, list]:
    from pagebirdy.image.vector import translate_vector

    report: dict = {
        "format": "image", "source": src_path, "output": out_path,
        "input_format": meta.format, "output_format": meta.format,
        "width": meta.width, "height": meta.height, "units": "pt", "artboards": meta.pages,
        "source_lang": source_lang, "target_lang": lang.code,
        "target_language": lang.name, "direction": lang.direction,
        "ocr_engine": "vision+live text", "warnings": [],
    }

    def warn(region, message):
        report["warnings"].append({"region": region, "message": message})

    try:
        partial, segments = translate_vector(src_path, out_path, lang,
                                             emit=emit, engines=engines, warn=warn)
    except Exception as e:  # noqa: BLE001 — never leak a PyMuPDF/provider trace to the user
        logger.exception("vector translation failed")
        raise ImageTranslationError("reconstruction",
                                    "The Illustrator file could not be translated.") from e
    report.update(partial)
    emit("quality", 100, "passed" if report["quality"]["passed"] else "issues found")
    for r in report["regions"]:
        for message in r["warnings"]:
            warn(r["id"], message)
    report.update({
        "status_counts": dict(Counter(r["status"] for r in report["regions"])),
        "content_counts": dict(Counter(r["content_type"] for r in report["regions"])),
        "verification": {"ran": False},
        "duration_sec": round(time.time() - started, 2),
    })
    return report, segments


# --- phases -------------------------------------------------------------------
# `translate_image` runs these back to back. They are separate so a caller that
# keeps its own segments — an office document holding pictures, whose image
# text is reviewed with the rest of the document — can OCR now and redraw
# later, from whatever targets review left, without translating here.


def classify_regions(regions: list[TextRegion], lang, source_lang: str = "en") -> None:
    """Classify `regions` in place and estimate each one's type size."""
    classify(regions)
    fonts = font_set(lang)
    if not fonts.regular:
        raise ImageTranslationError("reconstruction",
                                    f"No font is installed that can draw {lang.name}.")
    for r in regions:
        r.render["font_px"] = round(estimate_font_px(r.text, r.lines, fonts), 2)
        if r.language and r.language not in ("und", source_lang) \
                and not r.language.startswith(source_lang + "-") and r.action == "translate":
            r.warnings.append(f"OCR detected language '{r.language}', not '{source_lang}'")


def analyze_raster(work: Image.Image, lang, *, source_lang: str = "en",
                   ocr: Callable | None = None) -> list[TextRegion]:
    """OCR then classify: every region, with its action and type size.
    An `OcrError` propagates."""
    regions = (ocr or (lambda im: run_ocr(im)[0]))(work)
    if regions:
        classify_regions(regions, lang, source_lang)
    return regions


def work_image(img: Image.Image) -> Image.Image:
    """`img` in the mode every stage reads: RGBA if it has any transparency."""
    mode = "RGBA" if ("A" in img.getbands() or "transparency" in img.info) else "RGB"
    return img.convert(mode)


@dataclass
class RenderResult:
    final: Image.Image          # what to save: the source with rewritten boxes pasted in
    rendered: Image.Image       # the whole working-mode render (verification OCR reads it)
    from_source: bool           # `final` is the decoded source itself (JPEG tables kept)
    drawn_boxes: dict[str, tuple[int, int, int, int]]
    quality: dict
    mode_note: str | None = None


def render_raster(img: Image.Image, regions: list[TextRegion], segments: dict, lang, *,
                  paste_back: bool = True,
                  emit: Callable[[float, str], None] | None = None) -> RenderResult:
    """Redraw every region marked `translate` whose `target` is set and whose
    segment is in `segments` (region id → `Segment`), then run the quality
    checks. Nothing is translated here; a region it cannot redraw keeps its
    original pixels and says why in `r.warnings`."""
    work = work_image(img)
    original = np.asarray(work, dtype=np.float32)
    height, width = original.shape[:2]
    fonts = font_set(lang)
    draw = [r for r in regions if r.action == "translate" and r.target and r.id in segments]
    boxes = _work_boxes(regions, draw, width, height)
    output = original.copy()
    drawn_boxes: dict[str, tuple[int, int, int, int]] = {}
    for i, r in enumerate(draw, 1):
        box = boxes.get(r.id)
        if box is None:
            r.warnings.append("Region too small to redraw; original text kept")
            continue
        x0, y0, x1, y1 = box
        try:
            recon = background.reconstruct(original, box, r.line_height)
            style_info = background.text_style(original[y0:y1, x0:x1], recon.patch)
            text = rtl.restore_target(segments[r.id], lang)
            missing = missing_glyphs(text, fonts)
            if missing:
                r.warnings.append(f"Font cannot draw {missing!r}; a fallback face was used")
            w, h = x1 - x0, y1 - y0
            bold = looks_bold(r.text, w, h, fonts, float(r.render["font_px"]), style_info["stroke"])
            style = Style(fonts=fonts, bold=bold,
                          align=rtl.alignment(source_alignment(r, width), lang),
                          direction=rtl.direction(lang))
            fit = fit_text(text, w, h, style, float(r.render["font_px"]))
            mask = coverage(text, w, h, style, fit.font_px, fit.line_height, force=fit.forced)
        except Exception:  # noqa: BLE001
            logger.exception("image translation: rendering failed for %s", r.id)
            r.warnings.append("Rendering failed; original text kept")
            continue
        output[y0:y1, x0:x1] = composite(output[y0:y1, x0:x1], recon.patch, mask,
                                         style_info["color"])
        drawn_boxes[r.id] = box
        r.render.update({
            "drawn": True, "box": list(box), "fit": fit.to_dict(),
            "inside_box": True, "ink_pixels": int(np.count_nonzero(mask > 0.25)),
            "align": style.align, "direction": style.direction, "bold": style.bold,
            "color": "#%02x%02x%02x" % tuple(style_info["color"][:3]),
            "background": recon.strategy, "ring_std": round(recon.ring_std, 1),
            "roughness": round(recon.roughness, 2),
        })
        if fit.forced:
            r.warnings.append("Translation is much longer than the source and was "
                              "scaled below the minimum size to fit")
        elif fit.shrunk:
            r.notes.append(f"set at {fit.font_px:.1f}px (source {fit.natural_px:.1f}px) to fit")
        if recon.textured:
            r.warnings.append("Busy background behind this text; the patch may be visible")
        if emit:
            emit(100 * i / len(draw), f"{i} of {len(draw)}")

    out_u8 = np.clip(np.rint(output), 0, 255).astype(np.uint8)
    orig_u8 = np.asarray(work, dtype=np.uint8)
    quality = run_checks(orig_u8, out_u8, regions, drawn_boxes)

    # Mode follows from the array's shape (H×W×3 → RGB, H×W×4 → RGBA); the
    # explicit `mode` argument is gone in Pillow 13.
    rendered = Image.fromarray(out_u8)
    if paste_back and img.mode in ("RGB", "RGBA", "L", "LA", "CMYK"):
        # Paste only the rewritten boxes back into the decoded source, in its
        # own mode, so every other pixel is the source's own.
        for x0, y0, x1, y1 in drawn_boxes.values():
            img.paste(rendered.crop((x0, y0, x1, y1)).convert(img.mode), (x0, y0))
        return RenderResult(img, rendered, True, drawn_boxes, quality)
    return RenderResult(rendered, rendered, False, drawn_boxes, quality,
                        f"Image mode {img.mode} was written as {work.mode}.")


def encode_like_source(final: Image.Image, fmt: str, info: dict,
                       from_source: bool) -> tuple[bytes, str]:
    """`final` encoded as `_save` writes it to disk; returns (bytes, note)."""
    buf = io.BytesIO()
    note = _save(final, buf, fmt, info, from_source)
    return buf.getvalue(), note


# --- pipeline -----------------------------------------------------------------


def translate_image(
    src_path: str,
    out_dir: str,
    target_lang: str,
    *,
    source_lang: str = "en",
    progress: Progress | None = None,
    engines=None,
    ocr: Callable | None = None,
    verify: bool | None = None,
) -> tuple[dict, list]:
    """Translate the text in the image at `src_path`; returns (report, segments).

    `engines` and `ocr` exist for tests and offline runs; production passes
    neither and gets `build_engines` and Vision.
    """
    started = time.time()
    emit = progress or (lambda stage, pct, detail="": None)
    lang = languages.get(target_lang)
    os.makedirs(out_dir, exist_ok=True)

    # ---- validation ----
    emit("validation", 0, "")
    with open(src_path, "rb") as f:
        data = f.read()
    try:
        meta = validate_image_bytes(data)
    except ImageValidationError as e:
        raise ImageTranslationError("validation", str(e)) from None
    stem = os.path.splitext(os.path.basename(src_path))[0]
    out_path = os.path.join(out_dir, f"{stem}.{lang.code}{meta.output_extension}")

    if meta.kind == "vector":
        emit("validation", 100, f"{meta.format} {meta.width}×{meta.height}pt")
        return _translate_vector(src_path, out_path, meta, lang, source_lang=source_lang,
                                 emit=emit, engines=engines, started=started)

    try:
        img = _load_raster(data, meta)
    except Exception:  # noqa: BLE001
        raise ImageTranslationError("validation", "The image could not be decoded.") from None
    save_info = dict(img.info)
    work = work_image(img)
    width, height = work.size
    emit("validation", 100, f"{meta.format} {width}×{height}")
    # The format written back: the source's own, except a PSD, whose layers
    # cannot be written back — its composite is what was translated, as PNG.
    out_format = "PNG" if meta.format == "PSD" else meta.format

    # ---- OCR ----
    emit("ocr", 0, "")
    engine_name = "test" if ocr else ocr_engine()
    try:
        regions = (ocr or (lambda im: run_ocr(im)[0]))(work)
    except OcrError as e:
        raise ImageTranslationError("ocr", str(e)) from None
    emit("ocr", 100, f"{len(regions)} text region(s)")

    report: dict = {
        "format": "image",
        "source": src_path,
        "output": out_path,
        "input_format": meta.format,
        "output_format": out_format,
        "width": width,
        "height": height,
        "source_lang": source_lang,
        "target_lang": lang.code,
        "target_language": lang.name,
        "direction": lang.direction,
        "ocr_engine": engine_name,
        "warnings": [],
    }

    def warn(region: str | None, message: str) -> None:
        report["warnings"].append({"region": region, "message": message})

    if meta.format == "PSD":
        # Browsers cannot show a PSD; the composite is what the UI previews.
        report["source_preview"] = os.path.join(out_dir, f"{stem}.source.preview.png")
        img.save(report["source_preview"], "PNG")
        warn(None, "Photoshop layers were flattened: the translated image is a PNG of the "
                   "composite, not a layered PSD.")

    if not regions:
        # Nothing to translate: the deliverable is the source, byte for byte
        # (for a PSD, its composite).
        if meta.format == "PSD":
            img.save(out_path, "PNG")
        else:
            with open(out_path, "wb") as f:
                f.write(data)
        warn(None, "No text was detected in this image; the output is the original image.")
        emit("classification", 100, "")
        emit("translation", 100, "")
        emit("reconstruction", 100, "")
        emit("quality", 100, "")
        report.update({
            "regions": [], "status_counts": {}, "content_counts": {},
            "engine_primary": None, "engine_secondary": None, "engine_failures": [],
            "output_note": "unchanged copy of the source",
            "quality": {"passed": True, "checks": []}, "verification": {"ran": False},
            "duration_sec": round(time.time() - started, 2),
        })
        return report, []

    # ---- classification ----
    emit("classification", 0, "")
    classify_regions(regions, lang, source_lang)
    emit("classification", 100, f"{sum(r.action == 'translate' for r in regions)} to translate")

    # ---- translation ----
    emit("translation", 0, "")
    try:
        segments, engine_meta = translate_regions(regions, lang, engines=engines)
    except Exception as e:  # noqa: BLE001 — provider errors are not user-facing detail
        logger.exception("image translation: engine failure")
        raise ImageTranslationError("translation", "The translation service failed.") from e
    report.update(engine_meta)
    emit("translation", 100, f"{len(segments)} region(s)")

    # ---- reconstruction ----
    emit("reconstruction", 0, "")
    result = render_raster(img, regions, {s.id: s for s in segments}, lang,
                           paste_back=meta.format != "PSD",
                           emit=lambda pct, detail: emit("reconstruction", pct, detail))
    emit("reconstruction", 100, "")

    # ---- quality ----
    emit("quality", 0, "")
    quality, rendered, drawn_boxes = result.quality, result.rendered, result.drawn_boxes
    final, from_source = result.final, result.from_source
    if result.mode_note:
        warn(None, result.mode_note)
    report["output_note"] = _save(final, out_path, out_format, save_info, from_source)
    if meta.format == "PSD":
        report["output_note"] = "PNG of the flattened Photoshop composite"

    verification: dict = {"ran": False}
    if drawn_boxes and (verify if verify is not None else verify_enabled()) \
            and (ocr or engine_name != "none"):
        try:
            again = (ocr or (lambda im: run_ocr(im)[0]))(rendered)
            verification = verify_with_ocr(again, regions)
        except Exception as e:  # noqa: BLE001 — advisory only
            logger.info("image translation: verification OCR skipped: %s", e)
            verification = {"ran": False, "error": "verification OCR failed"}
    emit("quality", 100, "passed" if quality["passed"] else "issues found")

    for r in regions:
        for message in r.warnings:
            warn(r.id, message)
    report.update({
        "regions": [r.to_dict() for r in regions],
        "status_counts": dict(Counter(r.status for r in regions)),
        "content_counts": dict(Counter(r.content_type for r in regions)),
        "quality": quality,
        "verification": verification,
        "duration_sec": round(time.time() - started, 2),
    })
    return report, segments
