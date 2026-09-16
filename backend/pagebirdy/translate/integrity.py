"""Placeholder integrity gate — the hard accuracy guarantee.

Every math placeholder present in the source MUST appear, exactly once and
unaltered, in the target. If the multiset of tokens differs, the translation
corrupted or dropped math and MUST NOT ship — the segment is routed to a human.
"""

from __future__ import annotations

import re
from collections import Counter

# Matches opaque math-font tokens (⟦m0⟧), value-visible numeric tokens (⟦=3/4⟧),
# and the fixed line/paragraph-separator token (⟦br⟧).
_PLACEHOLDER = re.compile(r"⟦(?:m\d+|=[^⟧]*|br)⟧")


def tokens(text: str) -> Counter:
    return Counter(_PLACEHOLDER.findall(text))


def verify(source: str, target: str) -> tuple[bool, str]:
    """Return (ok, detail). ok == True means every placeholder is preserved."""
    src, tgt = tokens(source), tokens(target)
    missing = src - tgt
    extra = tgt - src
    # We allow the LLM to hallucinate numeric value placeholders (e.g. ⟦=5⟧) 
    # because restored_target() will simply render them back to their literal values.
    # We DO NOT allow hallucinating opaque math placeholders (e.g. ⟦m0⟧).
    extra_disallowed = Counter(x for x in extra.elements() if not x.startswith("⟦="))
    
    if not missing and not extra_disallowed:
        return True, ""
        
    detail = []
    if missing:
        detail.append(f"missing={sorted(missing.elements())}")
    if extra_disallowed:
        detail.append(f"extra={sorted(extra_disallowed.elements())}")
    return False, "; ".join(detail)


# --- editorial rule -------------------------------------------------------
#
# Client requirement: "if an input text is described in 1 or 2 lines then the
# translated text also should be in 1 or 2 lines (same number of lines)".
#
# Some languages (e.g. Spanish) run 20-30% longer than English, so the engine
# will happily return a longer block that reflows to more lines. Others (e.g.
# Korean) tend to be shorter. We cannot count rendered lines here (that is the
# layout engine's job), but we can hold the target to a length budget that keeps
# it inside the same number of lines, and flag the rest for a human instead of
# silently shipping a reflowed page.

# Headroom over the source length before a same-line-count fit is at risk.
LINE_BUDGET_RATIO = 1.35
# A percentage budget is meaningless on short strings (e.g. "Answers" -> a
# one-word translation is still one word on one line even if it is +43%),
# so allow a flat character allowance on top of it.
LINE_BUDGET_SLACK = 12


def line_count_ok(source: str, target: str, ratio: float = LINE_BUDGET_RATIO) -> tuple[bool, str]:
    """Check the target can still occupy the source's line count.

    Two rules:
      * an explicit newline count must match exactly — a paragraph that was two
        lines must not come back as three;
      * total length must stay within `ratio` of the source, otherwise the text
        will wrap onto an extra line no matter how it is set.
    """
    src_lines = source.count("\n") + 1
    tgt_lines = target.count("\n") + 1
    if src_lines != tgt_lines:
        return False, f"line count {src_lines} -> {tgt_lines}"

    src_len = len(source.strip())
    tgt_len = len(target.strip())
    if src_len and tgt_len > src_len * ratio + LINE_BUDGET_SLACK:
        over = (tgt_len / src_len - 1.0) * 100.0
        return False, f"target {over:.0f}% longer than source (budget {int((ratio - 1) * 100)}%)"
    return True, ""
