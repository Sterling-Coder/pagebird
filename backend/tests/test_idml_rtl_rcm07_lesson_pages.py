"""RCM07 L03's lesson pages, end to end, against what InDesign actually prints.

Four defects on the practice/develop spreads (pages 52-53), each traced in
InDesign 2026 to its cause rather than to a coordinate:

1. Problem numbers printed 16pt outside their frames, a few points from the
   page edge. `AnchorXoffset` is measured outward from the edge a side-aligned
   anchored object is aligned to; negating it on the Left->Right flip pushed
   every badge out of its hanging indent.
2. Sub-part labels (`a.`, `b.`, ...) printed small and light. The label is set
   by the paragraph style's nested `myriad bold`, and the target face written
   over the whole translated run beat it; a translation that trimmed a run's
   leading tab also collapsed the label's gap.
3. The Understand question bar ran onto the facing page. Its bleed off the
   outer trim crossed the spine when it mirrored; the target keeps the
   source's left-to-right binding.
4. The header's blue tab stayed at the spine while the title it heads mirrored
   away from it. A master shape bordering one page edge is part of the header
   band, not page furniture; the Family Letter's full-height strip is.

Every assertion is relative -- an inset against the same inset in English, an
edge against the page it belongs to -- and every object is found by what it is
(its style, its fill, its place on the page), not by its id.
"""

from __future__ import annotations

import glob
import os
import re

import pytest

from pagebirdy.idml import rtl, rtl_features, validate
from pagebirdy.idml.package import IdmlPackage
from pagebirdy.languages import get as get_language
from pagebirdy.translate.engine import Engine
from pagebirdy.translate.translator import Translator

BOOK = "RCM07_NA_SW_U01_L03"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOL = 0.5


def _source():
    hits = sorted(h for h in glob.glob(os.path.join(HERE, "uploads", f"{BOOK}-*.idml"))
                  if ".ar" not in os.path.basename(h))
    return hits[0] if hits else None


@pytest.fixture(scope="module")
def book():
    path = _source()
    if path is None:
        pytest.skip(f"{BOOK} not in uploads/")
    return path


class _Arabic(Engine):
    """Arabic prose, placeholders kept, run-edge whitespace trimmed the way an
    LLM trims it."""
    name = "fake-arabic"
    _TOKEN = re.compile(r"(⟦[^⟧]*⟧)")

    def translate(self, texts):
        out = []
        for t in texts:
            if not any(c.isalpha() for c in self._TOKEN.sub("", t)):
                out.append(t)
                continue
            parts = [p if self._TOKEN.fullmatch(p) or not any(c.isalpha() for c in p)
                     else re.sub(r"[A-Za-z][A-Za-z'’-]*", "نص", p)
                     for p in self._TOKEN.split(t)]
            out.append("".join(parts).strip(" \t"))
        return out


@pytest.fixture(scope="module")
def converted(book):
    """(source package, converted package), translated and turned RTL."""
    lang = get_language("ar")
    source = IdmlPackage(book)
    target = IdmlPackage(book)
    segs = target.segments()
    Translator(_Arabic(), None, None).run(segs)
    target.apply(segs, idml_font=lang.idml_font, font_styles=lang.idml_font_styles)
    target.document("Resources/Styles.xml")
    rtl.apply_rtl(target, document=BOOK, language="ar", idml_font=lang.idml_font,
                  font_styles=lang.idml_font_styles)
    source.document("Resources/Styles.xml")
    return source, target


# ---- shared lookups ---------------------------------------------------------

def _spread_items(pkg):
    """`Self` -> (element, spread, parent transform) for every page item."""
    return {k: (el, spread, parent)
            for k, (_, spread, el, parent) in validate._items(pkg.documents).items()}


def _box(entry):
    el, _, parent = entry
    return rtl.item_bounds(el, parent)


def _page_of(entry):
    el, spread, parent = entry
    extents = rtl.page_extents(spread)
    box = rtl.item_bounds(el, parent)
    page = rtl.dominant_page(box, extents) if box else None
    return (extents[page] if page is not None else None), spread


def _stories(pkg):
    return {s.get("Self"): s for n, t in pkg.documents.items()
            if n.startswith("Stories/") for s in t.iter("Story")}


# ---- 1. problem numbers keep their inset ------------------------------------

_SIDES = {"LeftAlign", "RightAlign"}


def _setting(pkg, frame):
    """The anchored-object setting in force on `frame`: its own, over its
    object style's."""
    styles = pkg.document("Resources/Styles.xml")
    wanted = frame.get("AppliedObjectStyle")
    merged = {}
    for os_el in styles.iter("ObjectStyle"):
        if os_el.get("Self") == wanted:
            found = os_el.find(".//AnchoredObjectSetting")
            if found is not None:
                merged.update(found.attrib)
    own = frame.find("AnchoredObjectSetting")
    if own is not None:
        merged.update(own.attrib)
    return merged


def _rendered_span(host_box, setting, width):
    """Where InDesign prints an edge-referenced, side-aligned anchored object.

    Calibrated in InDesign 2026: a positive offset moves a `LeftAlign` object
    left of the frame's left edge and a `RightAlign` object right of its right
    edge; the anchor point names which of the object's edges is put there.
    """
    offset = float(setting.get("AnchorXoffset", "0"))
    if setting["HorizontalAlignment"] == "LeftAlign":
        at = host_box[0] - offset
    else:
        at = host_box[2] + offset
    if setting["AnchorPoint"].endswith("LeftAnchor"):
        return at, at + width
    return at - width, at


def _markers(pkg):
    """(page extent, host frame box, rendered marker span) per problem number."""
    items = _spread_items(pkg)
    hosts = {el.get("ParentStory"): entry for entry in items.values()
             for el in [entry[0]] if el.get("ParentStory")}
    found = []
    for story_id, story in _stories(pkg).items():
        host = hosts.get(story_id)
        if host is None:
            continue
        for frame in story.iter("TextFrame"):
            if "STEM #" not in (frame.get("AppliedObjectStyle") or ""):
                continue
            setting = _setting(pkg, frame)
            if setting.get("HorizontalReferencePoint") != "TextFrame" or \
                    setting.get("HorizontalAlignment") not in _SIDES:
                continue
            xs = [float(p.get("Anchor").split()[0]) for p in frame.iter("PathPointType")]
            (page, _), box = _page_of(host), _box(host)
            found.append((frame.get("Self"), page, box,
                          _rendered_span(box, setting, max(xs) - min(xs))))
    return found


def test_problem_numbers_keep_their_inset_from_the_page_edge(converted):
    source, target = converted
    before = {k: v for k, *v in _markers(source)}
    after = {k: v for k, *v in _markers(target)}
    assert before and before.keys() == after.keys()
    for key, (page, box, span) in before.items():
        o_page, o_box, o_span = after[key]
        # English: inside the frame's leading edge, inset from the page's left.
        assert box[0] - TOL <= span[0] and span[1] <= box[2] + TOL, key
        # Arabic: inside the frame's new leading edge, the same inset from the
        # page's right.
        assert o_box[0] - TOL <= o_span[0] and o_span[1] <= o_box[2] + TOL, key
        assert abs((span[0] - page[0]) - (o_page[1] - o_span[1])) <= TOL, key


def test_same_level_problem_numbers_share_one_anchor(converted):
    _, target = converted
    by_page: dict = {}
    for _, page, _, span in _markers(target):
        by_page.setdefault(page, set()).add(round(span[1], 1))
    assert by_page
    for page, rights in by_page.items():
        assert len(rights) == 1, (page, rights)


# ---- 2. sub-part labels keep the source's typography ------------------------

_LABEL = re.compile(r"^[a-z]\.$")


def _labels(pkg):
    """(label run's inline font, FontStyle, PointSize, text after it) for every
    `STEM abc` paragraph that opens with a letter label."""
    out = []
    for story in _stories(pkg).values():
        for psr in story.iter("ParagraphStyleRange"):
            if not psr.get("AppliedParagraphStyle", "").endswith("STEM abc"):
                continue
            contents = [c for c in psr.iter("Content") if c.text]
            for i, c in enumerate(contents):
                text = c.text
                head = text.split("\t", 1)[0]
                if not _LABEL.match(head) or not validate._localname(c) == "Content":
                    continue
                csr = c.getparent()
                rest = text[len(head):] or (contents[i + 1].text if i + 1 < len(contents) else "")
                out.append((csr.findtext("Properties/AppliedFont"), csr.get("FontStyle"),
                            csr.get("PointSize"), head, rest))
    return out


def test_sub_part_labels_keep_the_source_face_weight_and_size(converted):
    source, target = converted
    before, after = _labels(source), _labels(target)
    assert len(after) == len(before) > 5
    # Every label is set the way English set it: nothing written over the
    # nested style, no size of its own -- the same for a. as for e.
    assert {(f, s, p) for f, s, p, _, _ in after} == {(f, s, p) for f, s, p, _, _ in before}
    assert len({(f, s, p) for f, s, p, _, _ in after}) == 1


def test_sub_part_labels_keep_the_gap_to_their_text(converted):
    _, target = converted
    for _, _, _, head, rest in _labels(target):
        assert rest.startswith("\t"), (head, rest[:10])


# ---- 3. the Understand bar stays on its page --------------------------------

def _question_bars(pkg):
    """Top-level groups on a facing-page spread holding a pale-yellow fill.

    A master spread's footer uses the same fill and is template furniture. The
    Family Letter's callout uses it too, on a single-page spread whose content
    mirrors about the area its side strip leaves (`rtl.content_axes`), not the
    page centre; it has no spine to cross."""
    bars = {}
    for key, entry in _spread_items(pkg).items():
        el, spread, _ = entry
        if spread.tag.endswith("MasterSpread") or len(rtl.page_extents(spread)) < 2:
            continue
        if not rtl._is(el, "Group") or el.getparent() is not spread:
            continue
        fills = [c for c in el if (c.get("FillColor") or "").endswith("Y=20 K=0")]
        if fills:
            bars[key] = entry
    return bars


def test_the_question_bar_mirrors_within_its_page_and_never_onto_the_facing_one(converted):
    source, target = converted
    s_bars, o_items = _question_bars(source), _spread_items(target)
    assert s_bars
    for key, entry in s_bars.items():
        (px0, px1), spread = _page_of(entry)
        extents = rtl.page_extents(spread)
        box, o_box = _box(entry), _box(o_items[key])
        facing = [e for e in extents if e != (px0, px1)]
        # What showed on the page in English, reflected about the page centre.
        on_page = (max(box[0], px0), min(box[2], px1))
        mirrored = (px0 + px1 - on_page[1], px0 + px1 - on_page[0])
        assert abs(o_box[1] - box[1]) <= TOL and abs(o_box[3] - box[3]) <= TOL
        spine_left = any(abs(e[1] - px0) <= TOL for e in facing)
        spine_right = any(abs(e[0] - px1) <= TOL for e in facing)
        if spine_left and px0 + px1 - box[2] < px0 - TOL:
            # Its outer-trim bleed would land over the spine: it stops there
            # instead -- moved, never trimmed, so it keeps its width.
            assert abs(o_box[0] - px0) <= TOL, key
            assert abs((o_box[2] - o_box[0]) - (box[2] - box[0])) <= TOL, key
        elif spine_right and px0 + px1 - box[0] > px1 + TOL:
            assert abs(o_box[2] - px1) <= TOL, key
            assert abs((o_box[2] - o_box[0]) - (box[2] - box[0])) <= TOL, key
        else:
            assert abs(max(o_box[0], px0) - mirrored[0]) <= TOL, key
            assert abs(min(o_box[2], px1) - mirrored[1]) <= TOL, key
        for fx0, fx1 in facing:
            assert min(o_box[2], fx1) - max(o_box[0], fx0) <= TOL, key


# ---- 4. the header tab goes with its header; the Family Letter strip stays --

def _master_edge_shapes(pkg):
    out = {}
    for key, entry in _spread_items(pkg).items():
        el, spread, _ = entry
        if not spread.tag.endswith("MasterSpread") or el.getparent() is not spread:
            continue
        if not rtl._is(el, "Rectangle") or not el.get("FillColor", "").startswith("Color/C=75"):
            continue
        box = _box(entry)
        (px0, px1), _ = _page_of(entry)
        pages = rtl.page_boxes(spread)
        height = pages[0][3] - pages[0][1]
        one_edge = (box[0] <= px0 + 1) != (box[2] >= px1 - 1)
        if one_edge and (box[3] - box[1]) < 0.5 * height:
            out[key] = entry
    return out


def test_the_header_tab_moves_to_the_side_its_title_now_starts_on(converted):
    source, target = converted
    tabs, o_items = _master_edge_shapes(source), _spread_items(target)
    assert tabs
    for key, entry in tabs.items():
        (px0, px1), _ = _page_of(entry)
        box, o_box = _box(entry), _box(o_items[key])
        on_left = box[0] <= px0 + 1
        assert (o_box[2] >= px1 - 1) if on_left else (o_box[0] <= px0 + 1), key
        assert abs((o_box[3] - o_box[1]) - (box[3] - box[1])) <= TOL, key
        assert abs(o_box[1] - box[1]) <= TOL, key


def test_every_page_header_label_ends_up_beside_its_tab(converted):
    """The running head on every page that uses a tabbed master sits on the
    same half of the page as that master's tab, in English and in Arabic."""
    source, target = converted
    for pkg in (source, target):
        items = _spread_items(pkg)
        tab_side = {}
        for key, entry in _master_edge_shapes(pkg).items():
            (px0, px1), spread = _page_of(entry)
            box = _box(entry)
            tab_side[(spread.get("Self"), round(px0))] = box[0] + box[2] < px0 + px1
        masters = {}
        for n, t in pkg.documents.items():
            if n.startswith("Spreads/"):
                for spread in t.iter("Spread"):
                    for page, (px0, px1) in zip([p for p in spread if rtl._is(p, "Page")],
                                                rtl.page_extents(spread)):
                        masters[(spread.get("Self"), round(px0))] = page.get("AppliedMaster")
        styles = rtl_features.paragraph_style_index(pkg.documents)
        checked = 0
        for entry in items.values():
            el, spread, _ = entry
            if not spread.tag.endswith("Spread") or spread.tag.endswith("MasterSpread"):
                continue
            if "_Master Page Styles:Navigation (Primary)" not in styles.get(el.get("ParentStory"), ()):
                continue
            (px0, px1), _ = _page_of(entry)
            master = masters.get((spread.get("Self"), round(px0)))
            side = [left for (m, mx0), left in tab_side.items()
                    if m == master and mx0 == round(px0)]
            if not side:
                continue
            box = _box(entry)
            assert (box[0] + box[2] < px0 + px1) == side[0]
            checked += 1
        assert checked


def test_the_family_letter_strip_badge_and_vertical_title_stay_together(converted):
    source, target = converted
    s_items, o_items = _spread_items(source), _spread_items(target)
    s_styles = rtl_features.paragraph_style_index(source.documents)
    vertical = [k for k, (el, _, _) in s_items.items()
                if "_Family Letter:FL lesson title" in s_styles.get(el.get("ParentStory"), ())]
    assert vertical
    for key in vertical:
        box, o_box = _box(s_items[key]), _box(o_items[key])
        assert all(abs(a - b) <= 1e-6 for a, b in zip(box, o_box)), key
    strips = [k for k, entry in s_items.items()
              if entry[1].tag.endswith("MasterSpread") and rtl._is(entry[0], "Rectangle")
              and _box(entry) is not None
              and (_box(entry)[3] - _box(entry)[1]) > 700]
    assert strips
    for key in strips:
        assert _box(s_items[key]) == _box(o_items[key]), key


# ---- 5. every page is mirrored on its own terms -----------------------------

def test_no_item_crosses_onto_a_facing_page_and_none_changes_page(book, converted):
    source, target = converted
    s_items, o_items = _spread_items(source), _spread_items(target)
    for key, entry in s_items.items():
        if key not in o_items or entry[0].getparent() is not entry[1]:
            continue
        box, o_box = _box(entry), _box(o_items[key])
        if box is None or o_box is None:
            continue
        extents = rtl.page_extents(entry[1])
        pages = rtl.pages_of(box, extents)
        if len(pages) != 1:
            continue
        px0, px1 = extents[pages[0]]
        assert validate._same_page(box, o_box, extents), key
        for ox0, ox1 in extents:
            if (ox0, ox1) == (px0, px1):
                continue
            if abs(ox1 - px0) <= TOL:      # a facing page on the left
                assert o_box[0] >= min(box[0], px0) - TOL, key
            if abs(ox0 - px1) <= TOL:      # a facing page on the right
                assert o_box[2] <= max(box[2], px1) + TOL, key


def test_a_page_s_content_axis_is_its_own(book):
    """The Family Letter's strip narrows only its own page's content area; the
    lesson spreads mirror each page about its own centre."""
    pkg = IdmlPackage(book)
    from pagebirdy.idml import rtl_plan
    plan = rtl_plan.build_plan(pkg.documents, document=BOOK, language="ar")
    by = plan.by_object()
    masters = {s.get("Self"): s for n, t in pkg.documents.items()
               if n.startswith("MasterSpreads/") for s in t.iter("MasterSpread")}
    narrowed = centred = 0
    for n, t in pkg.documents.items():
        if not n.startswith("Spreads/"):
            continue
        for spread in t.iter("Spread"):
            boxes = rtl.page_boxes(spread)
            axes = rtl.content_axes(boxes, rtl._fixed_furniture(spread, by, masters))
            for (x0, _, x1, _), axis in zip(boxes, axes):
                if abs(axis - (x0 + x1) / 2) <= 1e-6:
                    centred += 1
                else:
                    narrowed += 1
                    assert x0 < axis < (x0 + x1) / 2 or (x0 + x1) / 2 < axis < x1
    assert narrowed == 1 and centred > 1
