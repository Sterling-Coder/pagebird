"""babel CLI.

    python -m babel.cli inspect  <pdf> [--pages 0,1]
    python -m babel.cli translate <pdf> --out out/ [--pages 0,1] [--tm babel_tm.db]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from babel.config import load_env

load_env()

from babel import languages
from babel.ingest.pdf import extract_lines
from babel.protect.mathguard import build_segments
from babel.pipeline import pdf_to_idml, translate_idml, translate_pdf


def _parse_pages(val: str | None) -> list[int] | None:
    if not val:
        return None
    return [int(x) for x in val.split(",") if x.strip() != ""]


def cmd_inspect(args) -> int:
    lines = extract_lines(args.pdf, pages=_parse_pages(args.pages))
    segs = build_segments(lines)
    protected = [s for s in segs if s.placeholders]
    print(f"lines: {len(segs)}   lines-with-math: {len(protected)}")
    print("-" * 70)
    shown = 0
    for s in segs:
        if not s.is_translatable:
            continue
        tag = " [MATH]" if s.placeholders else ""
        print(f"{s.id}{tag}: {s.source!r}")
        if s.placeholders:
            print(f"    protected: {s.placeholders}")
        shown += 1
        if shown >= args.limit:
            print(f"... ({args.limit} shown; use --limit to see more)")
            break
    return 0


def cmd_translate(args) -> int:
    report = translate_pdf(
        args.pdf, out_dir=args.out, pages=_parse_pages(args.pages), tm_path=args.tm,
        target_lang=getattr(args, "lang", None),
    )
    report_path = os.path.join(
        args.out, os.path.splitext(os.path.basename(args.pdf))[0] + ".report.json"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("*** DRAFT PDF — lossy on tables/multi-box titles; IDML path for production ***")
    print(f"output PDF : {report['output']}")
    print(f"QA report  : {report_path}")
    print(f"engines    : {report['engine_primary']} + {report['engine_secondary']}")
    print(f"segments   : {report['segments_total']}  (math lines: {report['lines_with_math']})")
    print(f"status     : {report['status_counts']}")
    print(f"reassembly : {report['reassembly_actions']}")
    print(f"verify     : {report['verifier']} flagged {report['verify_flagged']}")
    print(f"disagree   : {report['disagreements']}   needs_human: {report['needs_human_count']}")
    if report["overflow"]:
        print(f"overflow   : {len(report['overflow'])} lines (see report)")
    if report["graphic_pages"]:
        pages = ", ".join(str(g["page"]) for g in report["graphic_pages"])
        print(f"graphics   : {len(report['graphic_pages'])} pages may hold untranslated graphic text (pages {pages})")
    return 0


def cmd_translate_idml(args) -> int:
    report = translate_idml(args.idml, out_dir=args.out, tm_path=args.tm,
                             target_lang=getattr(args, "lang", None))
    report_path = os.path.join(
        args.out, os.path.splitext(os.path.basename(args.idml))[0] + ".report.json"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"output IDML: {report['output']}")
    print(f"QA report  : {report_path}")
    print(f"engines    : {report['engine_primary']} + {report['engine_secondary']}")
    print(f"runs       : {report['segments_total']}  (math: {report['runs_with_math']}, written: {report['runs_written']})")
    print(f"graphics   : {report['graphics_translated']} linked graphic(s) translated")
    print(f"status     : {report['status_counts']}")
    print(f"verify     : {report['verifier']} flagged {report['verify_flagged']}")
    print(f"needs_human: {report['needs_human_count']}   disagree: {report['disagreements']}")

    if args.export:
        from babel.idml.export import export

        res = export(report["output"], args.out)
        print(f"export     : {'OK' if res.ok else 'skipped'} — {res.message}")
        if res.ok:
            print(f"             INDD={res.indd}")
    else:
        print(f"note       : {report['note']}")
    return 0


def cmd_pdf_to_idml(args) -> int:
    report = pdf_to_idml(
        args.pdf,
        out_dir=args.out,
        font=args.font,
        backgrounds=not args.no_backgrounds,
        with_ocr=not args.no_ocr,
        with_equations=not args.no_equations,
        mathpix_limit=args.mathpix_limit,
        equation_engine=args.equation_engine,
    )
    report_path = os.path.join(
        args.out, os.path.splitext(os.path.basename(args.pdf))[0] + ".idml.report.json"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"output IDML: {report['output']}")
    print(f"QA report  : {report_path}")
    print(f"pages      : {report['pages']}   text frames: {report['frames']}")
    print(f"lines      : {report['lines']}   (ocr: {report['ocr_lines']})")
    print(f"equations  : {report['equations']}  (latex: {report['equations_with_latex']}"
          f" via {report.get('equation_engine')})")
    if report.get("asset_dir"):
        print(f"assets     : {report['asset_dir']}  ({report['backgrounds']} page backgrounds)")
    for note in report["notes"]:
        print(f"  - {note}")
    print("next       : python -m babel.cli translate-idml "
          f"{report['output']} --out {args.out}")
    return 0


def cmd_preview_idml(args) -> int:
    from babel.idml.preview import render_idml

    out = args.out or os.path.splitext(args.idml)[0] + ".preview.pdf"
    stats = render_idml(args.idml, out, dpi=args.png_dpi, draw_frames=args.frames)
    print(f"preview PDF: {stats['output']}")
    print(f"pages      : {stats['pages']}   frames: {stats['frames']}   images: {stats['images']}")
    if stats["missing_images"]:
        print(f"missing    : {stats['missing_images']} linked image(s) not found on disk")
    if stats["overflow"]:
        print(f"overflow   : {stats['overflow']} frame(s) needed shrinking to fit")
    return 0


def cmd_ocr(args) -> int:
    import logging

    from babel.ingest.ocr import (detect_image_regions, detect_scanned_pages,
                                  ocr_diagnostics, ocr_image_regions, ocr_pages,
                                  ocr_status)

    # This command exists to diagnose OCR, so show the log rather than hide it.
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(levelname)-7s %(name)s: %(message)s")

    diag = ocr_diagnostics()
    print(f"engine     : {diag['active_engine']}"
          + (f"  (forced by BABEL_OCR_ENGINE={diag['forced_by_env']})"
             if diag["forced_by_env"] else ""))
    for name in ("docai", "vision", "http", "rapidocr"):
        node = diag[name]
        mark = "ready" if node.get("available") or node.get("healthy") else "unavailable"
        detail = node.get("reason") or ""
        print(f"  {name:<9} {mark}{('  — ' + detail) if detail else ''}")
    vis = diag["vision"]
    if not vis["available"]:
        # The two failure modes that actually happen, called out by name.
        print(f"  vision creds: {vis['credentials_path'] or '(unset)'} "
              f"exists={vis['credentials_file_exists']}")
        if vis["sdk_import_error"]:
            print(f"  vision sdk  : {vis['sdk_import_error']}")

    status = ocr_status()
    scanned = detect_scanned_pages(args.pdf)
    regions = detect_image_regions(args.pdf)
    print(f"scanned    : {len(scanned)} page(s) {scanned[:10]}")
    print(f"images     : {sum(len(v) for v in regions.values())} region(s) "
          f"on {len(regions)} page(s)")
    if not status:
        return 0
    lines, note = ocr_pages(args.pdf)
    print(f"  - {note}")
    img_lines, note = ocr_image_regions(args.pdf)
    print(f"  - {note}")
    for ln in (lines + img_lines)[: args.limit]:
        print(f"    p{ln.page + 1} {ln.raw_text!r}  conf={ln.ocr_confidence:.2f}")
    return 0


def cmd_equations(args) -> int:
    """Detect + recognise equations only, and print the LaTeX."""
    from babel.protect.equations import active_engine, extract_equations

    engine = args.engine or active_engine()
    print(f"engine     : {engine}")
    lines = extract_lines(args.pdf, pages=_parse_pages(args.pages))
    regions, note = extract_equations(args.pdf, lines, args.out,
                                      limit=args.limit, engine=args.engine)
    print(f"  - {note}")
    shown = [r for r in regions if not r.verified] if args.review_only else regions
    for r in shown[: args.show]:
        mark = "  " if r.verified else "!!"
        print(f"\n{mark} p{r.page + 1}  raw : {r.raw_text[:70]!r}")
        print(f"        latex: {r.latex!r}")
        if not r.verified:
            print(f"        REVIEW: {r.review_reason}")
        print(f"        crop : {r.crop}")
    out_json = os.path.join(args.out, "equations.json")
    os.makedirs(args.out, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(
            [{"page": r.page + 1, "bbox": [round(v, 1) for v in r.bbox],
              "raw": r.raw_text, "latex": r.latex, "verified": r.verified,
              "review_reason": r.review_reason, "crop": r.crop} for r in regions],
            f, ensure_ascii=False, indent=2,
        )
    print(f"\nwrote      : {out_json}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="babel")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("inspect", help="show protected segments, no translation")
    pi.add_argument("pdf")
    pi.add_argument("--pages", default=None, help="comma-separated 0-based page numbers")
    pi.add_argument("--limit", type=int, default=40)
    pi.set_defaults(func=cmd_inspect)

    pt = sub.add_parser("translate", help="translate a PDF and write target PDF + report")
    pt.add_argument("pdf")
    pt.add_argument("--out", default="out")
    pt.add_argument("--pages", default=None, help="comma-separated 0-based page numbers")
    pt.add_argument("--tm", default="babel_tm.db")
    pt.add_argument("--lang", default=None, choices=sorted(languages.LANGUAGES),
                    help="target language (default: BABEL_TARGET_LANG or es)")
    pt.set_defaults(func=cmd_translate)

    pm = sub.add_parser("translate-idml", help="translate an IDML and write target IDML (+ optional PDF/INDD)")
    pm.add_argument("idml")
    pm.add_argument("--out", default="out")
    pm.add_argument("--tm", default="babel_tm.db")
    pm.add_argument("--lang", default=None, choices=sorted(languages.LANGUAGES),
                    help="target language (default: BABEL_TARGET_LANG or es)")
    pm.add_argument("--export", action="store_true",
                    help="also export INDD via InDesign Server (needs INDESIGN_SERVER)")
    pm.set_defaults(func=cmd_translate_idml)

    pb = sub.add_parser("pdf-to-idml",
                        help="convert a PDF into IDML (ingest + OCR + equations)")
    pb.add_argument("pdf")
    pb.add_argument("--out", default="out")
    pb.add_argument("--font", default="Minion Pro")
    pb.add_argument("--no-backgrounds", action="store_true",
                    help="skip the graphics-only page images (text frames only)")
    pb.add_argument("--no-ocr", action="store_true")
    pb.add_argument("--no-equations", action="store_true")
    pb.add_argument("--mathpix-limit", type=int, default=None,
                    help="cap how many equations get recognised")
    pb.add_argument("--equation-engine", choices=["mathpix", "pix2tex", "none"],
                    default=None,
                    help="force a recogniser (default: mathpix if keyed, else pix2tex)")
    pb.set_defaults(func=cmd_pdf_to_idml)

    pv = sub.add_parser("preview-idml", help="render an IDML to a viewable PDF (no InDesign)")
    pv.add_argument("idml")
    pv.add_argument("--out", default=None)
    pv.add_argument("--png-dpi", type=int, default=0, help="also write PNG per page")
    pv.add_argument("--frames", action="store_true", help="outline text frames")
    pv.set_defaults(func=cmd_preview_idml)

    pe = sub.add_parser("equations", help="extract equations to LaTeX and print them")
    pe.add_argument("pdf")
    pe.add_argument("--out", default="out")
    pe.add_argument("--pages", default=None, help="comma-separated 0-based page numbers")
    pe.add_argument("--limit", type=int, default=None, help="cap equations recognised")
    pe.add_argument("--show", type=int, default=10, help="how many to print")
    pe.add_argument("--engine", choices=["mathpix", "pix2tex", "none"], default=None)
    pe.add_argument("--review-only", action="store_true",
                    help="print only equations that disagree with the PDF text")
    pe.set_defaults(func=cmd_equations)

    po = sub.add_parser("ocr", help="report scanned pages / image text regions")
    po.add_argument("pdf")
    po.add_argument("--limit", type=int, default=20)
    po.add_argument("--debug", action="store_true",
                    help="per-paragraph OCR logging, including text dropped below "
                         "the confidence threshold")
    po.set_defaults(func=cmd_ocr)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
