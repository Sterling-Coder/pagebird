"""Evaluation suite: how accurate was a translation job, and where did it lose?

Three orthogonal axes, deliberately never blended into one number:

  * axis B — content integrity (`integrity.py`): did anything get lost, invented,
    or left untranslated? Deterministic, no dependencies, no network. Run always.
  * axis C — layout fidelity (`layout_pdf.py`, `layout_idml.py`): does the output
    document still look/behave like the source? Raster + geometry for the PDF
    path, XML structure + overset for the IDML path.
  * axis A — translation quality (`quality.py`, `mqm.py`): is the target text
    right? Neural metrics (COMET / COMET-KIWI / chrF++) and an MQM-typed LLM
    judge. Optional dependencies; both degrade to `available: false`.

`scorecard.py` turns the three into gates (binary, must pass) plus a layout
score. Gates come first on purpose: overflow and placeholder integrity are
pass/fail properties, and averaging them into a weighted score lets a document
whose every text frame overflows still report "0.85".

Entry points: `evaluate_job` (anything in the review DB) and the file-pair
helpers. CLI: `python -m babel.eval --help`.

Nothing in this package imports from or mutates the pipeline — evaluation is a
read-only observer, so it can be pointed at jobs that already shipped.
"""

from __future__ import annotations

from babel.eval.runner import (
    evaluate_idml_pair,
    evaluate_job,
    evaluate_pdf_pair,
    freeze_gold,
)
from babel.eval.scorecard import GATES, layout_score, render_markdown, run_gates

__all__ = [
    "evaluate_job",
    "evaluate_pdf_pair",
    "evaluate_idml_pair",
    "freeze_gold",
    "run_gates",
    "layout_score",
    "render_markdown",
    "GATES",
]
