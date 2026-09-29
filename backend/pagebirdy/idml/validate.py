"""Compare a translated IDML against its source and report what changed.

An RTL conversion is a hundred small edits spread across two hundred XML
entries, and the only honest way to say it worked is to open both packages and
check -- object by object -- that everything which had to move moved, and
everything which had to survive survived.

The checks are grouped the way a reviewer reads a page:

* **structure** -- entry list, page count, page sizes, spread composition. None
  of it may change. A conversion that quietly dropped a spread or resized a
  page is not a conversion.
* **geometry** -- every page item matched to its source counterpart by `Self`,
  then asked three questions: did it move, did it keep its width, height,
  rotation and vertical position, and is it still on the page it started on.
* **text** -- how much of the document is in the target script, and whether any
  run of it is set in a face that cannot draw it.
* **direction** -- binding, story direction, paragraph direction, table
  direction, composer.
* **assets** -- every `<Link>` still points at the file it pointed at.
* **styles** -- every paragraph, character, object and table style still exists.

Every check reports counts and named examples rather than a bare pass/fail, so
a failure says which object on which spread and by how much.

The report is deliberately computed from the two files alone. It never consults
the pipeline that produced them, so it is equally usable on output from an
older build, from InDesign itself, or from a hand conversion.
"""

from __future__ import annotations

import zipfile

from lxml import etree

from pagebirdy import script
from pagebirdy.idml import rtl
from pagebirdy.idml.styles import StyleIndex

_EXAMPLES = 5  # named offenders per check; enough to debug, short enough to read
_TOL = 0.01    # points: well under a printer's dot, well over float noise

# Same hardened parser as idml/package.py: no XXE, huge_tree for embedded
# base64 image <Contents> past libxml2's 10 MB text-node cap.
_XML_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)

# Faces known to carry the RTL scripts, lowercased for substring comparison. A
# run of Arabic set in anything else is a missing-glyph box waiting to happen,
# and this is the check that catches it before the document reaches InDesign.
_RTL_CAPABLE = ("arabic", "hebrew", "naskh", "nastaliq", "kufi", "dubai",
                "geeza", "farisi", "traditional arabic", "simplified arabic",
                "tahoma", "arial unicode", "times new roman", "segoe ui",
                "david", "narkisim", "frankruehl", "miriam", "noto sans")


def _load(path: str) -> dict:
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def _trees(entries: dict, prefix) -> dict:
    out = {}
    for name, data in entries.items():
        if name.endswith(".xml") and name.startswith(prefix):
            try:
                out[name] = etree.fromstring(data, parser=_XML_PARSER)
            except etree.XMLSyntaxError:
                continue
    return out


def _localname(el) -> str:
    return etree.QName(el).localname if isinstance(el.tag, str) else ""


def _pages(trees: dict) -> list:
    """`(Self, GeometricBounds)` for every page, in document order."""
    pages = []
    for name in sorted(trees):
        for page in trees[name].iter("Page"):
            pages.append((page.get("Self") or "", page.get("GeometricBounds") or ""))
    return pages


def _items(trees: dict) -> dict:
    """Every page item anywhere in the spreads, keyed by `Self`.

    Nested items are included: a frame inside a group is as much a page item as
    a frame on the spread, and a check that skipped it would miss every
    composition the group mirror rearranges.

    Each item is stored with the transform of everything *above* it, so its
    bounds can be measured in spread coordinates. A group child's own
    `ItemTransform` is written in its group's space -- one of the sample books
    has a group whose children sit at x = -704 in their own space and on the
    page in the spread's -- so a check that read those numbers as spread
    coordinates would report objects on pages that do not exist.
    """
    found = {}

    def walk(el, parent, name, spread):
        for child in el:
            if not rtl._is_page_item(child):
                continue
            if child.get("Self"):
                found[child.get("Self")] = (name, spread, child, parent)
            walk(child, rtl.compose(parent,
                                    rtl.parse_transform(child.get("ItemTransform"))),
                 name, spread)

    for name, tree in trees.items():
        for spread in tree.iter("Spread", "MasterSpread"):
            # The walk starts *inside* the spread: a `<Spread>` carries an
            # `ItemTransform` of its own and so answers to `_is_page_item` like
            # anything else, but measuring it means measuring the union of its
            # children, which narrows the moment they rearrange -- and every
            # mirrored spread would report itself as a resized object.
            walk(spread, rtl.parse_transform(spread.get("ItemTransform")),
                 name, spread)
    return found


def _runs(trees: dict):
    """Every `<CharacterStyleRange>` in the stories, with the text it owns.

    "Owns" is the whole point. Character style ranges nest: an editorial
    `<Note>` is a whole styled story parked inside the range it annotates, and
    an anchored frame's text sits inside the range it is anchored in. Reading
    every descendant `<Content>` hands the inner run's text to the outer range
    as well, which has no font of its own -- and the check then reports
    correctly typeset Arabic as Arabic in a Latin face.

    So each `<Content>` is attributed to its *nearest* enclosing range, and a
    range with nothing of its own is not a run at all.
    """
    for name in sorted(trees):
        for csr in trees[name].iter("CharacterStyleRange"):
            text = "".join(rtl._run_text(c) for c in csr.iter()
                           if _localname(c) == "Content" and _nearest_range(c) is csr)
            if text.strip():
                yield name, csr, text


def _nearest_range(content):
    el = content.getparent()
    while el is not None:
        if _localname(el) == "CharacterStyleRange":
            return el
        el = el.getparent()
    return None


def _paragraph_of(csr):
    el = csr.getparent()
    while el is not None and _localname(el) != "ParagraphStyleRange":
        el = el.getparent()
    return el


def _rtl_capable(face: str) -> bool:
    low = (face or "").lower()
    return any(key in low for key in _RTL_CAPABLE)


class _ReadOnlyPackage:
    """Just enough of `IdmlPackage` for `StyleIndex.from_package` to index."""

    def __init__(self, entries: dict):
        self._entries = entries

    def read_document(self, name: str):
        data = self._entries.get(name)
        return etree.fromstring(data, parser=_XML_PARSER) if data is not None else None


class _Pair:
    """One group of entries parsed from each package, held side by side.

    Every check needs the same trees, and re-parsing them per check doubled the
    peak: on a real textbook two packages' worth of that is enough to exhaust
    the interpreter. A group is dropped (`del pair.source`) the moment the last
    check that wants it has run.
    """

    __slots__ = ("source", "output")

    def __init__(self, source: dict, output: dict):
        self.source = source
        self.output = output


def _fmt(box):
    return [round(v, 2) for v in box]


def _same_page(s_box, o_box, extents) -> bool:
    """True when an item is still on the page it started on.

    Only asked of an item that belonged to exactly one page to begin with. A
    banner that genuinely spans the gutter has no page to leave: mirroring it
    about the spread centre is what keeps it covering what it covered, and its
    *centre* crosses the gutter every time it does so. Judging that by centre
    reported the one correct case in a real book as a bug.

    Pasteboard furniture is skipped for the same reason: it is on no page
    before or after, and the mirror never touches it.

    What is compared is the page each box *mostly* covers, not the set of
    pages it touches. A bleed drawn larger than its page laps a few points
    over the gutter once it is mirrored -- it is on the same page it always
    was, and nudging it back off the gutter is what pushes a sidebar band over
    the content beside it. An item that changes the page it mostly covers has
    really moved: that is problem 4 of page 12 printing on page 13.
    """
    before = rtl.pages_of(s_box, extents)
    if len(before) != 1:
        return True
    return rtl.dominant_page(s_box, extents) == rtl.dominant_page(o_box, extents)


# ---- the checks -------------------------------------------------------------


def _check_structure(src: dict, out: dict, spreads, report: dict) -> None:
    report["entries_source"] = len(src)
    report["entries_output"] = len(out)
    report["entries_missing"] = sorted(set(src) - set(out))[:_EXAMPLES]
    report["entries_added"] = sorted(set(out) - set(src))[:_EXAMPLES]

    s_pages, o_pages = _pages(spreads.source), _pages(spreads.output)
    report["pages_source"] = len(s_pages)
    report["pages_output"] = len(o_pages)
    report["page_bounds_changed"] = [
        {"page": a[0], "source": a[1], "output": b[1]}
        for a, b in zip(s_pages, o_pages) if a[1] != b[1]
    ][:_EXAMPLES]
    report["page_order_changed"] = [a[0] for a, b in zip(s_pages, o_pages)
                                    if a[0] != b[0]][:_EXAMPLES]


def _is_horizontal_flip(source, output) -> bool:
    """True when `output`'s matrix is `source`'s with a horizontal mirror on it.

    Composing ``x -> 2*axis - x`` onto ``a b c d`` negates `a` and `c` and
    leaves `b` and `d` alone. Nothing else about the item changes: a reflection
    is an isometry, so its width, height and rotation come through untouched.
    """
    return (abs(output[0] + source[0]) <= _TOL
            and abs(output[1] - source[1]) <= _TOL
            and abs(output[2] + source[2]) <= _TOL
            and abs(output[3] - source[3]) <= _TOL)


def _is_a_picture(el) -> bool:
    """True for a placed raster, or the frame holding one and nothing else.

    These are the only items `rtl.reflect_graphic` turns round, and the only
    ones whose matrix a correct mirror is allowed to change.
    """
    return _localname(el) == "Image" or rtl.placed_content(el) == {"Image"}


def _check_geometry(spreads, report: dict) -> None:
    """Match items by `Self` and ask what the mirror promised of each."""
    s_items, o_items = _items(spreads.source), _items(spreads.output)

    moved = unmoved = flipped = 0
    resized, reshaped, drifted, left_page = [], [], [], []

    for key, (name, _s_spread, s_el, s_parent) in s_items.items():
        entry = o_items.get(key)
        if entry is None:
            continue
        _, o_spread, o_el, o_parent = entry

        s_t = rtl.parse_transform(s_el.get("ItemTransform"))
        o_t = rtl.parse_transform(o_el.get("ItemTransform"))
        if s_t[:4] != o_t[:4]:
            # `a b c d` carry width, height, rotation, scale and shear
            # together. Any change to them is a content flip or a distortion --
            # forbidden everywhere except on a placed photograph, which the
            # mirror turns round on purpose because the human-translated
            # references do; see `rtl.reflect_graphic`.
            if _is_a_picture(s_el) and _is_horizontal_flip(s_t, o_t):
                flipped += 1
            else:
                reshaped.append(key)

        s_box = rtl.item_bounds(s_el, s_parent)
        o_box = rtl.item_bounds(o_el, o_parent)
        if s_box is None or o_box is None:
            continue

        if abs((s_box[2] - s_box[0]) - (o_box[2] - o_box[0])) > _TOL or \
                abs((s_box[3] - s_box[1]) - (o_box[3] - o_box[1])) > _TOL:
            resized.append({"item": key, "source": _fmt(s_box),
                            "output": _fmt(o_box)})
        if abs(s_box[1] - o_box[1]) > _TOL:
            drifted.append({"item": key, "source_top": round(s_box[1], 2),
                            "output_top": round(o_box[1], 2)})
        if abs(s_box[0] - o_box[0]) > _TOL:
            moved += 1
        else:
            unmoved += 1

        # An item must still sit on the page it started on. Crossing the gutter
        # is how a mirror about the wrong axis shows up: the content of page 17
        # printing on page 16.
        extents = rtl.page_extents(o_spread)
        if extents and not _same_page(s_box, o_box, extents):
            left_page.append({"item": key, "spread": name})

    report["items_source"] = len(s_items)
    report["items_output"] = len(o_items)
    report["items_missing"] = sorted(set(s_items) - set(o_items))[:_EXAMPLES]
    report["items_moved"] = moved
    report["items_unmoved"] = unmoved
    report["items_flipped"] = flipped
    report["items_resized"] = resized[:_EXAMPLES]
    report["items_reshaped"] = reshaped[:_EXAMPLES]
    report["items_drifted_vertically"] = drifted[:_EXAMPLES]
    report["items_changed_page"] = left_page[:_EXAMPLES]


def _check_text(stories, index: StyleIndex, report: dict) -> None:
    report["runs_source"] = sum(1 for _ in _runs(stories.source))
    total = in_target = pinned = 0
    unrenderable = []
    for name, csr, text in _runs(stories.output):
        total += 1
        if csr.get("CharacterDirection") == "LeftToRightDirection":
            pinned += 1
        if not script.contains_rtl(text):
            continue
        in_target += 1
        face = index.effective(_paragraph_of(csr), csr, "AppliedFont") or ""
        if not _rtl_capable(face):
            unrenderable.append({"story": name,
                                 "font": face or "(nothing declared)",
                                 "text": text.strip()[:40]})

    report["runs_output"] = total
    report["runs_in_target_script"] = in_target
    report["runs_pinned_ltr"] = pinned
    report["runs_in_unrenderable_font"] = unrenderable[:_EXAMPLES]
    report["runs_in_unrenderable_font_count"] = len(unrenderable)


def _binding(entries: dict) -> str | None:
    for tree in _trees(entries, ("Resources/Preferences.xml",)).values():
        for el in tree.iter("DocumentPreference"):
            return el.get("PageBinding")
    return None


def _check_direction(src: dict, out: dict, stories, report: dict) -> None:
    o_all = dict(stories.output, **_trees(out, ("Resources/",)))
    counts = {"paragraphs_rtl": 0, "paragraphs_ltr": 0, "stories_rtl": 0,
              "stories_ltr": 0, "tables_rtl": 0, "tables_ltr": 0,
              "paragraphs_world_ready": 0, "paragraphs_latin_composer": 0}
    for tree in o_all.values():
        for el in tree.iter():
            tag = _localname(el)
            if tag in ("ParagraphStyleRange", "ParagraphStyle"):
                counts["paragraphs_rtl" if el.get("ParagraphDirection") ==
                       "RightToLeftDirection" else "paragraphs_ltr"] += 1
                counts["paragraphs_world_ready"
                       if "Optyca" in (el.get("Composer") or "")
                       else "paragraphs_latin_composer"] += 1
            elif tag == "StoryPreference":
                counts["stories_rtl" if el.get("StoryDirection") ==
                       "RightToLeftDirection" else "stories_ltr"] += 1
            elif tag in ("Table", "TableStyle"):
                counts["tables_rtl" if el.get("TableDirection") ==
                       "RightToLeftDirection" else "tables_ltr"] += 1
    report.update(counts)

    report["page_binding"] = _binding(out)
    report["page_binding_source"] = _binding(src)


def _check_assets(spreads, report: dict) -> None:
    def links(trees):
        found = []
        for tree in trees.values():
            for el in tree.iter():
                if _localname(el) == "Link":
                    found.append(el.get("LinkResourceURI") or "")
        return sorted(found)

    s_links, o_links = links(spreads.source), links(spreads.output)
    report["links_source"] = len(s_links)
    report["links_output"] = len(o_links)
    # Artwork translation deliberately repoints a link at a translated copy, so
    # a changed URI is reported rather than failed; a *lost* link is the fault.
    report["links_lost"] = sorted(set(s_links) - set(o_links))[:_EXAMPLES]
    report["links_repointed"] = len(set(o_links) - set(s_links))


def _check_styles(src: dict, out: dict, report: dict) -> None:
    def names(entries):
        found = set()
        for tree in _trees(entries, ("Resources/",)).values():
            for el in tree.iter():
                if _localname(el) in ("ParagraphStyle", "CharacterStyle",
                                      "ObjectStyle", "TableStyle", "CellStyle"):
                    found.add(el.get("Self") or "")
        return found

    s_styles, o_styles = names(src), names(out)
    report["styles_source"] = len(s_styles)
    report["styles_output"] = len(o_styles)
    report["styles_lost"] = sorted(s_styles - o_styles)[:_EXAMPLES]


def _check_fonts(src: dict, out: dict, stories, index: StyleIndex,
                 report: dict) -> None:
    def families(entries):
        tree = _trees(entries, ("Resources/Fonts.xml",)).get("Resources/Fonts.xml")
        if tree is None:
            return {}
        return {fam.get("Name"): [f.get("FontStyleName") for f in fam.iter("Font")]
                for fam in tree.iter("FontFamily")}

    s_fam, o_fam = families(src), families(out)
    report["font_families_source"] = len(s_fam)
    report["font_families_output"] = len(o_fam)
    report["font_families_lost"] = sorted(set(s_fam) - set(o_fam))[:_EXAMPLES]
    report["font_families_added"] = {k: o_fam[k]
                                     for k in sorted(set(o_fam) - set(s_fam))}

    # A family named by a run but never declared is the missing-font dialogue,
    # and for an Arabic run it is a page of empty boxes. Only the family is
    # checked: a style the family does not list is InDesign's own substitution
    # to make, and every source in hand names weights ("900", "3") no family
    # declares, so failing on those would report the source as broken.
    declared = set(o_fam)
    undeclared = []
    for name, csr, _text in _runs(stories.output):
        face = index.effective(_paragraph_of(csr), csr, "AppliedFont") or ""
        if face and face not in declared:
            undeclared.append({"story": name, "font": face})
    report["runs_naming_an_undeclared_face"] = undeclared[:_EXAMPLES]
    report["runs_naming_an_undeclared_face_count"] = len(undeclared)


# ---- the entry point --------------------------------------------------------


def validate_rtl_idml(source: str, output: str,
                      target_lang: str | None = None) -> dict:
    """Compare `output` against `source` and return every check's findings.

    `target_lang` decides only what the checks *expect*: an RTL target is
    expected to have moved its binding and turned its paragraphs round, an LTR
    one is expected to have left both alone. Everything else -- structure,
    geometry, assets, styles -- is checked identically either way, because
    "nothing that had to survive was lost" is the same requirement for both.
    """
    from pagebirdy import languages

    lang = languages.get(target_lang) if target_lang else None
    expect_rtl = bool(lang and lang.direction == "rtl")

    src, out = _load(source), _load(output)
    report: dict = {"source": source, "output": output,
                    "target_lang": lang.code if lang else None,
                    "expect_rtl": expect_rtl}

    # Each group of entries is parsed once and shared. Re-parsing the spreads
    # for every check doubled the peak, and on a real textbook two packages'
    # worth of that is enough to exhaust the interpreter mid-suite.
    spreads = _Pair(_trees(src, ("Spreads/", "MasterSpreads/")),
                    _trees(out, ("Spreads/", "MasterSpreads/")))
    _check_structure(src, out, spreads, report)
    _check_geometry(spreads, report)
    _check_assets(spreads, report)
    del spreads          # the spreads are the bulk of a package; free them here

    stories = _Pair(_trees(src, ("Stories/",)), _trees(out, ("Stories/",)))
    index = StyleIndex.from_package(_ReadOnlyPackage(out))
    _check_text(stories, index, report)
    _check_direction(src, out, stories, report)
    _check_styles(src, out, report)
    _check_fonts(src, out, stories, index, report)
    del stories, index, src, out
    report["problems"] = _problems(report, expect_rtl)
    report["ok"] = not report["problems"]
    return report


def _problems(r: dict, expect_rtl: bool) -> list:
    """The findings that mean the conversion is wrong, in plain words.

    Everything here is a *broken guarantee*, never a difference: an object that
    moved is the point of the exercise, an object that changed size is a bug.
    """
    out = []
    if r["entries_missing"]:
        out.append(f"entries lost from the package: {r['entries_missing']}")
    if r["pages_source"] != r["pages_output"]:
        out.append(f"page count changed {r['pages_source']} -> {r['pages_output']}")
    if r["page_bounds_changed"]:
        out.append(f"page size changed: {r['page_bounds_changed']}")
    if r["page_order_changed"]:
        out.append(f"pages reordered inside their spreads: {r['page_order_changed']}")
    if r["page_binding"] != r["page_binding_source"]:
        # PageBinding decides which side of a spread each page renders on --
        # flipping it (regardless of target direction) is a layout change
        # this pipeline never makes; text direction is carried by
        # StoryDirection/ParagraphDirection instead, checked below.
        out.append(f"page binding changed {r['page_binding_source']!r} -> "
                   f"{r['page_binding']!r}")
    if r["items_missing"]:
        out.append(f"page items lost: {r['items_missing']}")
    if r["items_resized"]:
        out.append(f"page items resized: {r['items_resized']}")
    if r["items_reshaped"]:
        out.append("page items whose matrix was altered — content flipped or "
                   f"distorted: {r['items_reshaped']}")
    if r["items_drifted_vertically"]:
        out.append(f"page items moved vertically: {r['items_drifted_vertically']}")
    if r["items_changed_page"]:
        out.append(f"page items that changed page: {r['items_changed_page']}")
    if r["links_lost"]:
        out.append(f"linked assets lost: {r['links_lost']}")
    if r["styles_lost"]:
        out.append(f"styles lost: {r['styles_lost']}")
    if r["font_families_lost"]:
        out.append(f"font families lost: {r['font_families_lost']}")
    if r["runs_in_unrenderable_font"]:
        out.append(
            f"{r['runs_in_unrenderable_font_count']} run(s) of target-script text "
            f"set in a face that cannot draw it: {r['runs_in_unrenderable_font']}")
    if r["runs_naming_an_undeclared_face"]:
        out.append(
            f"{r['runs_naming_an_undeclared_face_count']} run(s) name a font family "
            f"the package never declares: {r['runs_naming_an_undeclared_face']}")
    if expect_rtl:
        if r["paragraphs_ltr"]:
            out.append(f"{r['paragraphs_ltr']} paragraph(s) still read left to right")
        if r["stories_ltr"]:
            out.append(f"{r['stories_ltr']} story/stories still read left to right")
        if r["tables_ltr"]:
            out.append(f"{r['tables_ltr']} table(s) still order columns left to right")
        if r["paragraphs_latin_composer"]:
            out.append(f"{r['paragraphs_latin_composer']} paragraph(s) still use the "
                       "Latin composer, which does not shape Arabic")
    elif r["target_lang"]:
        # Only when a language was actually named. With none given the caller
        # has not said which conversion this was meant to be, so asserting that
        # nothing moved would fail every RTL job checked without a `--lang`.
        if r["items_moved"]:
            out.append(f"{r['items_moved']} page item(s) moved in an LTR job")
    return out


def format_report(r: dict) -> str:
    """The report as a reviewer's before/after table."""
    lines = [
        f"source : {r['source']}",
        f"output : {r['output']}",
        f"target : {r['target_lang'] or '(not given)'}   "
        f"expect RTL: {r['expect_rtl']}",
        "",
        "structure            source   output",
        f"  package entries    {r['entries_source']:>6}   {r['entries_output']:>6}",
        f"  pages              {r['pages_source']:>6}   {r['pages_output']:>6}",
        f"  page items         {r['items_source']:>6}   {r['items_output']:>6}",
        f"  text runs          {r['runs_source']:>6}   {r['runs_output']:>6}",
        f"  styles             {r['styles_source']:>6}   {r['styles_output']:>6}",
        f"  linked assets      {r['links_source']:>6}   {r['links_output']:>6}",
        f"  font families      {r['font_families_source']:>6}   "
        f"{r['font_families_output']:>6}",
        "",
        "geometry",
        f"  items mirrored             {r['items_moved']}",
        f"  items left in place        {r['items_unmoved']}"
        "   (centred on its page, or parked on the pasteboard)",
        f"  pictures turned round      {r['items_flipped']}",
        f"  items resized              {len(r['items_resized'])}",
        f"  items reshaped             {len(r['items_reshaped'])}",
        f"  items moved vertically     {len(r['items_drifted_vertically'])}",
        f"  items that changed page    {len(r['items_changed_page'])}",
        "",
        "text and direction",
        f"  page binding                    {r['page_binding_source']} -> "
        f"{r['page_binding']}",
        f"  runs in target script           {r['runs_in_target_script']}",
        f"  runs pinned left-to-right       {r['runs_pinned_ltr']}",
        f"  runs in an unusable face        "
        f"{r['runs_in_unrenderable_font_count']}",
        f"  runs naming an undeclared face  "
        f"{r['runs_naming_an_undeclared_face_count']}",
        f"  paragraphs RTL / LTR            {r['paragraphs_rtl']} / "
        f"{r['paragraphs_ltr']}",
        f"  stories RTL / LTR               {r['stories_rtl']} / {r['stories_ltr']}",
        f"  tables RTL / LTR                {r['tables_rtl']} / {r['tables_ltr']}",
        f"  world-ready / Latin composer    {r['paragraphs_world_ready']} / "
        f"{r['paragraphs_latin_composer']}",
        "",
        f"font families pagebirdy added    {r['font_families_added'] or '(none)'}",
        f"links repointed to artwork   {r['links_repointed']}",
        "",
    ]
    if r["problems"]:
        lines.append(f"PROBLEMS ({len(r['problems'])}):")
        lines.extend(f"  - {p}" for p in r["problems"])
    else:
        lines.append("PROBLEMS: none - every guarantee held.")
    return "\n".join(lines)
