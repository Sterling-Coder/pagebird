"""Prove the Arabic edition is the English one selectively adapted.

Three passes, deliberately ordered cheapest first. The structural pass reads
IDML against IDML and needs no renderer: it is where a duplicated master item
or a scrambled stacking order is caught, and those are the failures that ruin a
document rather than merely misplace a box. The coverage pass reads the plan
and reports how much of the page nobody classified -- and, because a plan is
only trustworthy if it was built against the right text, whether the plan
itself looks stale (see `plan_coverage`). Only the visual pass renders a PDF,
and it renders one **to look at**, never to transform: PDF is never a source
of geometry or a target of a write in this module, only an artifact to
compare pixels against.

**Known limitation of the visual pass**: `idml.preview.render_idml` draws
text position and, where a linked image resolves on disk, the image itself --
but placed graphics whose links do not resolve locally (the common case for a
corpus checked out without its `Links/` folder) are drawn as a placeholder
box, not the artwork. So `compare_to_reference`'s agreement figure is, in
practice, a **text-block agreement figure**, not a full visual agreement --
it says nothing about whether a diagram or photo ended up mirrored to the
right side. Treat it as such until an InDesign Server export is available to
render placed graphics faithfully.
"""

from __future__ import annotations

from collections import Counter

from pagebirdy.idml import rtl


def _page_items(documents: dict) -> list:
    out = []
    for name in sorted(documents):
        if not name.startswith(("Spreads/", "MasterSpreads/")):
            continue
        for spread in documents[name].iter("Spread", "MasterSpread"):
            for el in spread.iter():
                if rtl._is_page_item(el):
                    out.append((name, spread.get("Self"), el.get("Self")))
    return out


def _masters(documents: dict) -> dict:
    out = {}
    for name in sorted(documents):
        if not name.startswith("Spreads/"):
            continue
        for page in documents[name].iter("{*}Page"):
            out[page.get("Self")] = page.get("AppliedMaster")
    return out


def check_invariants(source: dict, output: dict) -> list:
    """Structural guarantees, IDML against IDML. Empty list means clean.

    Every `Self` must appear exactly once in the output, document order within
    a spread must survive untouched, `AppliedMaster` per page must be
    unchanged, and no item may change page or spread, be duplicated, or be
    promoted into existence by the transform. These are the guarantees that
    protect the document -- a wrong mirror answer misplaces a box, but a
    violation of one of these corrupts the book.
    """
    violations = []

    src, out = _page_items(source), _page_items(output)
    src_ids = [i[2] for i in src]
    out_ids = [i[2] for i in out]

    dupes = [k for k, n in Counter(out_ids).items() if n > 1]
    for d in sorted(dupes):
        violations.append(f"duplicate object {d!r} in output")

    for missing in sorted(set(src_ids) - set(out_ids)):
        violations.append(f"object {missing!r} dropped from output")
    for added in sorted(set(out_ids) - set(src_ids)):
        violations.append(f"object {added!r} created by the transform")

    if src_ids != out_ids and set(src_ids) == set(out_ids) and not dupes:
        violations.append("stacking order changed: document order differs")

    src_master, out_master = _masters(source), _masters(output)
    for page, master in sorted(src_master.items()):
        if out_master.get(page) != master:
            violations.append(
                f"page {page!r} changed applied master: "
                f"{master!r} -> {out_master.get(page)!r}")

    # An item must not change which spread it sits on.
    src_home = {i[2]: i[1] for i in src}
    for name, spread, self_id in out:
        if self_id in src_home and src_home[self_id] != spread:
            violations.append(
                f"object {self_id!r} moved from spread "
                f"{src_home[self_id]!r} to {spread!r}")

    violations.extend(page_crossings(source, output))
    return violations


def _top_level_boxes(documents: dict) -> dict:
    """`(document, Self)` -> (bounds, page extents) for every spread child."""
    out = {}
    for name in sorted(documents):
        if not name.startswith(("Spreads/", "MasterSpreads/")):
            continue
        for spread in documents[name].iter("Spread", "MasterSpread"):
            extents = rtl.page_extents(spread)
            for el in spread:
                if not rtl._is_page_item(el):
                    continue
                box = rtl.item_bounds(el)
                if box is not None:
                    out[(name, el.get("Self"))] = (box, extents)
    return out


def page_crossings(source: dict, output: dict) -> list:
    """Items the transform pushed onto a page beside the one they belong to.

    An item that sits on one page in the source (:func:`rtl.pages_of`) must,
    in the output, reach no further into any other page of its spread than it
    already did in the source. Measured on top-level spread children, whose
    bounds enclose everything nested inside them, so a component is judged
    whole. What the source already did -- a frame dragged past the spine that
    nothing moved -- is not reported; only what the transform introduced is.
    A banner spanning the gutter has no single page to keep and is skipped.
    """
    before, after = _top_level_boxes(source), _top_level_boxes(output)
    out = []
    for key, (box, extents) in sorted(before.items()):
        if key not in after or len(extents) < 2:
            continue
        hit = rtl.pages_of(box, extents)
        if len(hit) != 1:
            continue
        o_box = after[key][0]
        for i, (px0, px1) in enumerate(extents):
            if i == hit[0]:
                continue
            was = max(0.0, min(box[2], px1) - max(box[0], px0))
            now = max(0.0, min(o_box[2], px1) - max(o_box[0], px0))
            if now > was + _CROSSING_TOL:
                out.append(
                    f"object {key[1]!r} ({key[0]}) crosses from page "
                    f"{hit[0]} onto page {i} by {now - was:.2f}pt")
    return out


# How far past its page an item may reach before it counts as crossing onto
# the next one: transform float noise on a frame flush to the spine, no more.
_CROSSING_TOL = 0.05


def _wrapped_items(documents: dict) -> dict:
    """`(document, Self)` -> (bounds, left, right, turned) for every spread item
    that pushes type away with a bounding-box or contour wrap.

    `turned` is the sign of the placed picture's own x scale, so a picture the
    mirror turned round can be told from one carried across as drawn. Groups
    are skipped: their inside is rearranged, not kept, so no one edge of the
    group is the edge of one picture.
    """
    out = {}

    def walk(node, parent, name):
        for el in node:
            if not rtl._is_page_item(el):
                continue
            t = rtl.compose(parent, rtl.parse_transform(el.get("ItemTransform")))
            walk(el, t, name)
            pref = el.find("./{*}TextWrapPreference")
            if rtl._is(el, "Group") or pref is None:
                continue
            if pref.get("TextWrapMode", "None") in ("None", "JumpObjectTextWrap"):
                continue
            off = pref.find("./{*}Properties/{*}TextWrapOffset")
            box = rtl.item_bounds(el, parent)
            if off is None or box is None:
                continue
            try:
                left, right = float(off.get("Left", 0)), float(off.get("Right", 0))
            except ValueError:
                continue
            placed = next((c for c in el
                           if rtl._localname(c) in ("Image", "PDF", "EPS", "WMF")), None)
            turned = (rtl.parse_transform(placed.get("ItemTransform"))[0] < 0
                      if placed is not None else False)
            out[(name, el.get("Self"))] = (box, left, right, turned)

    for name in sorted(documents):
        if not name.startswith("Spreads/"):
            continue
        for spread in documents[name].iter("Spread"):
            walk(spread, rtl.IDENTITY, name)
    return out


def wrap_clearance_losses(source: dict, output: dict) -> list:
    """Objects whose text wrap lets type closer, on some edge, than English did.

    Measured per edge of the object as it now sits. An object that stayed has
    the same edges as before. One that crossed the page presents its former
    right edge on the left and its left on the right, and each of them owes
    the type there the *gap* (positive offset) English kept on the side type
    used to meet -- while any *inset* (negative offset) belongs to the margin
    inside the picture, and so stays with the side of the picture it was on,
    unless the picture itself was turned round and took the margin with it.
    """
    before, after = _wrapped_items(source), _wrapped_items(output)
    out = []
    for key, (box, left, right, turned) in sorted(before.items()):
        if key not in after:
            continue
        o_box, o_left, o_right, o_turned = after[key]
        moved = abs((o_box[0] + o_box[2]) - (box[0] + box[2])) > 2 * _CROSSING_TOL
        if not moved:
            need_left, need_right = left, right
        elif o_turned != turned:
            need_left, need_right = right, left
        else:
            need_left = max(right, 0.0) + min(left, 0.0)
            need_right = max(left, 0.0) + min(right, 0.0)
        for side, have, need in (("left", o_left, need_left),
                                 ("right", o_right, need_right)):
            if have < need - _CROSSING_TOL:
                out.append(
                    f"object {key[1]!r} ({key[0]}) lets text {need - have:.2f}pt "
                    f"closer on its {side} edge than the source did")
    return out


def plan_coverage(plan) -> dict:
    """How much of the document nobody classified, and whether to trust it.

    `warnings` carries a loud flag for the one failure mode with no other
    guard: a plan built *before* translation. `rtl_features._script_mix`
    reads "latin" for untranslated English text, so a prose frame that has
    not been translated yet classifies as `text.ltr_only` (Latin, pinned)
    and never as `text.prose` (Arabic/mixed) -- every single time, on every
    page. At runtime the plan is meant to be built after translation
    (`pipeline.translate_idml` does this), but nothing enforces that
    ordering, and `cli.cmd_rtl_validate`'s own fallback -- building a plan
    fresh from the *source* IDML when no `--plan` is given -- reproduces
    exactly this trap. A target whose language is RTL, whose `text.prose`
    share is zero and whose `text.ltr_only` share is not, is reporting
    coverage for the wrong-language document.
    """
    from pagebirdy import languages

    by_rule = Counter(d.rule for d in plan.decisions)
    total = len(plan.decisions)
    prose = by_rule.get("text.prose", 0)
    ltr_only = by_rule.get("text.ltr_only", 0)

    warnings = []
    try:
        is_rtl = languages.get(plan.language).direction == "rtl"
    except ValueError:
        is_rtl = False
    if is_rtl and prose == 0 and ltr_only > 0:
        warnings.append(
            f"plan for {plan.language!r} looks built before translation: "
            f"0 text.prose decisions but {ltr_only} text.ltr_only -- "
            "untranslated (Latin-script) prose always reads as ltr_only, "
            "never as prose. Rebuild the plan after translation.")

    return {"total": total,
            "default_keep": by_rule.get("default.keep", 0),
            "moved": sum(1 for d in plan.decisions if d.moves),
            "flipped": sum(1 for d in plan.decisions if d.flips),
            "by_rule": dict(by_rule),
            "prose_share": (prose / total) if total else 0.0,
            "warnings": warnings}


def check_full_bleed_rasters(documents: dict, plan) -> list:
    """Corpus invariant: a full-bleed raster must be classified as bleed.

    An earlier defect had exactly this shape: `master.item` (an earlier,
    broader rule) shadowed `graphic.decorative_bleed` in the rule table, so
    the honeycomb header banner -- a full-bleed raster living on a master
    spread -- silently shipped un-mirrored. No test on one object would have
    caught the *class* of failure; this walks every full-bleed raster in the
    corpus and flags any whose decision came from a style or text rule
    rather than the three rules actually allowed to answer for bleed art:
    `graphic.decorative_bleed` (mirrors it), `default.keep` (a family that
    has turned mirroring off, `mirror_decorative_bleed=False`), and
    `default.mirror` (`default.keep`'s AR-gated counterpart -- the same
    "no rule specifically classified this" catch-all, just mirroring
    position instead of keeping it, for the one language/family combination
    with a calibrated reference corpus; see `idml.rtl_rules`).

    Reads `documents` the same way `rtl_plan.build_plan` did to produce
    `plan` -- i.e. the pre-transform package -- since that is what the plan's
    decisions were actually computed against.
    """
    from pagebirdy.idml import rtl_features

    # default.mirror is default.keep's AR-gated counterpart -- the same
    # "no rule specifically classified this" catch-all, just mirroring
    # instead of keeping position for the one language/family combination
    # with a calibrated reference corpus (see idml.rtl_rules). A full-bleed
    # object's bounds already span ~the full page width, so RTL_REPOSITION
    # reflecting its position about the page axis is a near-no-op visually
    # -- this is not the same risk graphic.decorative_bleed's own Group
    # exclusion guards against (turning the picture's content round, which
    # reflect_graphic genuinely cannot do for a group).
    allowed = {"graphic.decorative_bleed", "graphic.content_bleed",
               "default.keep", "default.mirror"}
    by_object = plan.by_object()
    violations = []
    for f in rtl_features.collect(documents):
        if f.content_kind != "raster" or not f.full_bleed:
            continue
        d = by_object.get(f.self_id)
        if d is None:
            continue
        if d.rule not in allowed:
            violations.append(
                f"full-bleed raster {f.self_id!r} (page {f.page_index}) "
                f"classified by {d.rule!r}, expected "
                "graphic.decorative_bleed, graphic.content_bleed, default.keep, "
                "or default.mirror")
    return violations


# Below this many square points two boxes are touching, not overlapping: frames
# set flush against each other come out of the transform arithmetic a hair
# apart or a hair inside.
_OVERLAP_MIN_AREA = 4.0


def hidden_layers(designmap) -> frozenset:
    """`Self` of every layer the document keeps hidden (`Visible="false"`)."""
    if designmap is None:
        return frozenset()
    return frozenset(el.get("Self") for el in designmap.iter()
                     if isinstance(el.tag, str)
                     and el.tag.rsplit("}", 1)[-1] == "Layer"
                     and el.get("Visible") == "false")


def _visible_top_level(documents: dict, hidden: frozenset) -> dict:
    from pagebirdy.idml import rtl_features

    return {f.self_id: f for f in rtl_features.collect(documents)
            if not f.anchored and f.parent_id is None and f.bounds is not None
            and f.page_index is not None and f.layer not in hidden}


def _overlapping_pairs(items: dict) -> set:
    ids = sorted(items)
    pairs = set()
    for i, a in enumerate(ids):
        fa = items[a]
        for b in ids[i + 1:]:
            fb = items[b]
            if fa.spread != fb.spread or fa.document != fb.document:
                continue
            w = min(fa.bounds[2], fb.bounds[2]) - max(fa.bounds[0], fb.bounds[0])
            h = min(fa.bounds[3], fb.bounds[3]) - max(fa.bounds[1], fb.bounds[1])
            if w > 0 and h > 0 and w * h > _OVERLAP_MIN_AREA:
                pairs.add((a, b))
    return pairs


def new_overlaps(source: dict, output: dict, hidden: frozenset = frozenset()) -> list:
    """Visible top-level page items that overlap in `output` but not `source`.

    What a reader sees as a broken page: a picture landed on a paragraph, a
    running head under a callout bar. Frames that already overlapped in the
    English source -- an icon set over its caption on purpose -- are not
    reported; only what the transform introduced is. Items on a hidden layer
    never print, so they are left out on both sides.
    """
    before = _overlapping_pairs(_visible_top_level(source, hidden))
    return sorted(_overlapping_pairs(_visible_top_level(output, hidden)) - before)


def compare_to_reference(output_pdf: str, reference_pdf: str) -> dict:
    """Per-page agreement between our Arabic PDF and the human one.

    Compared on normalised x-band, because that is the question the redesign
    turns on: did this block end up on the side the human designer put it. Text
    is not compared -- the reference is a different translation of the same
    source and would disagree word for word while agreeing perfectly on layout.

    Text-block agreement only -- see the module docstring: `preview.py`
    does not draw placed graphics whose links don't resolve locally, so a
    diagram or photo mirrored to the wrong side does not show up here.
    """
    import fitz

    ours, theirs = fitz.open(output_pdf), fitz.open(reference_pdf)
    pages, matched, mismatches = 0, 0, []
    total = 0

    for pno in range(min(ours.page_count, theirs.page_count)):
        pages += 1
        a, b = _bands(ours[pno]), _bands(theirs[pno])
        for band in a:
            total += 1
            if any(abs(band[0] - o[0]) < 0.06 and abs(band[1] - o[1]) < 0.06
                   for o in b):
                matched += 1
            else:
                mismatches.append({"page": pno + 1, "band": band})

    ours.close()
    theirs.close()
    return {"pages": pages, "blocks": total,
            "agreement": (matched / total) if total else 0.0,
            "mismatches": mismatches[:50]}


def _bands(page) -> list:
    """Normalised (x0, x1) for every text block and image on a page."""
    width = page.rect.width
    out = []
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        bb = block["bbox"]
        out.append((bb[0] / width, bb[2] / width))
    for im in page.get_image_info():
        bb = im["bbox"]
        out.append((bb[0] / width, bb[2] / width))
    return out


def score_book(source_documents: dict, output_documents: dict, plan,
               output_pdf: str | None = None,
               reference_pdf: str | None = None) -> dict:
    """One book's scorecard: invariants, coverage and, if given, agreement."""
    report = {"violations": check_invariants(source_documents,
                                             output_documents),
              "full_bleed_violations": check_full_bleed_rasters(
                  source_documents, plan),
              "coverage": plan_coverage(plan)}
    if output_pdf and reference_pdf:
        report["visual"] = compare_to_reference(output_pdf, reference_pdf)
    return report
