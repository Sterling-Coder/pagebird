"""End-to-end PDF translation pipeline + QA report.

    ingest -> protect math -> (TM + dual-engine translate + integrity gate)
           -> reassemble PDF -> QA report
"""

from __future__ import annotations

import logging
import os
from collections import Counter

import fitz

from babel import fonts as babel_fonts
from babel import languages
from babel.ingest.pdf import extract_lines
from babel.protect.mathguard import build_segments
from babel.reassemble.pdf import detect_graphic_pages, figure_pages, rebuild_pdf
from babel.tm.store import TranslationMemory
from babel.translate.engine import build_engines
from babel.translate.translator import Translator

logger = logging.getLogger("babel.pipeline")


def _doc_context(lines) -> str:
    """A one-line hint for the MT engine: the largest text near the top (title)."""
    top = [ln for ln in lines if ln.bbox[1] < 200]
    if not top:
        return ""
    title = max(top, key=lambda ln: ln.dominant.size)
    return title.raw_text.strip()[:120]


def translate_pdf(
    src_pdf: str,
    out_dir: str = "out",
    pages: list[int] | None = None,
    tm_path: str = "babel_tm.db",
    review_db: str | None = "babel_review.db",
    target_lang: str | None = None,
    with_ocr: bool = True,
    project_id: str | None = None,
    folder_id: str | None = None,
    original_filename: str | None = None,
    created_by: str | None = None,
) -> dict:
    import time
    _started = time.time()
    lang = languages.get(target_lang)
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src_pdf))[0]
    out_pdf = os.path.join(out_dir, f"{base}.{lang.code}.pdf")

    lines = extract_lines(src_pdf, pages=pages)

    # Text baked into a graphic's pixels (a banner, callout) has no PDF text
    # object for extract_lines to find — OCR the raster images and fold the
    # recovered lines in before segmentation, same as any other line.
    if with_ocr:
        from babel.ingest.ocr import merge_ocr_lines, ocr_image_regions

        img_lines, note = ocr_image_regions(src_pdf)
        logger.info("image-OCR: %s", note)
        for ln in img_lines:
            logger.info("image-OCR line: page=%s bbox=%s text=%r",
                       ln.page, ln.bbox, ln.raw_text.strip())
        merged = merge_ocr_lines(lines, img_lines)
        logger.info("image-OCR: %d/%d lines kept after dedup", len(merged) - len(lines), len(img_lines))
        lines = merged

    segments = build_segments(lines)

    primary, secondary = build_engines(doc_context=_doc_context(lines), target_lang=lang.code)
    # The TM is keyed per language pair, so switching target never returns a
    # translation in the previous language.
    tm = TranslationMemory(tm_path, tgt_lang=lang.code)
    try:
        Translator(primary, secondary, tm, target_lang=lang.code).run(segments)
    finally:
        tm.close()

    from babel.translate.verify import build_verifier, run_verification

    verifier = build_verifier(target_lang=lang.code)
    verify_flagged = run_verification(segments, verifier)

    outcomes = rebuild_pdf(src_pdf, segments, out_pdf, target_lang=lang.code)

    rtl = lang.direction == "rtl"
    doc = fitz.open(src_pdf)
    try:
        graphic_pages = detect_graphic_pages(doc)
        # Only a mirrored edition can invert a figure, so an LTR job has no
        # figure review queue to answer for.
        figures = figure_pages(doc) if rtl else []
    finally:
        doc.close()

    regular = babel_fonts.resolve(lang.fonts.get("regular", ())) or ""

    # After reassembly, so the text is still drawn — the page is rendered *and*
    # queued, rather than left blank for a reviewer to rebuild from scratch.
    for seg in segments:
        if seg.page in figures and seg.is_translatable:
            seg.status = "needs_human"
            seg.notes.append(
                "page mirrored for RTL and holds a figure; confirm no diagram, "
                "axis or number line was inverted"
            )

    status_counts = Counter(s.status for s in segments)
    action_counts = Counter(o.action for o in outcomes)
    needs_human = [
        {"id": s.id, "page": s.page, "source": s.source, "notes": s.notes}
        for s in segments
        if s.status == "needs_human"
    ]

    report = {
        "source": src_pdf,
        "output": out_pdf,
        "target_lang": lang.code,
        "target_language": lang.name,
        "direction": lang.direction,
        # An RTL edition mirrors the page: what sat against the left margin is
        # set against the right one.
        "mirrored": rtl,
        # Mirroring flips artwork content as well as position, so every page
        # holding a figure needs a human to confirm nothing turned around.
        "figure_pages": figures,
        "font_source": ("bundled" if babel_fonts.bundled(os.path.basename(regular))
                        else "system" if regular else "builtin"),
        "font_regular": regular,
        # Urdu is set in Naskh, not the Nastaliq its readers expect: MuPDF
        # renders Nastaliq faces blank. Legible and orthographically correct,
        # but visibly the wrong style — a reviewer should know before sign-off.
        "style_degraded": lang.code == "ur",
        "quality": "DRAFT — PDF reconstruction is lossy on tables/multi-box titles. "
                   "Use the IDML path for production fidelity.",
        "engine_primary": primary.name,
        "engine_secondary": secondary.name if secondary else None,
        # Non-empty means some chunks fell back to source text (bad key, no quota,
        # network). The job still completes; these segments need a re-run.
        "engine_failures": list(getattr(primary, "failures", []))[:10],
        "segments_total": len(segments),
        "lines_with_math": sum(1 for s in segments if s.placeholders),
        "status_counts": dict(status_counts),
        "reassembly_actions": dict(action_counts),
        "disagreements": sum(1 for s in segments if s.disagreement),
        "verifier": verifier.name if verifier else None,
        "verify_flagged": verify_flagged,
        "needs_human_count": len(needs_human),
        "graphic_pages": graphic_pages,
        "needs_human": needs_human[:200],
        "job_id": None,
        "overflow": [
            {"id": o.segment_id, "page": o.page, "detail": o.detail}
            for o in outcomes
            if o.action == "overflow"
        ],
    }

    if review_db:
        from babel.review.store import ReviewStore

        store = ReviewStore(review_db, tm_path=tm_path)
        try:
            report["job_id"] = store.save_job(
                src_pdf, out_pdf, segments,
                {
                    "engine_primary": primary.name,
                    "status_counts": dict(status_counts),
                    "graphic_pages": graphic_pages,
                    "target_lang": lang.code,
                    "target_language": lang.name,
                    "direction": lang.direction,
                    "figure_pages": figures,
                    "engine_failures": report["engine_failures"],
                    "disagreements": report["disagreements"],
                    "needs_human_count": report["needs_human_count"],
                    "verify_flagged": report["verify_flagged"],
                },
                duration_sec=time.time() - _started,
                status="complete",
                project_id=project_id,
                job_type="document",
                folder_id=folder_id,
                original_filename=original_filename,
                created_by=created_by,
            )
        finally:
            store.close()

    return report


def pdf_to_idml(
    src_pdf: str,
    out_dir: str = "out",
    font: str = "Minion Pro",
    backgrounds: bool = True,
    with_ocr: bool = True,
    with_equations: bool = True,
    mathpix_limit: int | None = None,
    equation_engine: str | None = None,
) -> dict:
    """PDF → IDML, running the ingest / OCR / equation layers on the way.

    This is the initiation point the workflow doc was blocked on: a PDF-only
    client can now enter the high-fidelity IDML path without ever supplying an
    `.indd`. Feed the result to `translate_idml`.
    """
    import os as _os

    from babel.idml.build import FrameSpec, build_idml
    from babel.ingest.ocr import merge_ocr_lines, ocr_image_regions, ocr_pages
    from babel.protect.equations import extract_equations

    os.makedirs(out_dir, exist_ok=True)
    base = _os.path.splitext(_os.path.basename(src_pdf))[0]
    out_idml = _os.path.join(out_dir, f"{base}.idml")

    lines = extract_lines(src_pdf)
    notes: list[str] = []

    # --- layer 2: OCR ---------------------------------------------------
    ocr_lines: list = []
    image_frames: dict[int, list] = {}
    if with_ocr:
        page_lines, note = ocr_pages(src_pdf)
        notes.append(note)
        ocr_lines += page_lines

        img_lines, note = ocr_image_regions(src_pdf)
        notes.append(note)
        # Text inside images is drawn over the (still-visible) picture, so the
        # frame is opaque — it masks the burned-in English underneath.
        for ln in img_lines:
            image_frames.setdefault(ln.page, []).append(
                FrameSpec(bbox=tuple(ln.bbox), text=ln.raw_text.strip(),
                          size=ln.dominant.size, opaque=True)
            )
        lines = merge_ocr_lines(lines, page_lines)

    # --- layer 3: equations ---------------------------------------------
    regions = []
    if with_equations:
        regions, note = extract_equations(src_pdf, lines, out_dir,
                                          limit=mathpix_limit, engine=equation_engine)
        notes.append(note)

    # Equations are placed as pictures of the source at their original spot:
    # the text the PDF yields for them is corrupt, and math must never be sent
    # to a translation engine. The recognised LaTeX stays in the report.
    equation_images: dict[int, list] = {}
    for region in regions:
        if region.crop and region.crop_bbox:
            equation_images.setdefault(region.page, []).append(
                (region.crop_bbox, region.crop)
            )

    # --- layer 4: IDML ---------------------------------------------------
    result = build_idml(
        src_pdf, out_idml, segments=None, font=font,
        backgrounds=backgrounds, extra_frames=image_frames or None,
        equation_images=equation_images or None,
    )

    from babel.protect.equations import active_engine

    result.update({
        "source": src_pdf,
        "lines": len(lines),
        "ocr_lines": len(ocr_lines),
        "equations": len(regions),
        "equations_with_latex": sum(1 for r in regions if r.latex),
        "equations_need_review": sum(1 for r in regions if r.latex and not r.verified),
        "equation_engine": equation_engine or (active_engine() if with_equations else None),
        "latex": [
            {"page": r.page + 1, "bbox": [round(v, 1) for v in r.bbox],
             "raw": r.raw_text, "latex": r.latex,
             "verified": r.verified, "review_reason": r.review_reason,
             "crop": r.crop}
            for r in regions if r.latex
        ][:500],
        "notes": notes,
    })
    return result


def translate_idml(
    src_idml: str,
    out_dir: str = "out",
    tm_path: str = "babel_tm.db",
    review_db: str | None = "babel_review.db",
    target_lang: str | None = None,
    with_graphics: bool = True,
    with_graphics_ocr: bool = True,
    project_id: str | None = None,
    folder_id: str | None = None,
    original_filename: str | None = None,
    created_by: str | None = None,
) -> dict:
    """Translate an IDML file run-by-run and write a translated .idml.

    High-fidelity path: InDesign reflows on open, so this same file exports to
    both PDF and INDD (see idml.export). Reuses the whole translation core.

    `with_graphics` also translates linked `.ai`/`.eps` word-art graphics
    (stylized callouts like "SAY", "GO!" that are placed images, not IDML
    text) whose linked file is found locally and has extractable prose — see
    `babel.idml.graphics`. Requires the original design's Links folder to
    still be present at the path recorded in the IDML; if it isn't, those
    graphics are silently left untouched (nothing to translate them with).
    `with_graphics_ocr` additionally OCRs each linked graphic to catch text
    that was converted to vector outlines rather than kept live (a "GO!"
    arrow can be pure outlines while the "SAY" beside it is live text) —
    ignored if `with_graphics` is off."""
    import time
    from babel.idml.package import IdmlPackage

    _started = time.time()
    lang = languages.get(target_lang)
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src_idml))[0]
    out_idml = os.path.join(out_dir, f"{base}.{lang.code}.idml")

    logger.info("translate_idml: starting %s -> target_lang=%s", src_idml, lang.code)

    pkg = IdmlPackage(src_idml)
    segments = pkg.segments()
    logger.info("translate_idml: ingest complete, %d runs extracted", len(segments))

    primary, secondary = build_engines(target_lang=lang.code)
    logger.info("translate_idml: translating with %s%s",
                primary.name, f" + {secondary.name}" if secondary else "")
    tm = TranslationMemory(tm_path, tgt_lang=lang.code)
    try:
        Translator(primary, secondary, tm, target_lang=lang.code).run(segments)

        graphics_translated = 0
        if with_graphics:
            from babel.idml.graphics import translate_linked_graphics

            mapping = translate_linked_graphics(
                pkg.raw_entries(), lang, tm, primary, secondary, out_dir,
                with_ocr=with_graphics_ocr)
            graphics_translated = pkg.relink(mapping)
            logger.info("translate_idml: %d linked graphic(s) translated and relinked",
                        len(mapping))
    finally:
        tm.close()

    from babel.translate.verify import build_verifier, run_verification

    verifier = build_verifier(target_lang=lang.code)
    verify_flagged = run_verification(segments, verifier)

    disagreements = sum(1 for s in segments if s.disagreement)
    needs_human = sum(1 for s in segments if s.status == "needs_human")
    logger.info(
        "translate_idml: translation complete, %d needs_human, %d disagreements",
        needs_human, disagreements,
    )

    applied = pkg.apply(segments, idml_font=lang.idml_font)
    pkg.save(out_idml)
    logger.info("translate_idml: saved output to %s (%d runs written)", out_idml, applied)

    status_counts = Counter(s.status for s in segments)
    report = {
        "source": src_idml,
        "output": out_idml,
        "target_lang": lang.code,
        "target_language": lang.name,
        "engine_primary": primary.name,
        "engine_secondary": secondary.name if secondary else None,
        "segments_total": len(segments),
        "runs_with_math": sum(1 for s in segments if s.has_math_font),
        "runs_written": applied,
        "graphics_translated": graphics_translated,
        "status_counts": dict(status_counts),
        "disagreements": sum(1 for s in segments if s.disagreement),
        "verifier": verifier.name if verifier else None,
        "verify_flagged": verify_flagged,
        "needs_human_count": sum(1 for s in segments if s.status == "needs_human"),
        "job_id": None,
        "note": "Open the .idml in InDesign (or run babel.idml.export) to produce PDF + INDD.",
    }

    if review_db:
        from babel.review.store import ReviewStore

        store = ReviewStore(review_db, tm_path=tm_path)
        try:
            report["job_id"] = store.save_job(
                src_idml, out_idml, segments,
                {
                    "engine_primary": primary.name,
                    "status_counts": dict(status_counts),
                    "format": "idml",
                    "target_lang": lang.code,
                    "disagreements": report["disagreements"],
                    "needs_human_count": report["needs_human_count"],
                    "verify_flagged": report["verify_flagged"],
                },
                duration_sec=time.time() - _started,
                status="complete",
                project_id=project_id,
                job_type="document",
                folder_id=folder_id,
                original_filename=original_filename,
                created_by=created_by,
            )
        finally:
            store.close()

    logger.info("translate_idml: done, job_id=%s duration=%.2fs",
                report["job_id"], time.time() - _started)
    return report


def regenerate_idml_from_review(job: dict, review_db: str = "babel_review.db") -> str:
    """Re-apply a job's current review-store state (including post-export human
    approvals/edits) onto a fresh copy of the original .idml and overwrite the
    saved output.

    `translate_idml` writes the output .idml once, right after MT — any segment
    that came back `needs_human` (integrity fail, disagreement, low OCR
    confidence) is left untouched (English) at that point, by design, so a
    person can fix it in the review UI. But `ReviewStore.update_segment` only
    updates its own DB row; nothing re-applies that fix to the .idml on disk.
    Call this before serving a download so an approved/edited segment actually
    reaches the file instead of silently staying English forever.
    """
    from babel.idml.package import IdmlPackage
    from babel.review.store import ReviewStore

    src_idml = str(job["source"])
    out_idml = str(job["output"])
    meta = job.get("meta") or {}
    lang = languages.get(meta.get("target_lang"))

    pkg = IdmlPackage(src_idml)
    by_id = {s.id: s for s in pkg.segments()}

    store = ReviewStore(review_db)
    try:
        rows = store.get_segments(job["id"])
    finally:
        store.close()

    segments = []
    for r in rows:
        seg = by_id.get(r["seg_id"])
        if seg is None:
            continue
        seg.target = r["target"]
        seg.status = r["status"]
        segments.append(seg)

    pkg.apply(segments, idml_font=lang.idml_font)
    pkg.save(out_idml)
    return out_idml


def rebuild_from_edits(job_id: str, out_dir: str = "out",
                        review_db: str = "babel_review.db") -> str:
    """Redraw a PDF job's output from the review store's current target/status
    per segment — call after a human edits or approves a segment, since
    `ReviewStore.update_segment` only updates its own row; nothing re-draws
    the PDF until this runs.

    Re-extracts the original source PDF (ingest -> mathguard) rather than
    reconstructing Segment objects from the review store's reduced projection,
    so font/size/color/rotation/math placeholders come from the real PDF
    instead of being guessed — `build_segments`' id scheme (`p{page}-s{n}`) is
    deterministic over the same source, so ids line up with the stored rows.
    """
    from babel.ingest.ocr import merge_ocr_lines, ocr_image_regions
    from babel.review.store import ReviewStore

    store = ReviewStore(review_db)
    try:
        job = next((j for j in store.list_jobs() if j["id"] == job_id), None)
        if job is None:
            raise KeyError(f"job {job_id} not found")
        rows = store.get_segments(job_id)
    finally:
        store.close()

    src_pdf = str(job["source"])
    out_pdf = str(job["output"])
    meta = job.get("meta") or {}
    lang = languages.get(meta.get("target_lang"))

    lines = extract_lines(src_pdf)
    img_lines, _ = ocr_image_regions(src_pdf)
    lines = merge_ocr_lines(lines, img_lines)
    segments = build_segments(lines)

    by_id = {s.id: s for s in segments}
    for r in rows:
        seg = by_id.get(r["seg_id"])
        if seg is None:
            continue
        seg.target = r["target"]
        # `_replaceable` (reassemble/pdf.py) only redraws a segment whose
        # status is "translated" or "tm_hit" — a human approve/edit sets the
        # review-store status to "approved"/"edited", which isn't in that
        # set, so the edit would silently never reach the PDF. Map anything
        # with a real reviewed target to "translated"; leave "needs_human"
        # (and any other flagged state) alone so it still renders as source,
        # same as the original translate_pdf pass.
        seg.status = "translated" if r["status"] not in ("needs_human", "empty") else r["status"]

    rebuild_pdf(src_pdf, segments, out_pdf, target_lang=lang.code)
    return out_pdf
