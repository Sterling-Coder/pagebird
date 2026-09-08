"""Evaluation CLI — a separate entry point so nothing in `babel.cli` changes.

    python -m babel.eval jobs
    python -m babel.eval job <job_id> [--neural] [--mqm] [--gold docs/eval/gold.jsonl]
    python -m babel.eval pdf  <source.pdf>  <translated.pdf>
    python -m babel.eval idml <source.idml> <translated.idml> [--export-json e.json]
    python -m babel.eval gold [--out docs/eval/gold.jsonl] [--lang es]

`job` is the one to use: it reaches the segment pairs in the review DB, so it can
score content integrity and translation quality, not just layout.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from babel.config import load_env

load_env()

from babel import languages
from babel.eval import runner, scorecard
from babel.review.store import ReviewStore


def _write(result: dict, out_dir: str, stem: str) -> tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"{stem}.eval.json")
    md_path = os.path.join(out_dir, f"{stem}.eval.md")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(scorecard.render_markdown(result))
    return json_path, md_path


def _summarise(result: dict, json_path: str, md_path: str) -> None:
    gates = result.get("gates", {})
    print(f"format     : {result.get('format')}   lang: {result.get('target_lang')}")
    print(f"gates      : {'PASS' if gates.get('passed') else 'FAIL'}"
          + (f"  failed={gates['failed']}" if gates.get("failed") else "")
          + (f"  skipped={gates['skipped']}" if gates.get("skipped") else ""))

    score = result.get("layout_score", {})
    if score.get("score") is not None:
        print(f"layout     : {score['score']}   ({score.get('formula')})")
    else:
        print(f"layout     : — {score.get('reason', '')}")

    integ = result.get("integrity", {})
    for key in ("placeholder_integrity", "coverage", "number_preservation",
                "glossary_adherence", "source_leakage", "script_conformance"):
        node = integ.get(key)
        if isinstance(node, dict):
            rate = node.get("rate")
            detail = f"n={node.get('applicable')}" if rate is not None else node.get("reason", "")
            print(f"  {key:<24} {rate if rate is not None else '—'}   {detail}")

    kiwi = (result.get("quality") or {}).get("comet_kiwi") or {}
    if kiwi.get("mean") is not None:
        print(f"COMET-KIWI : {kiwi['mean']}  (below {kiwi.get('threshold')}: "
              f"{kiwi.get('below_threshold')} of {kiwi.get('scored')})")
    elif kiwi.get("reason"):
        print(f"COMET-KIWI : — {kiwi['reason']}")

    mqm_result = result.get("mqm") or {}
    if mqm_result.get("mqm_score") is not None:
        print(f"MQM        : {mqm_result['mqm_score']}  "
              f"({mqm_result.get('penalty_per_100_words')}/100w, "
              f"{mqm_result.get('critical_errors')} critical)")

    print(f"scorecard  : {md_path}")
    print(f"raw        : {json_path}")


def cmd_jobs(args) -> int:
    store = ReviewStore(args.review_db)
    try:
        jobs = store.list_jobs()
    finally:
        store.close()
    if not jobs:
        print(f"no jobs in {args.review_db}")
        return 0
    print(f"{'job_id':<14}{'fmt':<6}{'segments':<10}source")
    for job in jobs[: args.limit]:
        fmt = (job.get("meta") or {}).get("format", "pdf")
        total = sum((job.get("status_counts") or {}).values())
        print(f"{job['id']:<14}{fmt:<6}{total:<10}{job.get('source')}")
    return 0


def cmd_job(args) -> int:
    result = runner.evaluate_job(
        args.job_id, review_db=args.review_db, lang=args.lang,
        report_json=args.report, export_json=args.export_json, gold_path=args.gold,
        neural=args.neural, with_mqm=args.mqm, with_bleu=args.bleu,
        dpi=args.dpi, pages=args.pages, baseline_pdf=args.baseline,
        gpus=args.gpus, max_segments=args.max_segments,
    )
    _summarise(result, *_write(result, args.out, args.job_id))
    return 0 if result["gates"]["passed"] else 1


def cmd_pdf(args) -> int:
    result = runner.evaluate_pdf_pair(args.source, args.translated, lang=args.lang,
                                      dpi=args.dpi, pages=args.pages,
                                      report_json=args.report)
    stem = os.path.splitext(os.path.basename(args.translated))[0]
    _summarise(result, *_write(result, args.out, stem))
    return 0 if result["gates"]["passed"] else 1


def cmd_idml(args) -> int:
    result = runner.evaluate_idml_pair(args.source, args.translated,
                                       export_json=args.export_json, lang=args.lang)
    stem = os.path.splitext(os.path.basename(args.translated))[0]
    _summarise(result, *_write(result, args.out, stem))
    return 0 if result["gates"]["passed"] else 1


def cmd_gold(args) -> int:
    stats = runner.freeze_gold(args.review_db, args.out, lang=args.lang)
    print(f"gold corpus: {stats['output']}")
    print(f"entries    : {stats['entries']}  (lang: {stats['lang']})")
    if not stats["entries"]:
        print("note       : no approved segments yet — approve some in the review UI, "
              "or score reference-free with COMET-KIWI (--neural)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="babel.eval",
        description="Score a translation job: gates, layout fidelity, content "
                    "integrity, translation quality.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("jobs", help="list job ids in the review DB")
    pl.add_argument("--review-db", default="babel_review.db")
    pl.add_argument("--limit", type=int, default=40)
    pl.set_defaults(func=cmd_jobs)

    pj = sub.add_parser("job", help="score a job from the review DB (recommended)")
    pj.add_argument("job_id")
    pj.add_argument("--review-db", default="babel_review.db")
    pj.add_argument("--out", default="out/eval")
    pj.add_argument("--lang", default=None, choices=sorted(languages.LANGUAGES),
                    help="target language (default: inferred from the output filename)")
    pj.add_argument("--report", default=None,
                    help="pipeline .report.json — its overflow list is ground truth")
    pj.add_argument("--export-json", default=None,
                    help="InDesign export JSON carrying the overset-frame count")
    pj.add_argument("--gold", default=None, help="JSONL gold corpus (see `gold`)")
    pj.add_argument("--neural", action="store_true",
                    help="add COMET-KIWI / COMET (downloads a model, needs torch)")
    pj.add_argument("--mqm", action="store_true",
                    help="add the MQM LLM judge (billed per segment)")
    pj.add_argument("--bleu", action="store_true",
                    help="also report BLEU (regression tracking only)")
    pj.add_argument("--dpi", type=int, default=100, help="render DPI for SSIM")
    pj.add_argument("--pages", type=int, default=None, help="cap pages rendered for SSIM")
    pj.add_argument("--baseline", default=None,
                    help="identity-engine output PDF — splits layout loss into "
                         "reconstruction vs text growth")
    pj.add_argument("--gpus", type=int, default=0)
    pj.add_argument("--max-segments", type=int, default=2000)
    pj.set_defaults(func=cmd_job)

    pp = sub.add_parser("pdf", help="layout-only comparison of two PDFs")
    pp.add_argument("source")
    pp.add_argument("translated")
    pp.add_argument("--out", default="out/eval")
    pp.add_argument("--lang", default=None, choices=sorted(languages.LANGUAGES))
    pp.add_argument("--report", default=None)
    pp.add_argument("--dpi", type=int, default=100)
    pp.add_argument("--pages", type=int, default=None)
    pp.set_defaults(func=cmd_pdf)

    pi = sub.add_parser("idml", help="structural comparison of two IDML packages")
    pi.add_argument("source")
    pi.add_argument("translated")
    pi.add_argument("--out", default="out/eval")
    pi.add_argument("--lang", default=None, choices=sorted(languages.LANGUAGES))
    pi.add_argument("--export-json", default=None)
    pi.set_defaults(func=cmd_idml)

    pg = sub.add_parser("gold", help="freeze approved segments as a gold corpus")
    pg.add_argument("--review-db", default="babel_review.db")
    pg.add_argument("--out", default="docs/eval/gold.jsonl")
    pg.add_argument("--lang", default=None, choices=sorted(languages.LANGUAGES))
    pg.set_defaults(func=cmd_gold)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
