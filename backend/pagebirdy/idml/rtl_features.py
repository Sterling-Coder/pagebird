"""Everything the RTL classifier is allowed to know about a page item.

The classifier must not read XML. It reads these records, which is what makes
a decision reproducible from a saved plan and testable without a package on
disk. Collection is a pure read: nothing here mutates the tree, and the order
of the returned list is document order -- the book's own spine order for
items placed on a spread, then anchored objects found nested in a story's
text -- which is stacking order and must survive the whole pipeline untouched.

A feature is deliberately more than geometry. The corpus names its intent in
style names -- `_Family Letter:FL lesson title` is a vertical title and
`_Family Letter:FL caret` is a direction arrow -- and those names classify far
more reliably than a bounding box does. Not every item has geometry to give,
though: an object anchored inside a story's text is positioned by text flow,
not by a spread coordinate, and its record says so honestly (`bounds`,
`page_index`, `x_band` all None) rather than fabricating a page it isn't on.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import unquote

from pagebirdy import script
from pagebirdy.idml import rtl

# How much of itself an item may hang off its page before it counts as bleed.
# Well below a designer's deliberate placement and well above float noise.
_BLEED_EPS = 0.5


@dataclass(frozen=True)
class ObjectFeature:
    self_id: str
    kind: str
    spread: str
    document: str
    bounds: tuple | None
    transform: tuple
    rotated: bool
    sheared: bool
    page_index: int | None
    x_band: tuple | None
    full_bleed: bool
    layer: str | None
    object_style: str | None
    paragraph_styles: frozenset
    content_kind: str
    is_master_item: bool
    applied_master: str | None
    link_uris: frozenset
    script_mix: str
    anchored: bool
    z_index: int
    parent_id: str | None
    # An anchored object's extent in the space its own `ItemTransform` is
    # written in -- its enclosing group's, or the text's for the group itself.
    # Not a page position (`bounds` stays None for those), but it is a true
    # measure of how the pieces of one inline group sit relative to each
    # other, which is all a question about that group's arrangement needs.
    local_bounds: tuple | None = None
    # The item's story holds a mathematical expression and nothing else -- a
    # single operand, an operator, a relation, an answer blank, or a whole
    # equation set in one frame (`script.is_math_expression`). A designer
    # builds an equation out of several such frames, and their left-to-right
    # arrangement is the mathematics, not a reading order that turns round
    # with the page; `rtl_components` reads this to find those blocks.
    math_text: bool = False
    # True when that mathematics carries a relation or a binary arithmetic
    # operator (`script.contains_math_operator`), which is what distinguishes
    # a piece of an equation from a bare number that could be anything.
    math_operator: bool = False
    # On a document page, the item -- or the top-level item it sits inside --
    # reaches onto the side strip that page's master prints (`rtl.template_bands`):
    # a page's own copy of the badge, the Math Tools box, the folio, a callout
    # set against the strip. Template furniture that is not a master item.
    on_template_band: bool = False


def _name(value: str | None) -> str | None:
    """An IDML style reference as a readable name.

    IDML percent-escapes the colon that separates a style group from the style
    inside it, so `_Family Letter%3aFL caret` is what the file holds and
    `_Family Letter:FL caret` is what a rule wants to match.
    """
    if value is None:
        return None
    return unquote(value.split("/", 1)[-1] if "/" in value else value)


def paragraph_style_index(documents: dict) -> dict:
    """Story `Self` -> the set of paragraph style names it applies.

    Matches the unqualified tag `"Story"`, not the `"{*}Story"` wildcard:
    every `Stories/*.xml` is rooted in the packaging wrapper `<idPkg:Story>`,
    whose local name collides with the real, unnamespaced `<Story
    Self="...">` nested inside it. The wildcard matches both, so the wrapper
    -- whose `Self` is always None -- would collect the same styles a second
    time under `index[None]`. That is not a harmless duplicate: `collect()`
    looks up a page item's story with `el.get("ParentStory")`, which is also
    `None` for every item that has no story at all (any shape, image or
    group), so those items would silently inherit whatever story happened to
    populate `index[None]` last instead of falling back to the empty set.
    """
    index: dict = {}
    for doc, tree in documents.items():
        if not doc.startswith("Stories/"):
            continue
        for story in tree.iter("Story"):
            names = {_name(psr.get("AppliedParagraphStyle"))
                     for psr in story.iter("{*}ParagraphStyleRange")}
            index[story.get("Self")] = frozenset(n for n in names if n)
    return index


def story_text_index(documents: dict) -> dict:
    """Story `Self` -> its text, for the script test.

    Same `"Story"` (not `"{*}Story"`) reasoning as `paragraph_style_index`:
    matching the wildcard would fold every story's text into a spurious
    `index[None]` entry via the `<idPkg:Story>` wrapper, which a story-less
    page item's `texts.get(None, "")` lookup in `collect()` would then read
    instead of getting its honest empty string.
    """
    index: dict = {}
    for doc, tree in documents.items():
        if not doc.startswith("Stories/"):
            continue
        for story in tree.iter("Story"):
            index[story.get("Self")] = "".join(
                c.text or "" for c in story.iter("{*}Content"))
    return index


def table_story_index(documents: dict) -> dict:
    """Story `Self` -> whether a `<Table>` appears anywhere in its flow.

    Same unqualified `"Story"` reasoning as `paragraph_style_index` and
    `story_text_index`: matching the `"{*}Story"` wildcard would also match
    the namespaced `<idPkg:Story>` wrapper every `Stories/*.xml` is rooted
    in, folding this lookup into a spurious `index[None]` entry. `Table` is
    searched with the `{*}` wildcard because, unlike `Story`, it has no
    colliding wrapper to guard against and this index should not care
    whether some future IDML revision starts namespacing table elements.
    """
    index: dict = {}
    for doc, tree in documents.items():
        if not doc.startswith("Stories/"):
            continue
        for story in tree.iter("Story"):
            index[story.get("Self")] = story.find(".//{*}Table") is not None
    return index


def _math_operator(text: str, math_font: bool) -> bool:
    """Does this frame's text carry a mathematical operator?

    Visibly, or -- for text that is already nothing but an expression -- in a
    math font that prints one digit and means another. The
    `is_math_expression` guard is what keeps the font half of this honest;
    see `math_font_story_index`.
    """
    if script.contains_math_operator(text):
        return True
    return math_font and script.is_math_expression(text)


def math_font_story_index(documents: dict) -> dict:
    """Story `Self` -> whether any of its runs is set in a math font.

    These books write their operators as glyphs in a symbol face rather than
    as the characters they stand for: in `Mathematical Pi`, `"y 5 6x 1 1"` is
    `y = 6x + 1` and `"26"` is `-6`. `pagebirdy.protect.equations` documents the
    same substitution from the PDF side. So a text test alone cannot see the
    `=` in a frame that plainly has one, and `rtl_components` would refuse to
    read a row of such frames as an equation.

    On its own this is *not* evidence of an expression, and must never be
    used as if it were: a prose sentence carrying one `=` glyph resolves a
    math font too, and 1,398 of the 1,798 math-font stories across the
    calibration corpus are exactly that -- "Area is equal to the number of
    unit squares that fill a figure". It is only consulted for a frame whose
    text has *already* passed `script.is_math_expression`, where it answers
    the narrower question the glyph substitution destroyed the evidence for:
    is one of these tokens an operator?

    Resolved through the same `StyleIndex` the translation path uses, because
    these books declare the face on the paragraph style, not inline on the
    run. When `Resources/Styles.xml` was never handed to `collect` the index
    resolves nothing, every story answers False, and the visible-operator
    test stands alone -- a quieter rule, not a wrong one.
    """
    from pagebirdy.idml.package import is_math_font
    from pagebirdy.idml.styles import StyleIndex, ranges_of

    default = None
    prefs = documents.get("Resources/Preferences.xml")
    if prefs is not None:
        default = next((el for el in prefs.iter()
                        if rtl._localname(el) == "TextDefault"), None)
    styles = StyleIndex(documents.get("Resources/Styles.xml"), default)

    index: dict = {}
    for doc, tree in documents.items():
        if not doc.startswith("Stories/"):
            continue
        for story in tree.iter("Story"):
            index[story.get("Self")] = any(
                is_math_font(styles.effective(*ranges_of(content),
                                              "AppliedFont") or "")
                for content in story.iter("{*}Content"))
    return index


def _script_mix(text: str) -> str:
    if not text.strip():
        return "none"
    rtl_here = script.contains_rtl(text)
    if rtl_here and script.is_ltr_only(text):
        return "mixed"
    if rtl_here:
        return "arabic"
    if script.is_ltr_only(text):
        return "latin"
    return "mixed"


def _content_kind(el, has_table: bool = False) -> str:
    # A table's `<Row>`/`<Cell>` structure lives in the frame's own story,
    # nested under a `<CharacterStyleRange>` like any other flowed content --
    # it carries no `ItemTransform` (`_is_page_item` says no), so it never
    # shows up by walking `el` itself the way a placed raster or vector does.
    # `has_table` is looked up by the caller from the story index and named
    # ahead of the text/graphic checks below: a table frame also satisfies
    # `_carries_text`, and a rule table needs to tell "prose" from "table"
    # data apart rather than have the table quietly read as ordinary text.
    if has_table:
        return "table"
    placed = rtl.placed_content(el)
    text = rtl._carries_text(el)
    raster = bool(placed & set(rtl._RASTER))
    vector = bool(placed & set(rtl._VECTOR))
    if text and (raster or vector):
        return "mixed"
    if text:
        return "text"
    if raster and vector:
        return "mixed"
    if raster:
        return "raster"
    if vector:
        return "vector"
    if el.find("./{*}Properties/{*}PathGeometry") is not None:
        return "path"
    return "empty"


def _spine_order(documents: dict) -> list[str] | None:
    """The book's own reading order, from `designmap.xml`'s reference list.

    `designmap.xml` names every spread with an `<idPkg:Spread src="...">`
    entry, in spine order. Filenames don't sort into that order at all --
    `Spread_u107f.xml` sorts ahead of `Spread_u851.xml` alphabetically but
    opens after it in the book -- and `z_index` is meant to be compared across
    the whole document, so the *documents* have to be visited in the order the
    book is bound for that comparison to mean anything. Returns None when
    `designmap.xml` was never handed to `collect` (it isn't parsed by default;
    a caller opts in by adding it to `documents`), which is the caller's
    signal to fall back to something merely deterministic.
    """
    tree = documents.get("designmap.xml")
    if tree is None:
        return None
    # The `{*}` wildcard is deliberate here, unlike the Story/Spread lookups
    # elsewhere in this module: designmap.xml holds only the *namespaced*
    # <idPkg:Spread>/<idPkg:MasterSpread> reference elements, never an
    # unwrapped <Spread>, so there is no unnamespaced sibling to collide
    # with. The `src` filter is a second guard -- only a reference carries it.
    order = [el.get("src") for el in tree.iter("{*}MasterSpread", "{*}Spread")
              if el.get("src")]
    return order


def _document_order(documents: dict) -> list[str]:
    """`Spreads/` and `MasterSpreads/` documents, in the order to visit them.

    Prefers the book's spine order (`_spine_order`). Falls back to a plain
    sorted filename list -- alphabetical, not the book's order, but
    deterministic -- whenever `designmap.xml` is missing from `documents`, or
    its references don't account for every candidate document exactly (one
    side has an entry the other doesn't). A mismatch means the package handed
    in is partial or the two disagree, and guessing which candidates to keep
    and which to drop would silently lose or duplicate items; sorting
    everything is the safe fallback that still collects the whole set.

    Master spreads sort ahead of spreads either way -- `designmap.xml` lists
    them first in every sample book, and `"MasterSpreads/" < "Spreads/"`
    alphabetically agrees -- so nothing downstream needs to compare a master
    item's z_index against a spread item's for that ordering to hold.
    """
    candidates = {d for d in documents
                  if d.startswith(("Spreads/", "MasterSpreads/"))}
    spine = _spine_order(documents)
    if spine is not None:
        ordered = [d for d in spine if d in candidates]
        # Length as well as membership: a designmap that names the same
        # document twice satisfies the set comparison while yielding a repeat,
        # and a repeated document is collected twice -- duplicate features,
        # duplicate decisions, and a cluster member that `_move_component`
        # would shift by `dx` once per copy.
        if len(ordered) == len(candidates) and set(ordered) == candidates:
            return ordered
    return sorted(candidates)


def _story_owner_index(documents: dict) -> dict:
    """Story `Self` -> `(frame Self, spread Self, is_master)` of its frame.

    An object anchored inside a story's text has no spread of its own to
    measure against -- its `ItemTransform` places it in the *text*, not in
    spread space, and this module never builds spread coordinates for a
    `Stories/*.xml` document -- but it still visually belongs to whichever
    frame is flowing that text. An anchored record's `parent_id` and `spread`
    point at that frame instead of inventing geometry the anchor doesn't have.
    """
    index: dict = {}
    for doc, tree in documents.items():
        if not doc.startswith(("Spreads/", "MasterSpreads/")):
            continue
        is_master = doc.startswith("MasterSpreads/")
        for spread in tree.iter("Spread", "MasterSpread"):
            spread_self = spread.get("Self")
            for el in spread.iter():
                story = el.get("ParentStory")
                if story and story not in index:
                    index[story] = (el.get("Self"), spread_self, is_master)
    return index


def _collect_anchored(documents: dict, owners: dict, counter,
                      texts: dict | None = None,
                      math_fonts: dict | None = None) -> list:
    """Page items reachable only by walking down from a `<Story>` -- anchors.

    An anchored object carries an `ItemTransform` exactly like a page item
    sitting directly on a spread, which is why `_is_page_item` alone can't
    tell the two apart; what marks it is being nested inside a
    `<CharacterStyleRange>` rather than a `<Spread>`. Its transform describes
    where it sits *in the text*, not in spread space, so `bounds`,
    `page_index` and `x_band` are left None rather than measured in the wrong
    coordinate system -- a caller that needs this object's page has to resolve
    it through the frame flowing the story (`owners`), not through geometry
    this module doesn't have.

    `paragraph_styles` and `script_mix` come from the single
    `<ParagraphStyleRange>` the anchor is actually nested in, not from the
    whole story: an anchor sits in exactly one paragraph, and the story-wide
    index a text frame uses is the *union* of every paragraph style in the
    story, whatever that story otherwise contains. A rule table downstream
    treats certain style names as evidence an object is directional and must
    be structurally recomposed for RTL; handing every anchor its host
    story's whole style set would flag a decorative graphic as directional
    merely for sharing a story with an unrelated direction line elsewhere in
    the text, over-transforming an object that should stay exactly where it
    is. When no enclosing `<ParagraphStyleRange>` can be found (the anchor
    sits directly under the `<Story>`, outside any paragraph -- unusual but
    not impossible), the honest answer is empty, not the story's set:
    `frozenset()` and `"none"`.
    """
    texts = texts or {}
    math_fonts = math_fonts or {}
    out: list = []
    for doc in sorted(d for d in documents if d.startswith("Stories/")):
        tree = documents[doc]
        # Unqualified "Story", not "{*}Story": every Stories/*.xml is rooted
        # in the packaging wrapper <idPkg:Story>, whose local name collides
        # with the real <Story> nested inside it. Matching the wildcard would
        # walk from both roots and collect each anchor twice.
        for story in tree.iter("Story"):
            story_self = story.get("Self")
            frame_id, spread_self, is_master = owners.get(
                story_self, (None, None, False))

            def walk(node, parent_id, para):
                for el in node:
                    local = rtl._localname(el)
                    # Track the nearest enclosing paragraph as we descend, so
                    # an anchor several wrappers deep (CharacterStyleRange,
                    # a Group's own children, ...) still resolves to the one
                    # paragraph it's actually inside, not one further out.
                    next_para = el if local == "ParagraphStyleRange" else para
                    if not rtl._is_page_item(el):
                        walk(el, parent_id, next_para)
                        continue
                    t = rtl.parse_transform(el.get("ItemTransform"))
                    style_name = (_name(para.get("AppliedParagraphStyle"))
                                  if para is not None else None)
                    para_styles = (frozenset({style_name}) if style_name
                                   else frozenset())
                    para_text = ("".join(c.text or "" for c in
                                          para.iter("{*}Content"))
                                 if para is not None else "")
                    out.append(ObjectFeature(
                        self_id=el.get("Self"),
                        kind=rtl._localname(el),
                        spread=spread_self,
                        document=doc,
                        bounds=None,
                        transform=t,
                        rotated=(t[1] != 0.0 or t[2] != 0.0),
                        sheared=(t[1] != 0.0 and t[2] != 0.0
                                 and t[0] * t[1] + t[2] * t[3] != 0.0),
                        page_index=None,
                        x_band=None,
                        full_bleed=False,
                        layer=el.get("ItemLayer"),
                        object_style=_name(el.get("AppliedObjectStyle")),
                        paragraph_styles=para_styles,
                        content_kind=_content_kind(el),
                        is_master_item=is_master,
                        applied_master=None,
                        link_uris=frozenset(rtl._link_uris(el)),
                        script_mix=_script_mix(para_text),
                        math_text=script.is_math_expression(
                            texts.get(el.get("ParentStory"), "")),
                        math_operator=_math_operator(
                            texts.get(el.get("ParentStory"), ""),
                            math_fonts.get(el.get("ParentStory"), False)),
                        anchored=True,
                        z_index=next(counter),
                        parent_id=parent_id if parent_id is not None else frame_id,
                        local_bounds=rtl.item_bounds(el),
                    ))
                    walk(el, el.get("Self"), next_para)

            walk(story, None, None)
    return out


# How far past a strip item's edge a frame set inside it may run.
_INSIDE_TOL = 1.0


def _set_inside_band_items(features: list) -> list:
    """`features` of one spread, with what is set inside a strip item on it too.

    The Math Tools label is its own frame drawn inside the Math Tools box, and
    need not reach the strip itself (RCM08 U02 L05's stops 2pt short); left to
    mirror on its own it printed at the far page edge, out of its box. Wholly
    inside, not merely touching: a body frame whose corner runs under the badge
    circle is content. Anything nested in such a frame goes with it.
    """
    from dataclasses import replace

    holders = [f.bounds for f in features
               if f.on_template_band and f.parent_id is None and f.bounds]
    marked: set = set()
    result = []
    for f in features:
        inside = f.parent_id in marked or (
            f.parent_id is None and not f.on_template_band and f.bounds
            and any(h[0] - _INSIDE_TOL <= f.bounds[0]
                    and f.bounds[2] <= h[2] + _INSIDE_TOL
                    and h[1] - _INSIDE_TOL <= f.bounds[1]
                    and f.bounds[3] <= h[3] + _INSIDE_TOL for h in holders))
        if inside:
            marked.add(f.self_id)
            f = replace(f, on_template_band=True)
        result.append(f)
    return result


def collect(documents: dict) -> list:
    """Every page item in every spread, master spread and story, in document order.

    "Document order" is the book's spine order for `Spreads/`/`MasterSpreads/`
    (see `_document_order`), then anchored objects nested in `Stories/*.xml`.
    `z_index` is drawn from one counter shared across that whole walk -- a
    later stage sorts every component in the book by it, so per-spread
    counters that each restarted at 0 would collide and invert cross-spread
    stacking order.
    """
    pstyles = paragraph_style_index(documents)
    texts = story_text_index(documents)
    tables = table_story_index(documents)
    math_fonts = math_font_story_index(documents)
    owners = _story_owner_index(documents)
    out: list = []
    counter = iter(range(10_000_000))
    master_spreads = {s.get("Self"): s for d, t in documents.items()
                      if d.startswith("MasterSpreads/")
                      for s in t.iter("MasterSpread")}

    for doc in _document_order(documents):
        is_master = doc.startswith("MasterSpreads/")
        tree = documents[doc]
        for spread in tree.iter("Spread", "MasterSpread"):
            extents = rtl.page_extents(spread)
            masters = [pg.get("AppliedMaster")
                       for pg in spread.iter("{*}Page")]
            pages = rtl.page_boxes(spread)
            bands = ([[] for _ in pages] if is_master
                     else rtl.template_bands(spread, master_spreads))

            def walk(node, parent, parent_id, in_band=False):
                for el in node:
                    if not rtl._is_page_item(el):
                        continue
                    t = rtl.parse_transform(el.get("ItemTransform"))
                    box = rtl.item_bounds(el, parent)
                    page = rtl.dominant_page(box, extents) if box else None
                    band = full_bleed = None
                    if box is not None and page is not None:
                        px0, px1 = extents[page]
                        width = px1 - px0
                        band = ((box[0] - px0) / width, (box[2] - px0) / width)
                        full_bleed = (box[0] < px0 - _BLEED_EPS
                                      or box[2] > px1 + _BLEED_EPS)
                    story = el.get("ParentStory")
                    kind = _content_kind(el, tables.get(story, False))
                    # Decided on the top-level item and inherited: a callout's
                    # arrow is on the template because its bar is. A full-bleed
                    # photograph running under the strip is the page's
                    # decorative art, which the bleed rules turn round.
                    band_here = in_band or (
                        parent_id is None and page is not None
                        and page < len(bands)
                        and not (full_bleed and kind == "raster")
                        and rtl.on_template_band(box, pages[page], bands[page]))
                    out.append(ObjectFeature(
                        self_id=el.get("Self"),
                        kind=rtl._localname(el),
                        spread=spread.get("Self"),
                        document=doc,
                        bounds=box,
                        transform=t,
                        rotated=(t[1] != 0.0 or t[2] != 0.0),
                        sheared=(t[1] != 0.0 and t[2] != 0.0
                                 and t[0] * t[1] + t[2] * t[3] != 0.0),
                        page_index=page,
                        x_band=band,
                        full_bleed=bool(full_bleed),
                        layer=el.get("ItemLayer"),
                        object_style=_name(el.get("AppliedObjectStyle")),
                        paragraph_styles=pstyles.get(story, frozenset()),
                        content_kind=kind,
                        is_master_item=is_master,
                        applied_master=(masters[page]
                                        if page is not None and page < len(masters)
                                        else None),
                        link_uris=frozenset(rtl._link_uris(el)),
                        script_mix=_script_mix(texts.get(story, "")),
                        math_text=script.is_math_expression(
                            texts.get(story, "")),
                        math_operator=_math_operator(
                            texts.get(story, ""), math_fonts.get(story, False)),
                        anchored=False,
                        z_index=next(counter),
                        parent_id=parent_id,
                        on_template_band=band_here,
                    ))
                    walk(el, rtl.compose(parent, t), el.get("Self"), band_here)

            start = len(out)
            walk(spread, rtl.IDENTITY, None)
            if any(bands):
                out[start:] = _set_inside_band_items(out[start:])

    out.extend(_collect_anchored(documents, owners, counter, texts,
                                 math_fonts))
    return out
