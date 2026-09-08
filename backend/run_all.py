"""One-shot demo: run every layer on a PDF and show the result.

    python run_all.py                          # uses ../docs/grade8_clean.pdf
    python run_all.py ../docs/grade6_clean.pdf
    python run_all.py mydoc.pdf --out myout --open

Runs, in order:

    1. text extraction   PyMuPDF -> lines/spans with geometry
    2. OCR               scanned pages + text inside images  (needs DocAI keys)
    3. equations         detect + crop + Mathpix LaTeX       (needs Mathpix keys)
    4. IDML              live text frames over graphics-only backgrounds
    5. translate         EN -> ES through the existing core  (needs OPENAI_API_KEY)
    6. preview           IDML -> a PDF you can actually look at

Layers without credentials report why and are skipped; the run still completes.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from babel.config import load_env

load_env()

from babel.idml.preview import render_idml
from babel.ingest.ocr import detect_image_regions, detect_scanned_pages, ocr_status
from babel.ingest.pdf import extract_lines
from babel.pipeline import pdf_to_idml, translate_idml
from babel.protect.equations import mathpix_configured

BAR = "=" * 74


def head(step: str, title: str) -> None:
    print(f"\n{BAR}\n  {step}  {title}\n{BAR}")


def main(argv: list[str] | None = None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    default_pdf = os.path.join(here, "..", "docs", "grade8_clean.pdf")

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", nargs="?", default=default_pdf)
    ap.add_argument("--out", default="out")
    ap.add_argument("--font", default="Minion Pro")
    ap.add_argument("--mathpix-limit", type=int, default=None,
                    help="cap billed Mathpix calls")
    ap.add_argument("--skip-translate", action="store_true")
    ap.add_argument("--open", action="store_true",
                    help="open the preview PDF when finished")
    args = ap.parse_args(argv)

    pdf = os.path.abspath(args.pdf)
    if not os.path.exists(pdf):
        print(f"error: no such PDF: {pdf}")
        return 1
    os.makedirs(args.out, exist_ok=True)
    base = os.path.splitext(os.path.basename(pdf))[0]
    started = time.time()

    # ---------------------------------------------------------------- 0
    head("0/5", "Input + credential check")
    print(f"  pdf            : {pdf}")
    ocr = ocr_status()
    print(f"  OCR (DocAI)    : {'ready' if ocr else 'OFF — ' + ocr.reason}")
    print(f"  Mathpix        : {'ready' if mathpix_configured() else 'OFF — MATHPIX_APP_ID/KEY not set'}")
    has_llm = bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
    print(f"  Translation    : {'ready' if has_llm else 'OFF — identity/passthrough (no OPENAI_API_KEY)'}")

    # ---------------------------------------------------------------- 1
    head("1/5", "Layer 1 — text extraction (PyMuPDF)")
    lines = extract_lines(pdf)
    pages = len({ln.page for ln in lines})
    chars = sum(len(ln.raw_text) for ln in lines)
    print(f"  lines          : {len(lines)} across {pages} page(s)")
    print(f"  characters     : {chars}")
    for ln in lines[:3]:
        print(f"    p{ln.page + 1} {ln.raw_text.strip()[:60]!r}")

    # ---------------------------------------------------------------- 2
    head("2/5", "Layer 2 — OCR (scanned pages + text inside images)")
    scanned = detect_scanned_pages(pdf)
    regions = detect_image_regions(pdf)
    print(f"  scanned pages  : {len(scanned)} {scanned[:8]}")
    print(f"  image regions  : {sum(len(v) for v in regions.values())} "
          f"on {len(regions)} page(s)")
    if not ocr:
        print("  -> nothing to OCR without credentials; both are reported, not translated")

    # ---------------------------------------------------------------- 3+4
    head("3/5", "Layers 3 + 4 — equations, then IDML")
    report = pdf_to_idml(
        pdf, out_dir=args.out, font=args.font,
        mathpix_limit=args.mathpix_limit,
    )
    print(f"  equations      : {report['equations']} detected, "
          f"{report['equations_with_latex']} with LaTeX "
          f"(via {report.get('equation_engine')})")
    if report.get("equations_need_review"):
        print(f"  need review    : {report['equations_need_review']} disagree with "
              "the PDF text — see equations.json / crops")
    print(f"  IDML           : {report['output']}")
    print(f"  text frames    : {report['frames']} over {report['backgrounds']} page background(s)")
    for note in report["notes"]:
        print(f"    - {note}")

    idml = report["output"]

    # ---------------------------------------------------------------- 5
    if not args.skip_translate:
        head("4/5", "Translation EN -> ES (existing core)")
        tr = translate_idml(idml, out_dir=args.out)
        print(f"  engine         : {tr['engine_primary']}")
        print(f"  runs written   : {tr['runs_written']} / {tr['segments_total']}")
        print(f"  status         : {tr['status_counts']}")
        print(f"  needs human    : {tr['needs_human_count']}")
        print(f"  ES IDML        : {tr['output']}")
        idml_to_show = tr["output"]
    else:
        idml_to_show = idml

    # ---------------------------------------------------------------- 6
    head("5/5", "Preview — render the IDML to a viewable PDF")
    preview = os.path.join(args.out, f"{base}.preview.pdf")
    stats = render_idml(idml_to_show, preview, dpi=0)
    print(f"  preview PDF    : {stats['output']}")
    print(f"  pages/frames   : {stats['pages']} / {stats['frames']}   images: {stats['images']}")
    if stats["overflow"]:
        print(f"  overflow       : {stats['overflow']} frame(s) had to shrink to fit "
              "(Spanish expansion signal)")

    # ---------------------------------------------------------------- done
    summary = {
        "source_pdf": pdf,
        "lines": len(lines),
        "scanned_pages": scanned,
        "image_regions": sum(len(v) for v in regions.values()),
        "equations": report["equations"],
        "equations_with_latex": report["equations_with_latex"],
        "idml": idml,
        "preview_pdf": stats["output"],
        "frames": report["frames"],
        "overflow_frames": stats["overflow"],
        "seconds": round(time.time() - started, 1),
    }
    summary_path = os.path.join(args.out, f"{base}.run_all.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    head("DONE", f"{summary['seconds']}s")
    print(f"  OPEN THIS  ->  {os.path.abspath(stats['output'])}")
    print(f"  IDML       ->  {os.path.abspath(idml)}")
    print(f"  equations  ->  {os.path.abspath(os.path.join(args.out, 'equations'))}")
    print(f"  summary    ->  {summary_path}")

    if args.open:
        try:
            os.startfile(os.path.abspath(stats["output"]))  # noqa: S606  (Windows)
        except AttributeError:
            subprocess.run(["open", stats["output"]], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
