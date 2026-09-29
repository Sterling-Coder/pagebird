"""Shared helper for parsing an LLM's JSON reply.

Used to hold the live post-translation verification pass (a second model
judging every (EN, target) pair, gated by BABEL_VERIFY) that `pipeline.py`
ran after every job. It never blocked shipping — a flagged segment still
went out, just with a note nobody read — so it was pure extra latency and
API cost for no effect, and was removed.

`_strip_fence` is kept: `eval.mqm`'s on-demand QA judge (a separate,
explicitly-requested report, not part of the live pipeline) still needs it
to parse a fenced JSON reply the same way.
"""

from __future__ import annotations


def _strip_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.rstrip().endswith("```"):
            t = t.rsplit("```", 1)[0]
    return t.strip()
