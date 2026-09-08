"""Layout-fidelity metrics for the IDML path — axis C.

An IDML is a ZIP of XML, not a rendered page, so none of the raster metrics in
`layout_pdf` apply to it. What matters instead is whether the write-back stage
preserved the document's structure and styling while changing only the text, and
whether the text still fits once InDesign reflows it.

  * `run_preservation` — `<Content>` node counts must match exactly. `apply()`
    only assigns `node.text`, so any change here means the package was rebuilt
    wrongly and styling has been destroyed.
  * `style_preservation` — CharacterStyleRange / ParagraphStyleRange attributes
    must be untouched. `AppliedFont` is reported separately, since overriding it
    is deliberate for non-Latin targets (`languages.Language.idml_font`).
  * `math_run_preservation` — runs in a math face must come back byte-identical.
    This is the IDML equivalent of the PDF path's `skipped_math`.
  * `asset_preservation` — every non-Stories ZIP entry (Spreads, Resources,
    links) must be byte-identical. A changed spread means geometry moved.
  * `overset_frames` — the real fit metric, and the one thing only InDesign can
    answer. See `overset_from_export` for how to source it.

Raster comparison for this path happens *after* export: run `layout_pdf.evaluate`
on (source PDF, InDesign-exported PDF) to get a number comparable with the PDF
path's.
"""

from __future__ import annotations

import json
import zipfile

from lxml import etree

from babel.idml.package import _font_of, _iter_content, _localname, is_math_font


def _stories(path: str) -> tuple[dict[str, etree._Element], dict[str, bytes]]:
    """Parsed Stories/*.xml plus the raw bytes of every other ZIP entry."""
    stories: dict[str, etree._Element] = {}
    others: dict[str, bytes] = {}
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            data = z.read(name)
            if name.startswith("Stories/") and name.endswith(".xml"):
                stories[name] = etree.fromstring(data)
            else:
                others[name] = data
    return stories, others


def _ancestor(el, localname: str):
    p = el.getparent()
    while p is not None:
        if _localname(p) == localname:
            return p
        p = p.getparent()
    return None


def _style_key(content) -> tuple[dict, dict]:
    """(CharacterStyleRange attrs, ParagraphStyleRange attrs) for one run.

    Deliberately excludes AppliedFont, which lives in a Properties child and is
    an intentional rewrite target — it is compared separately.
    """
    csr = _ancestor(content, "CharacterStyleRange")
    psr = _ancestor(content, "ParagraphStyleRange")
    return (dict(csr.attrib) if csr is not None else {},
            dict(psr.attrib) if psr is not None else {})


def _runs(stories: dict[str, etree._Element]) -> dict[str, list]:
    """Content nodes per story, in document order — the order `apply()` used."""
    return {name: list(_iter_content(tree)) for name, tree in stories.items()}


def evaluate(src_idml: str, out_idml: str, export_json: str | None = None) -> dict:
    """Every axis-C IDML metric, comparing source and translated packages."""
    src_stories, src_others = _stories(src_idml)
    out_stories, out_others = _stories(out_idml)
    src_runs, out_runs = _runs(src_stories), _runs(out_stories)

    src_total = sum(len(v) for v in src_runs.values())
    out_total = sum(len(v) for v in out_runs.values())

    # --- structural comparison, story by story ---------------------------
    style_changes, font_overrides, math_changed, translated = [], 0, [], 0
    comparable, story_mismatch = 0, []
    for name, s_nodes in src_runs.items():
        o_nodes = out_runs.get(name)
        if o_nodes is None or len(o_nodes) != len(s_nodes):
            story_mismatch.append({
                "story": name, "src_runs": len(s_nodes),
                "out_runs": len(o_nodes) if o_nodes is not None else None,
            })
            continue
        for i, (s, o) in enumerate(zip(s_nodes, o_nodes)):
            s_text, o_text = s.text or "", o.text or ""
            if not s_text.strip():
                continue
            comparable += 1
            s_font, o_font = _font_of(s), _font_of(o)
            if s_font != o_font:
                font_overrides += 1
            if _style_key(s) != _style_key(o):
                style_changes.append({"story": name, "index": i,
                                      "src": _style_key(s), "out": _style_key(o)})
            if is_math_font(s_font):
                if s_text != o_text:
                    math_changed.append({"story": name, "index": i,
                                         "src": s_text[:80], "out": o_text[:80]})
            elif s_text != o_text:
                translated += 1

    math_runs = sum(
        1 for name, nodes in src_runs.items() for n in nodes
        if (n.text or "").strip() and is_math_font(_font_of(n))
    )
    prose_runs = comparable - math_runs

    # --- non-Stories entries must be byte-identical ----------------------
    changed_assets = sorted(
        name for name in src_others
        if name in out_others and src_others[name] != out_others[name]
    )
    missing_assets = sorted(set(src_others) - set(out_others))

    def rate(good: int, total: int):
        return round(good / total, 4) if total else None

    result = {
        "src": src_idml,
        "out": out_idml,
        "run_preservation": {
            "rate": rate(min(src_total, out_total), src_total),
            "src_runs": src_total,
            "out_runs": out_total,
            "stories": len(src_stories),
            "story_mismatches": story_mismatch,
        },
        "style_preservation": {
            "rate": rate(comparable - len(style_changes), comparable),
            "applicable": comparable,
            "changed": len(style_changes),
            # Intentional when the target language declares an idml_font; a
            # non-zero count with a Latin target means something rewrote fonts.
            "font_overrides": font_overrides,
            "examples": style_changes[:20],
        },
        "math_run_preservation": {
            "rate": rate(math_runs - len(math_changed), math_runs),
            "applicable": math_runs,
            "changed": len(math_changed),
            "examples": math_changed[:20],
        },
        "run_translation": {
            "rate": rate(translated, prose_runs),
            "applicable": prose_runs,
            "translated": translated,
            "note": "prose runs whose text changed; an untranslated run is either "
                    "a TM identity hit or a skipped segment",
        },
        "asset_preservation": {
            "rate": rate(len(src_others) - len(changed_assets) - len(missing_assets),
                         len(src_others)),
            "applicable": len(src_others),
            "changed": changed_assets[:20],
            "missing": missing_assets[:20],
        },
        "overset_frames": overset_from_export(export_json),
    }
    return result


def overset_from_export(export_json: str | None) -> dict:
    """Overset-frame count, the IDML path's true overflow metric.

    Only InDesign can produce this, because only InDesign performs the reflow.
    `export_indesign.jsx` does not emit it yet; adding it is four lines:

        var overset = 0;
        for (var i = 0; i < doc.stories.length; i++)
            if (doc.stories[i].overflows) overset++;

    then write `overset` into the JSON the script already returns. Point this
    function at that file and the metric becomes ground truth instead of the
    PDF path's `LINE_BUDGET_RATIO` estimate.
    """
    if not export_json:
        return {"count": None, "available": False,
                "reason": "no export JSON supplied; requires an InDesign export "
                          "(see this function's docstring for the JSX change)"}
    try:
        with open(export_json, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return {"count": None, "available": False, "reason": f"{export_json}: {exc}"}

    for key in ("overset_frames", "overset", "overflows"):
        if key in data:
            count = data[key]
            return {"count": count, "available": True, "rate": 1.0 if not count else 0.0,
                    "source": f"{export_json}:{key}"}
    return {"count": None, "available": False,
            "reason": f"{export_json} has no overset_frames/overset/overflows key"}
