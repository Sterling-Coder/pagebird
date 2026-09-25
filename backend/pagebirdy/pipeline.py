"""End-to-end PDF translation pipeline + QA report.

    ingest -> protect math -> (dual-engine translate + integrity gate)
           -> reassemble PDF -> QA report
"""

from __future__ import annotations

import logging
import os
from collections import Counter
from typing import Callable

import fitz

from pagebirdy import fonts as pagebirdy_fonts
from pagebirdy import languages
from pagebirdy.ingest.pdf import extract_lines
from pagebirdy.protect.mathguard import build_segments
from pagebirdy.reassemble.pdf import detect_graphic_pages, figure_pages, rebuild_pdf
from pagebirdy.translate.engine import build_engines
from pagebirdy.translate.translator import Translator

logger = logging.getLogger("pagebirdy.pipeline")


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
    review_db: str | None = "babel_review.db",
    target_lang: str | None = None,
    with_ocr: bool = True,
    project_id: str | None = None,
    folder_id: str | None = None,
    original_filename: str | None = None,
    created_by: str | None = None,
    job_id: str | None = None,
    progress_cb: Callable[[int, str], None] | None = None,
) -> dict:
    """`job_id`, if given, is an existing `review_jobs` row (created up front
    via `ReviewStore.create_pending_job` so the job is visible as "processing"
    before translation starts) that gets filled in via `finalize_job` instead
    of a fresh row via `save_job`.

    `progress_cb(percent, stage)`, if given, is called at each pipeline stage
    boundary — advisory only, best-effort on the caller's side; never awaited
    or allowed to affect the translation itself."""
    import time
    _started = time.time()

    def _progress(percent: int, stage: str) -> None:
        if progress_cb is not None:
            progress_cb(percent, stage)

    lang = languages.get(target_lang)
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src_pdf))[0]
    out_pdf = os.path.join(out_dir, f"{base}.{lang.code}.pdf")

    _progress(5, "extracting text")
    lines = extract_lines(src_pdf, pages=pages)

    # Text baked into a graphic's pixels (a banner, callout) has no PDF text
    # object for extract_lines to find — OCR the raster images and fold the
    # recovered lines in before segmentation, same as any other line.
    if with_ocr:
        from pagebirdy.ingest.ocr import merge_ocr_lines, ocr_image_regions

        _progress(10, "running OCR")
        img_lines, note = ocr_image_regions(src_pdf)
        logger.info("image-OCR: %s", note)
        for ln in img_lines:
            logger.info("image-OCR line: page=%s bbox=%s text=%r",
                       ln.page, ln.bbox, ln.raw_text.strip())
        merged = merge_ocr_lines(lines, img_lines)
        logger.info("image-OCR: %d/%d lines kept after dedup",
                    sum(1 for ln in merged if ln.from_ocr), len(img_lines))
        lines = merged

    segments = build_segments(lines)

    primary, secondary = build_engines(doc_context=_doc_context(lines), target_lang=lang.code)
    _progress(20, "translating")
    Translator(primary, secondary, target_lang=lang.code).run(
        segments,
        progress_cb=lambda done, total: _progress(
            20 + int(50 * done / total) if total else 70, "translating"
        ),
    )

    from pagebirdy.translate.verify import build_verifier, run_verification

    _progress(70, "checking accuracy")
    verifier = build_verifier(target_lang=lang.code)
    verify_flagged = run_verification(segments, verifier)

    _progress(80, "rebuilding document")
    outcomes = rebuild_pdf(src_pdf, segments, out_pdf, target_lang=lang.code)
    _progress(95, "finishing")

    rtl = lang.direction == "rtl"
    doc = fitz.open(src_pdf)
    try:
        graphic_pages = detect_graphic_pages(doc)
        # Only a mirrored edition can invert a figure, so an LTR job has no
        # figure review queue to answer for.
        figures = figure_pages(doc) if rtl else []
    finally:
        doc.close()

    regular = pagebirdy_fonts.resolve(lang.fonts.get("regular", ())) or ""

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
        "font_source": ("bundled" if pagebirdy_fonts.bundled(os.path.basename(regular))
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
        from pagebirdy.review.store import ReviewStore

        store = ReviewStore(review_db)
        try:
            meta = {
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
            }
            if job_id:
                store.finalize_job(job_id, out_pdf, segments, meta,
                                   duration_sec=time.time() - _started, status="complete")
                report["job_id"] = job_id
            else:
                report["job_id"] = store.save_job(
                    src_pdf, out_pdf, segments, meta,
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

    from pagebirdy.idml.build import FrameSpec, build_idml
    from pagebirdy.ingest.ocr import merge_ocr_lines, ocr_image_regions, ocr_pages
    from pagebirdy.protect.equations import extract_equations

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

    from pagebirdy.protect.equations import active_engine

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
    review_db: str | None = "babel_review.db",
    target_lang: str | None = None,
    with_graphics: bool = True,
    with_graphics_ocr: bool = True,
    with_draft_pdf: bool = False,
    project_id: str | None = None,
    folder_id: str | None = None,
    original_filename: str | None = None,
    created_by: str | None = None,
    job_id: str | None = None,
    progress_cb: Callable[[int, str], None] | None = None,
) -> dict:
    """Translate an IDML file run-by-run and write a translated .idml.

    `job_id`, if given, is an existing `review_jobs` row (created up front via
    `ReviewStore.create_pending_job` so the job is visible as "processing"
    before translation starts) that gets filled in via `finalize_job` instead
    of a fresh row via `save_job`.

    High-fidelity path: InDesign reflows on open, so this same file exports to
    both PDF and INDD (see idml.export). Reuses the whole translation core.

    `with_graphics` also translates linked `.ai`/`.eps` word-art graphics
    (stylized callouts like "SAY", "GO!" that are placed images, not IDML
    text) whose linked file is found locally and has extractable prose — see
    `pagebirdy.idml.graphics`. Requires the original design's Links folder to
    still be present at the path recorded in the IDML; if it isn't, those
    graphics are silently left untouched (nothing to translate them with).
    `with_graphics_ocr` additionally OCRs each linked graphic to catch text
    that was converted to vector outlines rather than kept live (a "GO!"
    arrow can be pure outlines while the "SAY" beside it is live text) —
    ignored if `with_graphics` is off."""
    import time
    from pagebirdy.idml.package import IdmlPackage

    _started = time.time()

    def _progress(percent: int, stage: str) -> None:
        if progress_cb is not None:
            progress_cb(percent, stage)

    lang = languages.get(target_lang)
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src_idml))[0]
    out_idml = os.path.join(out_dir, f"{base}.{lang.code}.idml")

    logger.info("translate_idml: starting %s -> target_lang=%s", src_idml, lang.code)

    _progress(5, "extracting text")
    pkg = IdmlPackage(src_idml)
    segments = pkg.segments()
    logger.info("translate_idml: ingest complete, %d runs extracted", len(segments))

    primary, secondary = build_engines(target_lang=lang.code)
    logger.info("translate_idml: translating with %s%s",
                primary.name, f" + {secondary.name}" if secondary else "")
    _progress(15, "translating")
    Translator(primary, secondary, target_lang=lang.code).run(
        segments,
        progress_cb=lambda done, total: _progress(
            15 + int(45 * done / total) if total else 60, "translating"
        ),
    )

    graphics_translated = 0
    mapping: dict[str, str] = {}
    if with_graphics:
        from pagebirdy.idml.graphics import translate_linked_graphics

        _progress(60, "translating linked graphics")
        # Fall back to a `Links/` folder next to the uploaded IDML when the
        # original designer's absolute paths aren't present locally.
        local_links_dir = os.path.join(os.path.dirname(os.path.abspath(src_idml)), "Links")
        mapping = translate_linked_graphics(
            pkg.raw_entries(), lang, primary, secondary, out_dir,
            with_ocr=with_graphics_ocr,
            local_links_dir=local_links_dir if os.path.isdir(local_links_dir) else None)
        graphics_translated = pkg.relink(mapping)
        logger.info("translate_idml: %d linked graphic(s) translated and relinked",
                    len(mapping))
    _progress(80, "checking accuracy")

    # `Links_<lang>/` (see idml/graphics.py's `graphics_dir`) is one shared
    # folder per language across EVERY job ever translated to it, not scoped
    # per document — so a caller bundling "this job's" translated graphics
    # (api.py's download endpoint) cannot just list that directory; it would
    # pick up every other job's output too, including stale/renamed copies
    # of a same-named asset reused across unrelated documents. Recording the
    # exact filenames this job produced is the only reliable scope.
    graphics_files = [os.path.basename(uri[len("file:"):]) for uri in mapping.values()]

    from pagebirdy.translate.verify import build_verifier, run_verification

    verifier = build_verifier(target_lang=lang.code)
    verify_flagged = run_verification(segments, verifier)

    disagreements = sum(1 for s in segments if s.disagreement)
    needs_human = sum(1 for s in segments if s.status == "needs_human")
    logger.info(
        "translate_idml: translation complete, %d needs_human, %d disagreements",
        needs_human, disagreements,
    )

    _progress(88, "rebuilding document")
    applied = pkg.apply(segments, idml_font=lang.idml_font, size_delta=lang.size_delta,
                       direction=lang.direction)
    pkg.save(out_idml)
    logger.info("translate_idml: saved output to %s (%d runs written)", out_idml, applied)

    # Draft PDF preview (no InDesign) — a legibility proof of the translation,
    # served as the job's download?format=pdf. Best-effort: never fail the job.
    # Off by default: nothing in the current UI consumes it for .idml jobs
    # (the file-detail page just offers a plain .idml download), and
    # rendering it added several real seconds to every job for no payoff.
    _progress(95, "finishing")
    has_draft_pdf = False
    if with_draft_pdf:
        out_pdf = os.path.splitext(out_idml)[0] + ".pdf"
        try:
            from pagebirdy.idml.render import render_idml_to_pdf
            render_idml_to_pdf(out_idml, out_pdf, target_lang=lang.code)
            has_draft_pdf = True
        except Exception:
            logger.exception("translate_idml: draft PDF render failed (idml still saved)")

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
        "has_draft_pdf": has_draft_pdf,
        "graphics_files": graphics_files,
        "note": "PDF is a draft preview (no InDesign). Open the .idml in InDesign "
                "(or run pagebirdy.idml.export) for a faithful PDF + INDD.",
    }

    if review_db:
        from pagebirdy.review.store import ReviewStore

        store = ReviewStore(review_db)
        try:
            meta = {
                "engine_primary": primary.name,
                "status_counts": dict(status_counts),
                "format": "idml",
                "target_lang": lang.code,
                "graphics_files": graphics_files,
                "disagreements": report["disagreements"],
                "needs_human_count": report["needs_human_count"],
                "verify_flagged": report["verify_flagged"],
            }
            if job_id:
                store.finalize_job(job_id, out_idml, segments, meta,
                                   duration_sec=time.time() - _started, status="complete")
                report["job_id"] = job_id
            else:
                report["job_id"] = store.save_job(
                    src_idml, out_idml, segments, meta,
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


def rebuild_from_edits(job_id: str, out_dir: str = "out",
                        review_db: str = "babel_review.db",
                        source_path: str | None = None, output_path: str | None = None) -> str:
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
    from pagebirdy.ingest.ocr import merge_ocr_lines, ocr_image_regions
    from pagebirdy.review.store import ReviewStore

    store = ReviewStore(review_db)
    try:
        job = next((j for j in store.list_jobs() if j["id"] == job_id), None)
        if job is None:
            raise KeyError(f"job {job_id} not found")
        rows = store.get_segments(job_id)
    finally:
        store.close()

    src_pdf = source_path or str(job["source"])
    out_pdf = output_path or str(job["output"])
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


def translate_links_folder(
    paths: list[str],
    out_dir: str = "out",
    review_db: str | None = "babel_review.db",
    target_lang: str | None = None,
    with_ocr: bool = True,
    project_id: str | None = None,
    folder_id: str | None = None,
    original_filename: str | None = None,
    created_by: str | None = None,
    job_id: str | None = None,
    progress_cb: Callable[[int, str], None] | None = None,
) -> dict:
    """Translate a batch of linked-graphic files (.ai/.eps/.pdf/.psd) on
    their own — independent of any `.idml`, with no relinking step. Each
    file goes through the exact same OCR/translate/rebuild path as a linked
    graphic found inside an `.idml` (`pagebirdy.idml.graphics.translate_graphic`);
    this just runs it standalone over a folder someone uploaded directly,
    rather than one discovered via an `.idml`'s own `<Link>` references.

    Trade-off versus attaching Links to an `.idml` upload (the earlier
    design): nothing here edits an `.idml`'s XML to point at the translated
    output, so re-linking the translated graphics into a document is a
    manual step in InDesign afterward. In exchange, a links batch is its own
    independent job — uploaded, translated, and downloaded once, not
    duplicated into every document that happens to reference it.
    """
    import shutil
    import time
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from pagebirdy.idml.graphics import _content_hash, translate_graphic

    _started = time.time()

    def _progress(percent: int, stage: str) -> None:
        if progress_cb is not None:
            progress_cb(percent, stage)

    lang = languages.get(target_lang)
    os.makedirs(out_dir, exist_ok=True)
    translated_dir = os.path.join(out_dir, f"translated_{lang.code}")
    os.makedirs(translated_dir, exist_ok=True)

    primary, secondary = build_engines(target_lang=lang.code)
    logger.info("translate_links_folder: translating %d file(s) with %s%s",
                len(paths), primary.name, f" + {secondary.name}" if secondary else "")

    # Byte-identical uploads (the same reused asset attached under several
    # filenames, or literally re-selected twice) are common in a batch this
    # size — dedup by content hash so each distinct graphic is OCR'd and
    # translated exactly once, then the result is copied to every other
    # filename that shares its bytes instead of re-running the whole
    # OCR+LLM+rebuild pipeline for a file we've already translated.
    by_hash: dict[str, list[str]] = {}
    for path in paths:
        try:
            h = _content_hash(path)
        except OSError:
            h = path  # unreadable file: treat as its own singleton group, fails normally below
        by_hash.setdefault(h, []).append(path)
    unique_paths = [group[0] for group in by_hash.values()]
    if len(unique_paths) < len(paths):
        logger.info("translate_links_folder: %d file(s) are byte-identical duplicates, "
                    "translating %d unique file(s)", len(paths) - len(unique_paths),
                    len(unique_paths))

    # Each file is independent (own OCR + translate call), so run the batch
    # concurrently instead of one-by-one — a folder of hundreds of graphics
    # was taking far too long serialized. Matches the worker count used for
    # concurrent chunk translation elsewhere (translate/verify.py).
    _MAX_CONCURRENT_LINKS = 6

    # Display/storage names are flat (no subfolders) even though a batch
    # uploaded via folder-picker can carry the same leaf filename in several
    # subfolders — two genuinely different files ("Unit01/CA001.ai" and
    # "Unit02/CA001.ai") must not overwrite each other's translated output or
    # original upload the way saving them by leaf name alone once did. Each
    # namespace (translated output vs. persisted-original) is disambiguated
    # independently since they land in different storage prefixes.
    def _dedupe_name(name: str, used: set[str]) -> str:
        if name not in used:
            used.add(name)
            return name
        base, ext = os.path.splitext(name)
        n = 2
        candidate = f"{base}_{n}{ext}"
        while candidate in used:
            n += 1
            candidate = f"{base}_{n}{ext}"
        # Worth a real log line, not just a name silently changing under the
        # hood — this is the exact "two files, one filename" case that used
        # to cause silent data loss, and a client asking "where's my file"
        # should be answerable by grepping the job id for "renamed".
        logger.info("translate_links_folder: renamed %r -> %r to avoid overwriting "
                    "a different file with the same name", name, candidate)
        used.add(candidate)
        return candidate

    def _desired_out_name(path: str) -> str:
        base, ext = os.path.splitext(os.path.basename(path))
        if ext.lower() in (".psd",):
            ext = ".pdf"
        return f"{base}{ext}"

    translated_names_used: set[str] = set()
    original_names_used: set[str] = set()

    # Precomputed up front (one name per hash group's representative) since
    # `translate_graphic` writes straight to this path — the name has to be
    # settled before translation runs, not after.
    out_name_by_representative = {
        group[0]: _dedupe_name(_desired_out_name(group[0]), translated_names_used)
        for group in by_hash.values()
    }

    def _translate_one(path: str) -> str | None:
        out_path = os.path.join(translated_dir, out_name_by_representative[path])
        try:
            translated = translate_graphic(path, out_path, lang, primary, secondary,
                                           with_ocr=with_ocr)
        except Exception as e:  # a malformed/unusual file must not abort the whole batch
            logger.info("translate_links_folder: failed on %s, left untranslated: %s", path, e)
            return None
        return os.path.basename(out_path) if translated else None

    translated_files: list[str] = []
    total = len(unique_paths) or 1
    done_count = 0
    _progress_lock = threading.Lock()
    result_by_path: dict[str, str | None] = {}
    with ThreadPoolExecutor(max_workers=_MAX_CONCURRENT_LINKS) as ex:
        futures = {ex.submit(_translate_one, path): path for path in unique_paths}
        for fut in as_completed(futures):
            with _progress_lock:
                done_count += 1
                _progress(int(90 * done_count / total), "translating linked graphics")
            result_by_path[futures[fut]] = fut.result()

    # Every uploaded file, translated or not — pure artwork with no
    # extractable text is the common case and was previously dropped
    # entirely (never written anywhere, never uploaded, invisible to both
    # the download zip and any per-file listing). The caller persists these
    # by original name (and its real source path, needed since it may live
    # in a subfolder) so "N files uploaded" and "N files visible" actually
    # match, and nothing a user attached silently vanishes.
    untranslated_files: list[dict] = []
    for group in by_hash.values():
        representative = group[0]
        result = result_by_path.get(representative)
        if result is None:
            for path in group:
                name = _dedupe_name(os.path.basename(path), original_names_used)
                untranslated_files.append({"name": name, "path": path})
            continue
        translated_files.append(result)
        src_out = os.path.join(translated_dir, result)
        for duplicate in group[1:]:
            dup_name = _dedupe_name(_desired_out_name(duplicate), translated_names_used)
            dup_out = os.path.join(translated_dir, dup_name)
            if dup_out == src_out:
                continue
            try:
                shutil.copyfile(src_out, dup_out)
                translated_files.append(dup_name)
            except OSError as e:
                logger.info("translate_links_folder: failed to copy cached result to %s: %s",
                            duplicate, e)
                name = _dedupe_name(os.path.basename(duplicate), original_names_used)
                untranslated_files.append({"name": name, "path": duplicate})
    _progress(95, "finishing")

    logger.info(
        "translate_links_folder: done — %d input file(s), %d unique by content, "
        "%d translated, %d persisted untranslated (%d output file(s) total)",
        len(paths), len(unique_paths), len(translated_files), len(untranslated_files),
        len(translated_files) + len(untranslated_files))
    if len(translated_files) + len(untranslated_files) != len(paths):
        # Every input file should land in exactly one of these two lists —
        # anything else means a file was lost somewhere in this function and
        # needs investigating before it ships, not discovered later as a
        # client-reported missing-file count mismatch.
        logger.error(
            "translate_links_folder: output count (%d) != input count (%d) — "
            "a file was dropped somewhere in this batch",
            len(translated_files) + len(untranslated_files), len(paths))

    report = {
        "target_lang": lang.code,
        "target_language": lang.name,
        "engine_primary": primary.name,
        "engine_secondary": secondary.name if secondary else None,
        "total_files": len(paths),
        "translated_files": translated_files,
        "untranslated_files": untranslated_files,
        "job_id": None,
    }

    if review_db:
        from pagebirdy.review.store import ReviewStore

        store = ReviewStore(review_db)
        try:
            meta = {
                "job_type": "links",
                "format": "links",
                "target_lang": lang.code,
                "total_files": len(paths),
                "translated_count": len(translated_files),
                # `finalize_job` REPLACES the pending job's meta_json wholesale
                # (not a merge) — the extensions set at upload time (see
                # api.py's translate_links_upload) would otherwise vanish the
                # moment the job completes, right when the Files table Type
                # column actually reads it.
                "extensions": sorted({os.path.splitext(p)[1].lower().lstrip(".")
                                       for p in paths if os.path.splitext(p)[1]}),
            }
            if job_id:
                store.finalize_job(job_id, translated_dir, [], meta,
                                   duration_sec=time.time() - _started, status="complete")
                report["job_id"] = job_id
            else:
                report["job_id"] = store.save_job(
                    "links", translated_dir, [], meta,
                    duration_sec=time.time() - _started,
                    status="complete",
                    project_id=project_id,
                    job_type="links",
                    folder_id=folder_id,
                    original_filename=original_filename,
                    created_by=created_by,
                )
        finally:
            store.close()

    return report
