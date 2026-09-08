"""The accuracy scorecard as a PDF — the client-facing artefact.

Rendered with `fitz.Story`, PyMuPDF's HTML/CSS layout engine, so this needs no
dependency the project does not already have (PyMuPDF is the PDF pipeline's
core). Story paginates on its own: we place repeatedly until it reports no more
content, which is what makes a 10-gate report and a 40-metric one both work.

Two details that matter:

  * **Fonts.** Story's built-ins are Base-14 (Latin only), so a Korean filename
    or a Spanish example would render as empty boxes — the exact defect the
    `tofu` metric exists to catch. The target language's own face from
    `languages.py` is embedded instead, which covers both the target script and
    Latin.
  * **Skipped vs failed.** A skipped check is drawn grey with its reason, never
    as a pass or a zero. A report that overstates what it verified is worse
    than no report.
"""

from __future__ import annotations

import html
import io
import os

import fitz

from babel import languages  # noqa: F401  (used for the spelled-out language name)

# Same labels the review UI shows, so a downloaded report and the screen agree.
GATE_LABELS = {
    "placeholder_integrity": "Math placeholders intact",
    "coverage": "Segments translated",
    "number_preservation": "Numbers preserved",
    "source_leakage": "No untranslated source text",
    "script_conformance": "Target script used",
    "tofu": "All characters renderable",
    # Shown inverted (see `_INVERTED`) so it reads higher-is-better like every
    # other figure. The label has to match the number: with the value flipped,
    # "Overflowing text — 100%" would be exactly backwards.
    "overflow": "Text fits its box",
    "idml_overset": "No overset frames (InDesign)",
    "idml_run_preservation": "IDML runs preserved",
    "idml_math_runs": "IDML math runs untouched",
    "idml_assets": "IDML assets untouched",
}

LAYOUT_ROWS = [
    ("vector_preservation", "Vector art preserved"),
    ("masked_pixel_similarity", "Pixel similarity (text masked)"),
    ("block_iou", "Text blocks in place"),
    ("tofu", "All characters renderable"),
    ("overflow", "Text fits its box"),
    ("run_preservation", "IDML runs preserved"),
    ("style_preservation", "IDML styles preserved"),
    ("math_run_preservation", "IDML math runs untouched"),
    ("run_translation", "IDML runs translated"),
    ("asset_preservation", "IDML assets untouched"),
    ("overset_frames", "Overset frames (InDesign)"),
]

INTEGRITY_ROWS = [
    ("placeholder_integrity", "Math placeholders intact"),
    ("coverage", "Segments translated"),
    ("number_preservation", "Numbers preserved"),
    ("glossary_adherence", "Glossary adherence"),
    ("source_leakage", "No untranslated source"),
    ("script_conformance", "Target script used"),
    ("language_id", "Detected language correct"),
]

_CSS = """
* { font-family: body; }
h1 { font-size: 16px; margin: 0 0 3px 0; }
h2 { font-size: 11px; color: #1F4E79; margin: 22px 0 8px 0; }
p { font-size: 8.5px; margin: 0 0 5px 0; }
p.meta { color: #6b7280; font-size: 8px; margin: 0 0 2px 0; }
p.note { color: #6b7280; font-size: 8px; margin: 4px 0 10px 0; }
p.verdict-pass { color: #15803d; font-size: 12px; font-weight: bold; margin: 14px 0 4px 0; }
p.verdict-fail { color: #dc2626; font-size: 12px; font-weight: bold; margin: 14px 0 4px 0; }
p.overall { font-size: 18px; margin: 18px 0 3px 0; }
p.lead { font-size: 9.5px; margin: 10px 0 9px 0; }
ul.lead { font-size: 9.5px; margin: 0 0 10px 0; }
li { font-size: 9.5px; margin: 0 0 4px 0; }

/* Ruled tables: every figure sits in its own cell with a visible boundary, so a
   long reason in the last column cannot be misread as belonging to the row
   above or below. `border-collapse` is required — without it Story draws a
   separate box per cell and the rules double up. */
table { width: 100%; margin: 6px 0 14px 0; border-collapse: collapse; }
/* No background fill on the header: Story leaks table-cell shading onto later
   pages as stray grey bars. Weight and rule colour carry the header instead. */
th { font-size: 7.5px; color: #4b5563; text-align: left; font-weight: bold;
     border: 1px solid #c8d0da; padding: 4px 6px; }
td { font-size: 8.5px; border: 1px solid #d9e0e8; padding: 4px 6px; }
td.num { text-align: right; }
td.pass { color: #15803d; font-weight: bold; }
td.fail { color: #dc2626; font-weight: bold; }
td.skip { color: #9ca3af; }
tr.skip td { color: #9ca3af; }
td.why { color: #6b7280; font-size: 8px; }

/* The glossary at the end is read top to bottom, so each entry is a stanza:
   the metric name in bold, its explanation in normal weight, the formula
   indented beneath, then a rule before the next one. The rule is what stops the
   definitions reading as one continuous wall of text. */
p.def { font-size: 8.5px; font-weight: normal;
        margin: 0 0 4px 0; padding: 11px 0 0 0;
        border-top: 1px solid #e3e8ee; }
p.def b { font-weight: bold; }
/* The rule sits above the term, not below the formula, so an entry whose
   explanation carries several formula lines stays one block instead of being
   sliced between them. */
p.defformula { font-family: mono; font-size: 7.5px; color: #1F4E79;
               margin: 0 0 5px 14px; }
"""


# `scorecard.GATES` states each reason for a developer reading the code — it
# names internal gates and design decisions. This report goes to whoever ordered
# the translation, so the same reasons are given here in their terms: what breaks
# in the finished document if the check fails.
GATE_WHY: dict[str, str] = {
    "placeholder_integrity":
        "a lost or altered formula means the mathematics on the page is wrong",
    "coverage":
        "text that never got translated is still sitting there in English",
    "number_preservation":
        "a figure that changed or vanished inside a sentence",
    "source_leakage":
        "whole sentences left in English in a document delivered as translated",
    "script_conformance":
        "output that should be in the target alphabet but is not",
    "tofu":
        "characters the font cannot print, which appear as empty boxes on the page",
    "overflow":
        "text that no longer fits its box, which breaks the agreed line count",
    "idml_overset":
        "text hidden inside a box that does not appear on the printed page",
    "idml_run_preservation":
        "text pieces lost while rebuilding the file, which destroys the formatting",
    "idml_math_runs":
        "a formula that was sent to the translator and came back as words",
    "idml_assets":
        "page layouts or linked images that changed, moving the page geometry",
}

# Checks that exist only for InDesign files. On a PDF they are not merely
# unmeasured — they are meaningless, which is a different thing to tell a reader.
_INDESIGN_ONLY = {
    "idml_overset", "idml_run_preservation", "idml_math_runs", "idml_assets",
    "overset_frames", "run_preservation", "math_run_preservation",
    "asset_preservation",
}

# What a PDF loses by skipping an InDesign-only check: nothing, and here is why.
_NOT_ON_PDF: dict[str, str] = {
    "idml_overset": "a PDF cannot have overset text",
    "overset_frames": "a PDF cannot have overset text",
    "idml_run_preservation": "a PDF has no text runs to lose",
    "run_preservation": "a PDF has no text runs to lose",
    "idml_math_runs": "this is covered by the formula check above",
    "math_run_preservation": "this is covered by the formula check above",
    "idml_assets": "a PDF has no separate layout files",
    "asset_preservation": "a PDF has no separate layout files",
}


# A reason alone leaves the reader asking "so does that matter?". Each skipped
# check therefore also states what is and is not covered as a result.
# A check whose sample size is zero found nothing to look at. That is a
# different statement from "we could not run it", and says so.
NOTHING_TO_CHECK: dict[str, str] = {
    "idml_math_runs": "this document contains no formulas, so there was nothing "
                      "to check",
    "math_run_preservation": "this document contains no formulas, so there was "
                             "nothing to check",
    "placeholder_integrity": "this document contains no formulas or numbers to "
                             "protect",
    "number_preservation": "this document contains no numbers",
    "glossary_adherence": "no line in this document uses a term from the "
                          "approved list",
    "script_conformance": "no line in this document has words to check",
    "source_leakage": "no line in this document has enough words to compare",
}

SKIP_IMPACT: dict[str, str] = {
    "idml_overset": "text that does not fit its box would go unnoticed until "
                    "someone opens the file in InDesign",
    "overset_frames": "text that does not fit its box would go unnoticed until "
                      "someone opens the file in InDesign",
    "idml_run_preservation": "lost text would go unnoticed until the file is opened",
    "idml_assets": "moved page geometry would go unnoticed until the file is opened",
    "script_conformance": "nothing is missed: the untranslated-text check covers "
                          "this for Latin-alphabet languages",
    "language_id": "the untranslated-text check still catches text left in "
                   "English, though less precisely",
    "glossary_adherence": "wording is still checked, but nobody is verifying that "
                          "agreed terms were used consistently",
    "tofu": "unprintable characters can only be seen once InDesign has produced "
            "the final PDF",
    "overflow": "text that does not fit is reported as overset frames instead, "
                "which needs an InDesign export",
    "masked_pixel_similarity": "the layout score is made up from the remaining "
                               "checks, which count for more to make up for it",
}


# A check that was skipped is one of two entirely different things, and the
# report used to call both "SKIPPED":
#
#   not_applicable  — the check cannot apply. A PDF has no overset frames; a
#                     Spanish document has no non-Latin alphabet to verify.
#                     Nothing is missed and there is nothing to do.
#   action_required — the check would apply, but something has not been set up.
#                     Real coverage is missing and somebody has to act.
#
# Collapsing the two hides genuine gaps behind a wall of harmless ones.
NOT_APPLICABLE = "not_applicable"
ACTION_REQUIRED = "action_required"

# Checks to leave out of the report entirely when they are not in use. A term
# list that has never been written is a decision nobody has taken yet, not a
# finding about this document — printing an empty row for it only adds a line
# the reader has to work out and discard.
OMIT_WHEN_UNAVAILABLE = {"glossary_adherence"}

# What has to happen for an unconfigured check to start running.
OPEN_ITEM_ACTION: dict[str, str] = {
    "glossary_adherence":
        "Write an approved term list for this language. Until then nothing "
        "verifies that agreed terminology is used consistently. Matching is by "
        "whole word and ignores capitalisation; on the translated side a short "
        "word ending is allowed, so a plural or inflected form still counts as "
        "the approved term. Agree that rule before the list is switched on.",
    "language_id":
        "Install the optional language-detection component. The untranslated-text "
        "check still catches English left in place, but less precisely.",
    "masked_pixel_similarity":
        "Install the optional image-comparison component. The layout score is "
        "currently made from the remaining two checks, which count for more.",
    "tofu":
        "Export the document from InDesign, then run this report against the "
        "exported PDF. Unprintable characters cannot be seen before then.",
    "overflow":
        "Export the document from InDesign. Text that does not fit is reported "
        "as overset frames, which only InDesign can count.",
    "overset_frames":
        "Export the document from InDesign so overset text can be counted.",
    "idml_overset":
        "Export the document from InDesign so overset text can be counted.",
    "idml_run_preservation":
        "Export the document from InDesign to confirm no text runs were lost.",
    "idml_math_runs":
        "Export the document from InDesign to confirm formulas were left alone.",
    "idml_assets":
        "Export the document from InDesign to confirm page geometry is unchanged.",
}


def _skip_kind(gate: str, raw: str | None, fmt: str = "pdf",
               applicable: int | None = None) -> str:
    """Whether a skipped check is harmless or a real gap someone must close."""
    text = (raw or "").strip()
    recorded = text and text != "not measured"
    is_indesign = fmt in ("idml", "indd")

    if gate in _INDESIGN_ONLY and not is_indesign:
        return NOT_APPLICABLE          # a PDF cannot have these problems
    if applicable == 0 and not recorded:
        return NOT_APPLICABLE          # ran, found nothing to look at
    if "Latin-script" in text:
        return NOT_APPLICABLE          # no non-Latin alphabet to verify
    return ACTION_REQUIRED


def _skip_reason(gate: str, raw: str | None, target_name: str,
                 fmt: str = "pdf", applicable: int | None = None) -> str:
    """Why a check did not run, and what that means for the reader.

    Reads as "<reason> — <what is or is not covered as a result>", so a skipped
    row never leaves the question "should I be worried about that?" open.

    The same check skips for different reasons depending on the file: an
    InDesign-only check is meaningless on a PDF, but on an IDML it simply has
    not been measured yet because nobody has run the export.
    """
    is_indesign = fmt in ("idml", "indd")
    text = (raw or "").strip()
    recorded = text and text != "not measured"

    # A check with nothing to look at did run; it simply found no candidates.
    # Only claim that when nothing better was recorded — a metric that reports a
    # missing package also reports a sample size of zero, and there the package
    # is the real answer.
    if applicable == 0 and not recorded:
        return NOTHING_TO_CHECK.get(
            gate, "this document contains nothing this check applies to")

    if gate in _INDESIGN_ONLY and not is_indesign:
        why = _NOT_ON_PDF.get(gate)
        reason = "only applies to InDesign files, and this is a PDF"
        return f"{reason} — nothing is missed: {why}" if why else reason

    # The stored reason names language codes and internal metric names.
    if not recorded:
        reason = ("needs an InDesign export, which has not been run"
                  if gate in _INDESIGN_ONLY else "does not apply to this document")
    elif "Latin-script" in text:
        reason = (f"{target_name} is written in the Latin alphabet, so this "
                  f"check does not apply")
    elif "pip install" in text:
        reason = "an optional component is not installed on this machine"
    elif "InDesign" in text:
        reason = "needs an InDesign export, which has not been run"
    elif "no glossary" in text:
        reason = f"no approved term list has been written for {target_name} yet"
    else:
        reason = text

    impact = SKIP_IMPACT.get(gate)
    return f"{reason} — {impact}" if impact else reason


# Metrics where a figure below 100% is not a fault. Reporting "155 of 294
# affected" for how much text changed reads as damage when it is just a count.
_INFORMATIONAL = {"run_translation"}


# Layout metrics count things other than pieces of text, and record the count
# under their own field name rather than `applicable`.
_COUNT_FIELD = {
    "vector_preservation": "src_drawings",
    "block_iou": "src_boxes",
    "masked_pixel_similarity": "pages_scored",
    "overflow": "of_segments",
    "run_preservation": "src_runs",
    "overset_frames": "count",
}


def _sample(metric: dict, key: str) -> int | None:
    """How many things this check looked at, whatever the metric calls them."""
    total = metric.get("applicable")
    if isinstance(total, int):
        return total
    total = metric.get(_COUNT_FIELD.get(key, ""))
    return total if isinstance(total, int) else None


def _open_items(gates: dict, layout: dict, integrity: dict, target_name: str,
                fmt: str) -> list[tuple[str, str, str]]:
    """Checks that would apply here but have not been set up.

    Gathered from the gates *and* from the metric tables: several unconfigured
    checks — the glossary, the language detector, the image comparison — are not
    gates at all, so collecting only from the gate list would report an empty
    list on a document that has real gaps.
    """
    labels = dict(LAYOUT_ROWS + INTEGRITY_ROWS)
    items: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    def consider(key: str, node: dict, label: str) -> None:
        if key in seen or _measured(node) or key in OMIT_WHEN_UNAVAILABLE:
            return
        total = _sample(node, key)
        if _skip_kind(key, node.get("reason"), fmt, total) != ACTION_REQUIRED:
            return
        seen.add(key)
        items.append((label,
                      _skip_reason(key, node.get("reason"), target_name, fmt, total),
                      OPEN_ITEM_ACTION.get(key, "")))

    for check in gates.get("checks", []):
        if check.get("status") != "skip":
            continue
        gate = check.get("gate", "")
        # A gate reads a metric; look the metric up so its recorded reason and
        # sample size are used rather than the gate's thinner record.
        base = gate[5:] if gate.startswith("idml_") else gate
        node = layout.get(base) or integrity.get(base) or {"reason": check.get("reason")}
        consider(gate, node, GATE_LABELS.get(gate, gate))

    for section, rows in ((layout, LAYOUT_ROWS), (integrity, INTEGRITY_ROWS)):
        for key, label in rows:
            node = section.get(key)
            if isinstance(node, dict):
                consider(key, node, labels.get(key, label))
    return items


def _justify(metric: dict, key: str = "") -> str:
    """What this number means for the document, in words rather than counts.

    Deliberately no sample sizes: a reader who is handed "all 46 passed" under a
    document of 848 assumes 802 pieces were ignored. Each check only looks at
    the text it applies to, and saying so plainly beats printing a denominator
    that invites the wrong conclusion.
    """
    rate = metric.get("rate")
    if not isinstance(rate, (int, float)):
        rate = metric.get("mean")
    if not isinstance(rate, (int, float)):
        return ""
    if key in _INFORMATIONAL:
        return "for information only"
    # The overflow metric counts failures, so its "affected" is the rate itself.
    bad = rate if key in _INVERTED else 1.0 - rate
    if bad <= 0.0005:
        return "no problems found"
    if bad < 0.05:
        return "a small amount of text affected"
    if bad < 0.25:
        return "some text affected"
    return "a large part of the text affected"


# What a failed check means for the finished document, as a sentence. The reader
# should be able to act on this without reading the tables underneath.
FAILURE_PLAIN: dict[str, str] = {
    "placeholder_integrity":
        "some formulas or numbers did not survive translation, so the mathematics "
        "printed on the page is wrong in places",
    "coverage":
        "a large part of the document was never translated and is still in English",
    "number_preservation":
        "a number changed or went missing inside a sentence",
    "source_leakage":
        "whole sentences are still in English",
    "script_conformance":
        "some text is not written in the target alphabet, which means it was not "
        "translated",
    "tofu":
        "some characters cannot be printed by the font and will appear as empty "
        "boxes on the page",
    "overflow":
        "some text no longer fits inside its box",
    "idml_overset":
        "some text is hidden inside a box and will not appear when printed",
    "idml_run_preservation":
        "pieces of text were lost while rebuilding the file, which damages the "
        "formatting",
    "idml_math_runs":
        "a formula was translated when it should have been left alone",
    "idml_assets":
        "page layouts or linked images changed, so the page geometry has moved",
}


def _summary(result: dict, gates: dict, target_name: str) -> str:
    """A short plain-language verdict, before any table.

    Someone who ordered the translation should be able to read the top of this
    page and know whether they can send the document out, and if not, what is
    wrong with it — without reading a percentage or a table.
    """
    checks = gates.get("checks", [])
    failed = [c for c in checks if c.get("status") == "fail"]
    passed = [c for c in checks if c.get("status") == "pass"]

    lines = [
        f"<p class='lead'>This report compares the {_esc(target_name)} version of "
        f"the document against the English original (source language).</p>"
    ]

    # Nothing is said when every check passed: the verdict line and the table
    # below already carry that, and repeating it in a sentence only adds bulk.
    # A failure does get spelled out, because the reader has to know what to fix.
    if failed:
        problems = "".join(
            f"<li>{_esc(FAILURE_PLAIN.get(c.get('gate', ''), c.get('why', '')))}</li>"
            for c in failed)
        lines.append(
            f"<p class='lead'><b>This document is not ready to hand over.</b> "
            f"{'A problem was' if len(failed) == 1 else 'Problems were'} "
            f"found:</p><ul class='lead'>{problems}</ul>")

    return "".join(lines)


def _esc(value) -> str:
    return html.escape(str(value), quote=False)


# Every figure in this report is higher-is-better except the overflow rate, and
# a lone "0.0%" in a column of 100.0%s reads as a zero score however carefully
# the footnote explains it. So it is shown inverted, as the share of text that
# does fit. The gate still tests the underlying rate.
_INVERTED = {"overflow"}

# Why a row's denominator is not the document total. Without this, "all 46
# passed" under a stated total of 848 reads as 802 pieces quietly ignored.
DENOMINATOR: dict[str, str] = {
    "placeholder_integrity": "pieces that were translated",
    "coverage": "every piece of text in the document",
    "number_preservation": "pieces that contain a number",
    "glossary_adherence": "pieces that use a term from the approved list",
    "source_leakage": "pieces with at least two real words to compare",
    "script_conformance": "pieces with words to check",
    "language_id": "pieces long enough to identify a language from",
    "tofu": "pieces that carry text",
    "overflow": "every piece of text in the document",
    "run_preservation": "text runs in the file",
    "style_preservation": "text runs compared",
    "math_run_preservation": "text runs set in a maths font",
    "run_translation": "text runs that could be translated",
    "asset_preservation": "files in the package that are not text",
    "vector_preservation": "drawings in the source document",
    "block_iou": "blocks of text on the page",
    "masked_pixel_similarity": "pages compared",
}


def _pct(metric: dict, key: str = "") -> str:
    """Rates and means as percentages; counts as counts; anything else a dash."""
    for field in ("rate", "mean"):
        value = metric.get(field)
        if isinstance(value, (int, float)):
            if key in _INVERTED:
                value = 1.0 - value
            return f"{value * 100:.1f}%"
    if isinstance(metric.get("count"), (int, float)):
        return str(metric["count"])
    return "—"


def _measured(metric: dict) -> bool:
    return any(isinstance(metric.get(k), (int, float)) for k in ("rate", "mean", "count"))


def _font_css(lang: str | None) -> tuple[str, fitz.Archive | None]:
    """Embed the target language's faces so non-Latin text is not drawn as boxes.

    The bold face is registered separately and deliberately: Story does not
    synthesise a heavier weight from a single file, so with only the regular
    face declared every `<b>` renders at normal weight and the headings in the
    glossary are indistinguishable from the prose under them.
    """
    try:
        faces = languages.get(lang).fonts
    except ValueError:
        faces = {}

    def first(style: str) -> str | None:
        return next((p for p in faces.get(style, []) if os.path.exists(p)), None)

    regular = first("regular")
    if not regular:
        # Base-14 fallback. Latin-only, but better than failing the download.
        return "* { font-family: sans-serif; }\n", None

    css = f"@font-face {{ font-family: body; src: url({os.path.basename(regular)}); }}\n"
    bold = first("bold")
    # Only useful when it is a genuinely different file — the CJK registry maps
    # some scripts to one face for every weight.
    if bold and bold != regular:
        css += (f"@font-face {{ font-family: body; font-weight: bold; "
                f"src: url({os.path.basename(bold)}); }}\n")
    archive = fitz.Archive(os.path.dirname(regular))
    if bold and os.path.dirname(bold) != os.path.dirname(regular):
        archive.add(os.path.dirname(bold))
    return css, archive


def _metric_table(section: dict, rows: list[tuple[str, str]],
                  target_name: str = "", fmt: str = "pdf") -> str:
    present = [(key, label, section.get(key)) for key, label in rows
               if isinstance(section.get(key), dict)
               and not (key in OMIT_WHEN_UNAVAILABLE
                        and not _measured(section[key]))]
    if not present:
        return "<p class='note'>Nothing measured.</p>"

    out = ["<table><tr><th>check</th><th>result</th><th>what it looked at</th>"
           "<th>what that means</th></tr>"]
    for key, label, metric in present:
        measured = _measured(metric)
        klass = "" if measured else " class='skip'"
        total = _sample(metric, key)

        # What the check looked at, described rather than counted. The count is
        # what made a reader think the rest of the document had been ignored.
        looked_at = _esc(DENOMINATOR.get(key, "")) if measured else "—"

        if measured:
            detail = _esc(_justify(metric, key))
        else:
            kind = _skip_kind(key, metric.get("reason"), fmt, total)
            tag = ("Not applicable" if kind == NOT_APPLICABLE
                   else "Not set up")
            detail = (f"<b>{tag}.</b> " + _esc(
                _skip_reason(key, metric.get("reason"), target_name, fmt, total)))

        out.append(
            f"<tr{klass}><td>{_esc(label)}</td>"
            f"<td class='num'>{_pct(metric, key)}</td>"
            f"<td class='why'>{looked_at}</td>"
            f"<td class='why'>{detail}</td></tr>"
        )
    out.append("</table>")
    return "".join(out)


# Plain-language definition per metric, for the glossary at the end of the
# report. Keyed by the metric key so the glossary can be built from whatever this
# particular document actually measured — a PDF report should not carry
# definitions for IDML checks it never ran.
# (plain explanation, formula). The formula is shown under the explanation so a
# reader can check the arithmetic without leaving the report.
EXPLANATIONS: dict[str, tuple[str, str]] = {
    # gates + content
    "placeholder_integrity": (
        "Formulas and numbers are set aside before translating and put back "
        "afterwards, so the translator cannot change them. This confirms they all "
        "came back.",
        "pieces of text with every formula intact / pieces translated x 100",
    ),
    "coverage": (
        "Did every piece of text actually get translated? Anything missed stays "
        "on the page in English.",
        "pieces of text that were translated / total pieces x 100",
    ),
    "number_preservation": (
        "Every number in the original is looked for in the translation. Only "
        "missing numbers count against the score — an added one is usually "
        "correct, as when \"Five boxes\" becomes \"5 boxes\".",
        "pieces with no missing number / pieces containing numbers x 100",
    ),
    "glossary_adherence": (
        "For each approved client term in the source, checks the translation used "
        "the agreed wording rather than a synonym. Only segments that actually "
        "contain a glossary term are counted.",
        "segments using the agreed term / segments containing a glossary term x 100",
    ),
    "source_leakage": (
        "If a line reads exactly the same as the English, it was never "
        "translated. Web addresses and short abbreviations are ignored, since "
        "those stay the same in every language.",
        "pieces whose wording changed / pieces with at least two real words x 100",
    ),
    "script_conformance": (
        "Confirms the text really is written in the target alphabet. A line that "
        "should be Korean but contains no Korean characters was never translated.",
        "pieces written in the target alphabet / pieces checked x 100",
    ),
    "language_id": (
        "An automatic language identifier reads each translation and confirms it is "
        "in the target language. Short segments and names confuse it, so a clean "
        "100% is uncommon.",
        "segments detected as the target language / segments checked x 100",
    ),
    "tofu": (
        "Every character is tested against the font that will print it. One the "
        "font does not have shows up as an empty box on the page, even though "
        "the text itself is correct.",
        "pieces with no unprintable character / pieces with text x 100",
    ),
    "overflow": (
        "How much of the text still fits inside the box it was given. Anything "
        "that does not fit either spills over or pushes onto an extra line.",
        "pieces whose text fits its box / total pieces x 100",
    ),
    # PDF structure
    "vector_preservation": (
        "Diagrams, table lines and charts are stored as drawing instructions, not "
        "pictures. A drop here means artwork was flattened into an image: it "
        "prints blurry and can no longer be edited.",
        "output drawings / source drawings x 100   (capped at 100%)",
    ),
    "masked_pixel_similarity": (
        "Both pages are compared as pictures with the words painted out, so only "
        "the background, lines and images are judged. On a page that is mostly "
        "text this stays near 100% and says little; it matters on pages full of "
        "diagrams.",
        "structural similarity (SSIM) of the two page images, after text is masked",
    ),
    "block_iou": (
        "Measures how far each block of text moved from where it sat in the "
        "original. This is normally the lowest layout figure, because translated "
        "text is a different length and re-wraps.",
        "overlap area / combined area of the two boxes, averaged over all blocks",
    ),
    # IDML structure
    "run_preservation": (
        "Counts the individual pieces of text in the file before and after. The "
        "count must match exactly; anything else means the file was rebuilt wrongly "
        "and formatting has been destroyed.",
        "output text pieces / source text pieces x 100",
    ),
    "style_preservation": (
        "Checks that font, size, boldness and paragraph settings on each piece of "
        "text are unchanged. Deliberately swapping the font for a non-Latin "
        "language is expected and is not counted as a loss.",
        "pieces with unchanged styling / pieces compared x 100",
    ),
    "math_run_preservation": (
        "Text set in a maths font must come back exactly as it went in. A failure "
        "means a formula was sent to the translation engine and came back as words.",
        "maths pieces identical to source / maths pieces x 100",
    ),
    "run_translation": (
        "How much of the text actually changed. Reported for information only — a "
        "very low figure warns that little was translated.",
        "pieces whose text changed / translatable pieces x 100",
    ),
    "asset_preservation": (
        "Everything in the package that is not text — page layouts, linked images, "
        "resources — must be unchanged. A failure means page geometry moved.",
        "unchanged files / total non-text files x 100",
    ),
    "overset_frames": (
        "After InDesign lays the document out it reports any box holding more text "
        "than fits. Text in an overset box simply does not appear on the printed "
        "page. Only InDesign can measure this.",
        "count of overflowing frames reported by InDesign   (0 required)",
    ),
}

QUALITY_EXPLANATIONS: dict[str, tuple[str, str]] = {
    "comet_kiwi": (
        "A model trained on thousands of human quality ratings predicts a score for "
        "each translated segment. It needs no correct answer to compare against, so "
        "it can run on live output.",
        "predicted quality score, 0-100%, averaged over segments",
    ),
    "mqm": (
        "A second model reads each translation, lists every error it can justify "
        "and labels each with a type and a severity.",
        "penalty = sum of (errors x how serious each one is); "
        "minor 1, major 5, critical 10\n"
        "score = 100% - (penalty per 100 words / 25)",
    ),
}


def glossary_entries(gates: dict, layout: dict, integrity: dict,
                     quality: dict | None = None, mqm: dict | None = None
                     ) -> list[dict]:
    """[{term, text, formula}, ...] for the metrics this report actually measured.

    Shared by the PDF renderer and the review UI, so the on-screen panel and the
    downloaded report can never describe the same number differently.
    """
    quality, mqm = quality or {}, mqm or {}
    labels = dict(LAYOUT_ROWS + INTEGRITY_ROWS)
    keys: list[str] = []

    def add(key: str) -> None:
        if key in EXPLANATIONS and key not in keys:
            keys.append(key)

    for check in gates.get("checks", []):
        if check.get("status") == "skip":
            continue
        gate = check.get("gate", "")
        add(gate[5:] if gate.startswith("idml_") else gate)
    for key, _ in LAYOUT_ROWS:
        if _measured(layout.get(key) or {}):
            add(key)
    for key, _ in INTEGRITY_ROWS:
        if _measured(integrity.get(key) or {}):
            add(key)

    entries = [{"term": GATE_LABELS.get(key) or labels.get(key, key),
                "text": EXPLANATIONS[key][0], "formula": EXPLANATIONS[key][1]}
               for key in keys]
    if _measured(quality.get("comet_kiwi") or {}):
        text, form = QUALITY_EXPLANATIONS["comet_kiwi"]
        entries.append({"term": "COMET-KIWI", "text": text, "formula": form})
    if mqm.get("mqm_score") is not None:
        text, form = QUALITY_EXPLANATIONS["mqm"]
        entries.append({"term": "MQM", "text": text, "formula": form})
    return entries


def _glossary(gates: dict, layout: dict, integrity: dict, quality: dict,
              mqm: dict, structural_only: bool = False) -> str:
    """Plain-language definitions for the metrics this report actually contains."""
    keys: list[str] = []

    def add(key: str) -> None:
        if key in EXPLANATIONS and key not in keys:
            keys.append(key)

    # Gate order first (the order the reader just saw), then the tables. Only
    # checks that actually ran are defined: a PDF report explaining four skipped
    # IDML metrics is clutter, and the gate table already gives the skip reason.
    for check in gates.get("checks", []):
        if check.get("status") == "skip":
            continue
        gate = check.get("gate", "")
        add(gate[5:] if gate.startswith("idml_") else gate)
    for key, _ in LAYOUT_ROWS:
        if _measured(layout.get(key) or {}):
            add(key)
    for key, _ in INTEGRITY_ROWS:
        if _measured(integrity.get(key) or {}):
            add(key)

    labels = dict(LAYOUT_ROWS + INTEGRITY_ROWS)

    def entry(term: str, pair: tuple[str, str]) -> str:
        text, formula_text = pair
        out = f"<p class='def'><b>{_esc(term)}</b> &#8212; {_esc(text)}</p>"
        for line in formula_text.split("\n"):
            out += f"<p class='defformula'>{_esc(line)}</p>"
        return out

    # Definition paragraphs rather than a table: fitz.Story will not split a
    # table across a page boundary and silently DROPS one that does not fit in
    # the space left, which is how the first version of this glossary rendered
    # as a heading with nothing under it. Paragraphs flow onto the next page.
    entries = [entry(GATE_LABELS.get(key) or labels.get(key, key), EXPLANATIONS[key])
               for key in keys]
    if _measured(quality.get("comet_kiwi") or {}):
        entries.append(entry("COMET-KIWI", QUALITY_EXPLANATIONS["comet_kiwi"]))
    if mqm.get("mqm_score") is not None:
        entries.append(entry("MQM", QUALITY_EXPLANATIONS["mqm"]))
    if not entries:
        return ""

    structure = ("Layout = average of the InDesign structural checks above"
                 if structural_only else
                 "Layout = 0.45 x Vector art + 0.30 x Pixel similarity"
                 " + 0.25 x Text blocks")

    return (
        "<h2>What each check means</h2>"
        "<p class='note'>Every figure is a percentage, and higher is always "
        "better. Each check looks only at the text it applies to, so the checks "
        "are not measuring the same thing as one another.</p>"
        "<p class='def'><b>How the overall figure is worked out</b> &#8212; wording "
        "counts for more than layout, because a wrong number matters more than a "
        "text box sitting slightly off. Only checks that actually ran are counted; "
        "if one could not run, the share it would have had is divided between the "
        "checks that did.</p>"
        f"<p class='defformula'>Overall accuracy = 0.60 x wording + 0.40 x layout</p>"
        "<p class='defformula'>Wording = average of the content checks below</p>"
        f"<p class='defformula'>{_esc(structure)}</p>"
        + "".join(entries)
    )


def build_html(result: dict) -> str:
    """The report as Story-compatible HTML."""
    gates = result.get("gates", {}) or {}
    integrity = result.get("integrity", {}) or {}
    layout = result.get("layout", {}) or {}
    score = result.get("layout_score", {}) or {}

    from babel.eval.scorecard import _stamp

    title = (result.get("original_filename") or
             os.path.basename(str(result.get("source") or "")) or
             result.get("job_id") or "document")

    # Spell the languages out. A reader who does not work on this pipeline has
    # no reason to know that "ko" means Korean, and a report they cannot read
    # unaided is not a report.
    try:
        target_name = languages.get(result.get("target_lang")).name
    except ValueError:
        target_name = str(result.get("target_lang") or "unknown")
    fmt = str(result.get("format", "")).lower()
    fmt_name = {"pdf": "PDF", "idml": "InDesign (IDML)",
                "indd": "InDesign (INDD)"}.get(fmt, fmt.upper() or "unknown")

    # No filename / format / count strip under the title: the opening sentence
    # already names the languages, and a row of counts is the first thing that
    # makes this look like a technical printout rather than a summary.
    parts = [f"<h1>Accuracy report</h1>"]

    overall = result.get("overall") or {}
    passed = bool(gates.get("passed"))

    # The verdict in sentences comes first. Everything below it is the evidence.
    parts.append(_summary(result, gates, target_name))

    if isinstance(overall.get("score"), (int, float)):
        # The figure alone. How it is composed is explained once, at the end.
        parts.append(f"<p class='overall'>Overall accuracy "
                     f"<b>{overall['score'] * 100:.1f}%</b></p>")

    parts.append(
        f"<p class='verdict-{'pass' if passed else 'fail'}'>"
        f"{'READY TO DELIVER' if passed else 'NOT READY TO DELIVER'}</p>"
    )
    # A gate reads one metric; that metric knows how many items it looked at.
    # Without it a gate skipped for want of candidates is indistinguishable from
    # one skipped because a tool was missing.
    from babel.eval.scorecard import GATES as _GATES

    def _sample_size(gate_key: str) -> int | None:
        path = next((g.path for g in _GATES if g.key == gate_key), ())
        node: object = result
        for part in path:
            node = node.get(part) if isinstance(node, dict) else None
        return node.get("applicable") if isinstance(node, dict) else None

    open_items = _open_items(gates, layout, integrity, target_name, fmt)

    parts.append("<table><tr><th>check</th><th>result</th><th>score</th>"
                 "<th>why</th></tr>")
    for check in gates.get("checks", []):
        gate = check.get("gate", "")
        status = check.get("status", "skip")
        value = check.get("value")
        total = _sample_size(gate)
        label_text = GATE_LABELS.get(gate, gate)

        if status == "skip":
            kind = _skip_kind(gate, check.get("reason"), fmt, total)
            reason = _skip_reason(gate, check.get("reason"), target_name, fmt, total)
            if kind == ACTION_REQUIRED:
                # Real missing coverage. It does not belong in a pass/fail table
                # where it reads as one more harmless skip; `_open_items` has
                # already collected it for the section below.
                continue
            verdict, shown, why = "NOT APPLICABLE", "—", reason
        else:
            verdict = {"pass": "PASSED", "fail": "FAILED"}[status]
            if isinstance(value, float) and value <= 1:
                shown = f"{(1.0 - value if gate in _INVERTED else value) * 100:.1f}%"
            else:
                shown = "—" if value is None else str(value)
            why = GATE_WHY.get(gate) or check.get("why", "")

        parts.append(
            f"<tr><td>{_esc(label_text)}</td>"
            f"<td class='{status}'>{verdict}</td>"
            f"<td class='num'>{shown}</td>"
            f"<td class='why'>{_esc(why)}</td></tr>"
        )
    # Unconfigured checks sit in the same table, in the same format, rather than
    # in a section of their own: a reader scanning one list should see every
    # check and its state without being sent somewhere else for the rest.
    for label_text, reason, action in open_items:
        parts.append(
            f"<tr><td>{_esc(label_text)}</td>"
            f"<td class='skip'>NOT SET UP</td>"
            f"<td class='num'>—</td>"
            f"<td class='why'>{_esc(reason)} <b>{_esc(action)}</b></td></tr>")
    parts.append("</table>")

    heading = ("Does the file still hold together?" if score.get("structural_only")
               else "Does the page still look right?")
    parts.append(f"<h2>{heading}</h2>")
    if score.get("score") is None:
        parts.append(f"<p class='note'>{_esc(score.get('reason', 'not measured'))}</p>")
    else:
        parts.append(f"<p>Layout score <b>{score['score'] * 100:.1f}%</b></p>")
        if score.get("missing"):
            # The score object names metrics by their internal keys; the reader
            # only ever sees the labels used in the tables.
            labels = dict(LAYOUT_ROWS + INTEGRITY_ROWS)
            missing = ", ".join(labels.get(k, k) for k in score["missing"])
            parts.append(f"<p class='note'>Not measured on this document: "
                         f"{_esc(missing)}. The remaining checks count for more "
                         f"to make up the score.</p>")
    if layout.get("available") is False:
        parts.append(f"<p class='note'>{_esc(layout.get('reason', ''))}</p>")
    else:
        parts.append(_metric_table(layout, LAYOUT_ROWS, target_name, fmt))

    parts.append(f"<h2>Does it still say the right thing in {_esc(target_name)}?</h2>")
    parts.append(_metric_table(integrity, INTEGRITY_ROWS, target_name, fmt))
    length = integrity.get("length_ratio") or {}
    if length.get("applicable"):
        median = length.get("median")
        trend = ("about the same length as the English"
                 if isinstance(median, (int, float)) and 0.9 <= median <= 1.1
                 else ("shorter than the English"
                       if isinstance(median, (int, float)) and median < 0.9
                       else "longer than the English"))
        over = length.get("over_line_budget") or 0
        risk = ("None of it runs long enough to risk not fitting its box"
                if not over else
                "A few lines run long enough to risk not fitting their box")
        parts.append(
            f"<p class='note'>Length: the typical {_esc(target_name)} line is "
            f"{_esc(trend)}. {risk}. Reported for information; it does not affect "
            f"the score.</p>"
        )

    quality = result.get("quality") or {}
    kiwi = quality.get("comet_kiwi") or {}
    mqm = result.get("mqm") or {}
    if _measured(kiwi) or mqm.get("mqm_score") is not None:
        parts.append("<h2>Translation quality</h2>")
        if _measured(kiwi):
            parts.append(f"<p>COMET-KIWI (reference-free) <b>{_pct(kiwi)}</b> "
                         f"over {_esc(kiwi.get('scored'))} segments</p>")
        if mqm.get("mqm_score") is not None:
            parts.append(
                f"<p>MQM <b>{mqm['mqm_score'] * 100:.1f}%</b> &#8212; "
                f"{_esc(mqm.get('penalty_per_100_words'))} penalty per 100 words, "
                f"{_esc(mqm.get('critical_errors'))} critical errors</p>")
    # No "quality was not run" notice: the optional tier is off by default, and a
    # standing apology for a metric nobody asked for is noise on a client report.

    parts.append(_glossary(gates, layout, integrity, quality, mqm,
                           structural_only=bool(score.get("structural_only"))))
    return "".join(parts)


def render_pdf(result: dict) -> bytes:
    """The scorecard as PDF bytes, paginated to fit.

    The embedded face is subset before returning. Without it a Korean report
    carries the whole of Malgun Gothic — a measured 13 MB for a one-page
    document, which is not something to hand a client.
    """
    face_css, archive = _font_css(result.get("target_lang"))
    story = fitz.Story(html=build_html(result), user_css=face_css + _CSS,
                       archive=archive)

    buffer = io.BytesIO()
    writer = fitz.DocumentWriter(buffer)
    media = fitz.paper_rect("a4")
    frame = media + (48, 48, -48, -56)
    more = 1
    while more:
        device = writer.begin_page(media)
        more, _ = story.place(frame)
        story.draw(device)
        writer.end_page()
    writer.close()

    doc = fitz.open(stream=buffer.getvalue(), filetype="pdf")
    try:
        try:
            doc.subset_fonts()
        except Exception:
            # Subsetting is an optimisation; a failure here must not cost the
            # user their report.
            pass
        return doc.tobytes(garbage=3, deflate=True)
    finally:
        doc.close()
