"""Gates, the layout composite, and the human-readable scorecard.

Gates come before any score, and nothing that is a gate is also a weighted term.
That ordering is the whole design: a weighted average is *compensatory*, so a
document whose every text frame overflows still reports a respectable number if
its vector art survived. Overflow, dropped placeholders, leaked English and
missing glyphs are pass/fail properties of a deliverable, so they are checked as
pass/fail and reported before the score anyone will quote.

The layout composite covers only the three genuinely graded dimensions, and
renormalises over whichever of them could actually be measured — a missing
`scikit-image` must not silently drag the score down.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, NamedTuple

# Weights for the layout composite. Vector preservation leads because a
# rasterized diagram is unusable for print and un-editable in InDesign, which is
# a harder failure than a few points of drift.
LAYOUT_WEIGHTS = {
    "vector_preservation": 0.45,
    "masked_pixel_similarity": 0.30,
    "block_iou": 0.25,
}


class Gate(NamedTuple):
    key: str
    path: tuple[str, ...]
    field: str
    test: Callable[[Any], bool]
    why: str


def _dig(result: dict, path: tuple[str, ...]) -> Any:
    node: Any = result
    for part in path:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


GATES: tuple[Gate, ...] = (
    Gate("placeholder_integrity", ("integrity", "placeholder_integrity"), "rate",
         lambda v: v >= 1.0,
         "a dropped or altered math placeholder means corrupted mathematics"),
    Gate("coverage", ("integrity", "coverage"), "rate",
         lambda v: v >= 0.99,
         "segments that never got a translation. Every other content check only "
         "looks at segments that did translate, so without this gate a document "
         "that is two-thirds untranslated still passes them all"),
    Gate("number_preservation", ("integrity", "number_preservation"), "rate",
         lambda v: v >= 0.99,
         "the shipping gate permits invented numeric placeholders, so this is "
         "the only check that catches a drifted number in prose"),
    Gate("source_leakage", ("integrity", "source_leakage"), "rate",
         lambda v: v >= 0.99,
         "untranslated English left standing in a delivered document"),
    Gate("script_conformance", ("integrity", "script_conformance"), "rate",
         lambda v: v >= 0.99,
         "a non-Latin target containing no target-script characters was not translated"),
    Gate("tofu", ("layout", "tofu"), "rate",
         lambda v: v >= 1.0,
         "characters the target font cannot render ship as empty boxes while the "
         "extracted text still reads correctly"),
    Gate("overflow", ("layout", "overflow"), "rate",
         lambda v: v <= 0.02,
         "text that no longer fits its frame — the client's same-line-count requirement"),
    Gate("idml_overset", ("layout", "overset_frames"), "count",
         lambda v: v == 0,
         "InDesign reports overset text; ground truth for the IDML path"),
    Gate("idml_run_preservation", ("layout", "run_preservation"), "rate",
         lambda v: v >= 1.0,
         "a changed Content-node count means the package was rebuilt wrongly"),
    Gate("idml_math_runs", ("layout", "math_run_preservation"), "rate",
         lambda v: v >= 1.0,
         "math-face runs must come back byte-identical"),
    Gate("idml_assets", ("layout", "asset_preservation"), "rate",
         lambda v: v >= 1.0,
         "a changed Spread or Resource means page geometry moved"),
)


def run_gates(result: dict) -> dict:
    """Evaluate every gate that applies. Absent metrics skip, they never pass.

    `overflow` inverts: its metric is a rate of failures, so the gate is an upper
    bound while every other gate is a lower bound.
    """
    checks = []
    for gate in GATES:
        node = _dig(result, gate.path)
        value = node.get(gate.field) if isinstance(node, dict) else None
        if value is None:
            reason = (node or {}).get("reason") if isinstance(node, dict) else "not measured"
            checks.append({"gate": gate.key, "status": "skip", "value": None,
                           "why": gate.why, "reason": reason or "not measured"})
            continue
        passed = gate.test(value)
        checks.append({"gate": gate.key, "status": "pass" if passed else "fail",
                       "value": value, "why": gate.why})

    failed = [c for c in checks if c["status"] == "fail"]
    return {
        "passed": not failed,
        "checks": checks,
        "failed": [c["gate"] for c in failed],
        "skipped": [c["gate"] for c in checks if c["status"] == "skip"],
    }


def layout_score(layout: dict, fmt: str = "pdf") -> dict:
    """Weighted composite of the three graded layout dimensions.

    Renormalises over available components so an uninstalled `scikit-image`
    lowers confidence rather than the score, and reports which components were
    actually included — a composite whose provenance is hidden is not a metric.

    There is deliberately **no IDML composite**. An IDML is a ZIP of XML, so
    every graded dimension here (vector art, rendered pixels, box geometry)
    is undefined until InDesign lays the document out. The structural
    properties that *can* be checked pre-export — runs, styles, math runs,
    assets — are already gates, and folding a gate into a weighted average is
    exactly the compensatory scoring this module exists to avoid. Inventing a
    number from them would produce a near-constant 1.0 that looks like a
    measurement and is not one.
    """
    parts, weight_used = {}, 0.0
    for key, weight in LAYOUT_WEIGHTS.items():
        node = layout.get(key) or {}
        value = node.get("rate") if key == "vector_preservation" else node.get("mean")
        if value is None:
            continue
        parts[key] = {"value": round(float(value), 4), "weight": weight}
        weight_used += weight

    if not parts:
        if fmt == "idml":
            return {
                "score": None,
                "structural_only": True,
                "reason": "IDML structure is verified by the gates above (runs, "
                          "styles, math runs, assets). Visual fidelity needs an "
                          "InDesign export — then score the exported PDF against "
                          "the source PDF with the same evaluator.",
            }
        return {"score": None, "reason": "no layout component could be measured"}

    score = sum(p["value"] * p["weight"] for p in parts.values()) / weight_used
    return {
        "score": round(score, 4),
        "components": parts,
        "weight_covered": round(weight_used, 2),
        "missing": [k for k in LAYOUT_WEIGHTS if k not in parts],
        "formula": " + ".join(f"{p['weight']}*{k}" for k, p in parts.items())
                   + f" / {round(weight_used, 2)}",
    }


# --- overall accuracy ------------------------------------------------------
#
# One headline number, defined for both document paths. Content is weighted
# above structure because a page that looks perfect while saying the wrong thing
# is the worse failure.
OVERALL_WEIGHTS = {"content": 0.60, "structure": 0.40}

# Integrity metrics that make up the content half. All are 0-1 and oriented so
# that 1.0 is good, so an unweighted mean over whichever were measurable is a
# fair summary.
CONTENT_METRICS = (
    "placeholder_integrity",
    "coverage",
    "number_preservation",
    "glossary_adherence",
    "source_leakage",
    "script_conformance",
)

# The IDML path's structural half. The PDF path uses its layout composite.
IDML_STRUCTURE_METRICS = (
    "run_preservation",
    "style_preservation",
    "math_run_preservation",
    "asset_preservation",
)


def _mean_rates(section: dict, keys) -> tuple[float | None, list[str]]:
    """Mean of whichever named rates were actually measured, plus their names."""
    values, used = [], []
    for key in keys:
        node = section.get(key)
        if not isinstance(node, dict):
            continue
        value = node.get("rate")
        if isinstance(value, (int, float)):
            values.append(float(value))
            used.append(key)
    return (sum(values) / len(values) if values else None), used


def overall_score(result: dict) -> dict:
    """A single accuracy figure, defined for both the PDF and IDML paths.

    Content (60%) is the mean of the measurable integrity rates; structure (40%)
    is the PDF layout composite, or the mean of the IDML structural rates. Only
    the halves that could be measured are counted, and the weights renormalise
    over them, so an uninstalled optional dependency lowers confidence rather
    than the score.

    **This number is reported with `gates_passed` attached and must never be
    shown without it.** It is a mean, so it is compensatory by construction: the
    document measured while writing this scored 97.4% overall while failing the
    untranslated-source gate with 37 English segments still in a Spanish
    deliverable. The average is a useful trend line across versions; the gates
    are what decide whether a document ships.
    """
    integrity = result.get("integrity") or {}
    layout = result.get("layout") or {}
    fmt = result.get("format", "pdf")

    content, content_used = _mean_rates(integrity, CONTENT_METRICS)

    if fmt == "idml":
        structure, structure_used = _mean_rates(layout, IDML_STRUCTURE_METRICS)
        structure_from = "IDML structural metrics"
    else:
        structure = (result.get("layout_score") or {}).get("score")
        structure_used = list((result.get("layout_score") or {}).get("components", {}))
        structure_from = "PDF layout composite"

    halves = {}
    if content is not None:
        halves["content"] = {"value": round(content, 4),
                             "weight": OVERALL_WEIGHTS["content"],
                             "metrics": content_used}
    if isinstance(structure, (int, float)):
        halves["structure"] = {"value": round(float(structure), 4),
                               "weight": OVERALL_WEIGHTS["structure"],
                               "source": structure_from,
                               "metrics": structure_used}

    gates = result.get("gates") or {}
    if not halves:
        return {"score": None, "reason": "nothing measurable",
                "gates_passed": bool(gates.get("passed"))}

    weight_used = sum(h["weight"] for h in halves.values())
    score = sum(h["value"] * h["weight"] for h in halves.values()) / weight_used

    return {
        "score": round(score, 4),
        "halves": halves,
        "weight_covered": round(weight_used, 2),
        "missing": [k for k in OVERALL_WEIGHTS if k not in halves],
        # Always travels with the score. A mean cannot express "this must not
        # ship", so the verdict has to ride alongside it everywhere it is shown.
        "gates_passed": bool(gates.get("passed")),
        "gates_failed": list(gates.get("failed") or []),
    }


def baseline_delta(translated: dict, baseline: dict) -> dict:
    """Split layout loss into reconstruction loss and text-growth loss.

    `baseline` is the same document run through the identity engine (no API keys
    → passthrough), i.e. English in, English out. Its layout score is the
    reconstruction ceiling, so:

        1.0 - ceiling            = damage the pipeline does regardless of language
        ceiling - translated     = damage caused by the target text being longer

    Two numbers, two different owners. Blended into one score, neither is
    actionable — which is why a bare layout score is close to uninterpretable.
    """
    ceiling = (baseline or {}).get("score")
    got = (translated or {}).get("score")
    if ceiling is None or got is None:
        return {"available": False,
                "reason": "needs a layout score for both the identity-engine "
                          "baseline and the translated run"}
    return {
        "available": True,
        "reconstruction_ceiling": ceiling,
        "translated_score": got,
        "reconstruction_loss": round(1.0 - ceiling, 4),
        "text_growth_loss": round(ceiling - got, 4),
    }


# --- rendering -------------------------------------------------------------


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def _rate_rows(section: dict, keys: tuple[str, ...]) -> list[str]:
    rows = []
    for key in keys:
        node = section.get(key)
        if not isinstance(node, dict):
            continue
        rate = node.get("rate", node.get("mean", node.get("count")))
        detail = node.get("reason") or f"n={node.get('applicable', node.get('scored', '—'))}"
        rows.append(f"| {key} | {_fmt(rate)} | {detail} |")
    return rows


def _stamp(epoch: Any) -> str:
    if not isinstance(epoch, (int, float)):
        return "unknown"
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def render_markdown(result: dict) -> str:
    """A scorecard a reviewer can read and a client can be shown.

    Written to stand alone once downloaded: it carries the document names, the
    evaluation date, and — where a metric could not be measured — the reason,
    so nobody reads a blank as a zero.
    """
    gates = result.get("gates", {})
    title = result.get("original_filename") or result.get("source") or result.get("job_id")
    out: list[str] = [
        f"# Accuracy report — {title}",
        "",
        f"- job: `{result.get('job_id', '—')}`  ",
        f"- format: **{result.get('format', '?')}**  ",
        f"- target language: **{result.get('target_lang', '?')}**  ",
        f"- segments: **{result.get('integrity', {}).get('segments', '?')}**  ",
        f"- source: `{result.get('source', '?')}`  ",
        f"- output: `{result.get('output', '?')}`  ",
        f"- evaluated: {_stamp(result.get('evaluated_at'))}",
        "",
    ]

    overall = result.get("overall") or {}
    if isinstance(overall.get("score"), (int, float)):
        halves = overall.get("halves", {})
        breakdown = " · ".join(f"{name} {half['value'] * 100:.1f}%"
                               for name, half in halves.items())
        out += [
            f"## Overall accuracy — {overall['score'] * 100:.1f}%",
            "",
            f"{breakdown} — content weighted 60%, structure 40%.",
            "",
            "This is a mean, so it is compensatory by construction: it cannot "
            "express \"must not ship\". Read it with the gate verdict below, "
            "never on its own.",
            "",
        ]

    out += [
        f"## Gates — {'PASS' if gates.get('passed') else 'FAIL'}",
        "",
        "Pass/fail properties of the deliverable. Deliberately not averaged into "
        "a score: a weighted mean is compensatory, so one catastrophic failure "
        "can hide behind several good numbers. A **SKIP** row was not measured — "
        "it is not a pass.",
        "",
        "| gate | status | value | why it is a gate |",
        "|---|---|---|---|",
    ]
    for check in gates.get("checks", []):
        note = check["why"] if check["status"] != "skip" else f"skipped: {check.get('reason')}"
        out.append(f"| {check['gate']} | {check['status'].upper()} | "
                   f"{_fmt(check['value'])} | {note} |")

    score = result.get("layout_score", {})
    out += ["", "## Structure" if score.get("structural_only") else "## Layout", ""]
    if score.get("score") is None:
        # No composite exists for this format, or nothing could be measured —
        # either way the reason belongs in the report, not a bare dash.
        out += [score.get("reason", "not measured"), ""]
    else:
        out += [f"composite: **{_fmt(score.get('score'))}**"
                + (f"  (`{score['formula']}`)" if score.get("formula") else ""), ""]
    if score.get("missing"):
        out.append(f"not measured: {', '.join(score['missing'])}")
        out.append("")
    out += ["| metric | value | detail |", "|---|---|---|"]
    out += _rate_rows(result.get("layout", {}),
                      ("vector_preservation", "masked_pixel_similarity", "block_iou",
                       "tofu", "overflow", "run_preservation", "style_preservation",
                       "math_run_preservation", "run_translation", "asset_preservation",
                       "overset_frames"))

    delta = result.get("baseline_delta", {})
    if delta.get("available"):
        out += ["", f"reconstruction ceiling **{_fmt(delta['reconstruction_ceiling'])}** "
                    f"→ reconstruction loss {_fmt(delta['reconstruction_loss'])}, "
                    f"text-growth loss {_fmt(delta['text_growth_loss'])}"]

    out += ["", "## Content integrity", "", "| metric | value | detail |", "|---|---|---|"]
    out += _rate_rows(result.get("integrity", {}),
                      ("placeholder_integrity", "coverage", "number_preservation",
                       "glossary_adherence", "source_leakage", "script_conformance",
                       "language_id"))
    length = result.get("integrity", {}).get("length_ratio", {})
    if length.get("applicable"):
        out.append(f"| length_ratio (median) | {_fmt(length.get('median'))} | "
                   f"p90 {_fmt(length.get('p90'))}, "
                   f"{length.get('over_line_budget')} over the "
                   f"{length.get('line_budget_ratio')} line budget |")

    quality = result.get("quality", {})
    if quality:
        out += ["", "## Translation quality", "", "| metric | value | detail |", "|---|---|---|"]

        kiwi = quality.get("comet_kiwi", {})
        detail = kiwi.get("reason") or (
            "n={}, below {}: {}".format(kiwi.get("scored"), kiwi.get("threshold"),
                                        kiwi.get("below_threshold")))
        out.append(f"| COMET-KIWI (reference-free) | {_fmt(kiwi.get('mean'))} | {detail} |")

        cm = quality.get("comet", {})
        detail = cm.get("reason") or "n={}".format(cm.get("scored"))
        out.append(f"| COMET (reference-based) | {_fmt(cm.get('mean'))} | {detail} |")

        surf = quality.get("surface", {})
        detail = surf.get("reason") or "n={}, TER {}".format(surf.get("matched"),
                                                            _fmt(surf.get("ter")))
        out.append(f"| chrF++ | {_fmt(surf.get('chrf2'))} | {detail} |")

    mqm_result = result.get("mqm", {})
    if mqm_result.get("available") and mqm_result.get("scored"):
        out += ["", "## MQM (LLM judge)", "",
                f"score **{_fmt(mqm_result.get('mqm_score'))}** — "
                f"{_fmt(mqm_result.get('penalty_per_100_words'))} penalty per 100 words, "
                f"{mqm_result.get('critical_errors')} critical, "
                f"judge `{mqm_result.get('judge')}`", ""]
        if mqm_result.get("by_category"):
            out += ["| category | errors |", "|---|---|"]
            out += [f"| {k} | {v} |" for k, v in mqm_result["by_category"].items()]

    return "\n".join(out) + "\n"
