"""What each kind of object does in an Arabic edition, and why.

An ordered table, first match wins. Every rule is a pure predicate over an
`ObjectFeature` and returns an action, an orientation and a text treatment --
three answers, because they are three questions.

**Two kinds of object: page furniture and content.** Furniture -- master
items, the lesson badge, the vertical lesson title, the full-bleed decorative
art, whatever a page sets on its master's side strip -- stays where the page
template put it. Everything
else is content, and content mirrors within its page, for every RTL language.
Mirroring only some of it is what overlaps a page: a picture reflected onto a
paragraph that stayed where English left it. The rules after the furniture
block differ only in how much of an object's inside mirrors with it (a styled
equation crosses the page as one rigid unit) and in the text and orientation
they record.

The table is per book family. `curriculum-associates-rcm` is calibrated against
the human Arabic editions in `backend/Reference/`; another series registers its
own and overrides whichever rules disagree, without touching the engine.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from pagebirdy.idml import rtl_plan
from pagebirdy.idml import rtl_components
from pagebirdy.idml.rtl_components import DirectionMarkers

DEFAULT_FAMILY = "curriculum-associates-rcm"


@dataclass(frozen=True)
class PageContext:
    page_index: int | None
    page_width: float | None
    is_master: bool


@dataclass(frozen=True)
class Rule:
    rule_id: str
    predicate: object
    action: str
    orientation: str
    text: str
    reason: str


@dataclass(frozen=True)
class RuleTable:
    family: str
    rules: tuple
    markers: DirectionMarkers
    mirror_decorative_bleed: bool
    # Links whose graphic must never be turned round, whatever else applies.
    # Two things land here and they mean the same thing: a family's "this
    # decorative image is not RTL-adapted" list, and this run's `keep_upright`
    # links, whose pixels carry type the artwork stage already translated.
    never_flip_links: frozenset


def first_match(table: RuleTable, feature, page, component) -> Rule:
    for rule in table.rules:
        if rule.predicate(feature, page, component, table):
            return rule
    raise AssertionError("the table must end in a catch-all rule")


# ---- predicates ------------------------------------------------------------
#
# Each takes (feature, page, component, table). They are written as named
# functions rather than lambdas so a debug log can name the one that fired.

def _style_suffix(feature, suffix: str) -> bool:
    s_lower = suffix.lower()
    return any(s.lower().endswith(s_lower) for s in feature.paragraph_styles)


def _style_group(feature, group: str) -> bool:
    g_lower = group.lower()
    return any(s.lower().startswith(g_lower) for s in feature.paragraph_styles)


def _in_directional_component(component) -> bool:
    return component is not None and component.directional


def p_master_item(f, page, comp, table):
    return f.is_master_item


# The badge's own style names, as the corpus spells them (local name, compared
# case-insensitively). A named list rather than "the style mentions lesson":
# `Direction line (Lesson)` does too, on 758 frames that are ordinary content.
_BADGE_STYLES = frozenset({"fl lesson #", "fl lesson", "lesson", "lesson #"})
_UPRIGHT_TITLE_STYLE = "fl lesson title"


def p_lesson_badge(f, page, comp, table):
    # Matching the whole `_Master Page Styles:` group used to catch the running
    # heads filed beside the badge (`Navigation (Primary)`, `session`, `name`)
    # as well, and a running head held still while the page mirrored is
    # exactly what the mirrored content then lands on. The human Arabic
    # reference mirrors the running head with the page (page 48: the English
    # frame at 45-525 prints its Arabic ending at 567, its mirror image).
    for s in f.paragraph_styles:
        local = s.rsplit(":", 1)[-1].lower()
        if local in _BADGE_STYLES:
            return True
        if local == _UPRIGHT_TITLE_STYLE and not f.rotated:
            return True
    return False


def p_vertical_title(f, page, comp, table):
    return _style_suffix(f, ":FL lesson title") and f.rotated


def p_template_band(f, page, comp, table):
    # A document page's own copy of what its master sets on the side strip --
    # an overridden badge circle or Math Tools box, the folio, a callout bar
    # ending on the strip -- is not a master item, and fell through to
    # `default.mirror`: RCM07 L04 page 59 printed its badge circle in the
    # top-left corner, its lesson number still on the right. An anchored
    # object has no page position of its own to keep.
    return f.on_template_band and not f.anchored


# `graphic problem box` is not here: it names the paragraph that holds a word
# problem's inline box -- a backdrop, the box outline and the problem's prose --
# in every one of its 54 uses across the corpus, and nothing in that box has a
# left-to-right order of its own to keep. Filed as rigid, the box kept its text
# frame on the left while the problem's graph mirrored onto it.
_MATH_STYLES = ("vertical equation", "math console")
_MATH_OBJECT_STYLES = ("long division arrow 1", "long division arrow 2",
                       "math console", "problem box")


def p_math_equation(f, page, comp, table):
    # The pieces of one expression, found by `rtl_components` before anything
    # is classified: five text frames spelling "3 · 4 = 12", the seven rows
    # under it, the answer boxes and the fraction bars drawn among them; or an
    # explicit `<Group>` the designer drew the same equation with.
    #
    # Their arrangement is the mathematics rather than a reading order, so the
    # block crosses the page as one rigid unit and nothing inside it is
    # rearranged. `math.styled` says the same thing about a frame the corpus
    # *names* as an equation; this says it about one the corpus only shows,
    # which is most of them.
    #
    # A directional component still wins, exactly as it does for
    # `math.styled`: a family that has named a composition directional has
    # said something about it this rule cannot know.
    if comp is None or not comp.math:
        return False
    return not _in_directional_component(comp)


def p_math_styled(f, page, comp, table):
    if _in_directional_component(comp):
        return False
    if f.object_style in _MATH_OBJECT_STYLES:
        return True
    return any(s.split(":")[-1] in _MATH_STYLES for s in f.paragraph_styles)


def p_vector_art(f, page, comp, table):
    return f.content_kind == "vector" and not _in_directional_component(comp)


def p_translated_artwork(f, page, comp, table):
    # `keep_upright` links are folded into never_flip_links by the plan
    # builder, so this rule stays pure and the table holds all the run's data.
    return bool(f.link_uris & table.never_flip_links) and \
        f.content_kind == "raster" and not f.full_bleed


def p_decorative_bleed(f, page, comp, table):
    if not table.mirror_decorative_bleed:
        return False
    # A `<Group>` is a container, and `content_kind` credits it with whatever
    # its descendants hold -- so a group wrapping one photograph reads as
    # `raster` here. Ordering a group to turn round is an instruction nothing
    # can carry out: `reflect_graphic` reflects a frame's *own* outline and
    # composes a mirror onto its children, which needs the frame to own the
    # path geometry, and it declines a group outright. Classifying one anyway
    # printed `MIRROR_GRAPHIC` in the plan and the log for a banner that
    # shipped unturned. The picture inside is reached on its own account.
    if f.kind == "Group":
        return False
    if f.link_uris & table.never_flip_links:
        return False
    return (f.content_kind == "raster" and f.full_bleed
            and not _in_directional_component(comp))


def p_master_decorative_bleed(f, page, comp, table):
    return f.is_master_item and p_decorative_bleed(f, page, comp, table)


def p_direction_line(f, page, comp, table):
    return comp is not None and comp.directional and comp.kind == "cluster"


def p_directional_component(f, page, comp, table):
    return comp is not None and comp.directional


def p_nav_control(f, page, comp, table):
    return f.object_style in ("callout bubble", "carryover")


def p_table(f, page, comp, table):
    # A table is a frame whose story holds a <Table>. Its column order is a
    # data relationship, so the default is to change direction and nothing
    # else; a family that knows its columns are directional overrides this
    # rule to set TableDirection as well.
    return f.kind == "Table" or f.content_kind == "table"


def p_prose_text(f, page, comp, table):
    return f.content_kind == "text" and f.script_mix in ("arabic", "mixed")


def p_ltr_only_text(f, page, comp, table):
    return f.content_kind == "text"


# IDML's own interactive form-control kinds, plus the plain-Rectangle style
# this book family draws a fill-in-the-blank underline or answer box with.
# Measured against the full 10-book calibration corpus with the flipped
# default (see docs/superpowers/specs/2026-09-10-rtl-content-mirroring-
# default-design.md, "Form-field protection"): unprotected, `object_style ==
# "Form Fields"` alone accounts for 763 of ~1,224 objects the flipped default
# would newly reposition, sitting directly inside the bounds of the prose
# paragraph beside it -- an answer blank drawn inline in a sentence whose
# text (content_kind == "text") never moves. This rule keeps the blank with
# its sentence the same way `nav.control` keeps a callout with its context.
def p_form_field(f, page, comp, table):
    return rtl_components.is_form_field(f)


def p_always(f, page, comp, table):
    return True


# The page template, as opposed to the page's content: these stay where the
# template put it and join no content composition.
FURNITURE_RULES = frozenset({"graphic.decorative_bleed", "master.item",
                             "master.lesson_badge", "structure.vertical_title",
                             "structure.template_band"})


_RULES = (
    # Page furniture first: what the page template draws around the content --
    # the full-bleed decorative art, master items, the lesson badge and running
    # heads, the vertical lesson title -- stays exactly where the template put
    # it. Everything after this block is content, and content mirrors.
    #
    # Ahead of master.item on purpose: position and orientation are separate
    # questions, and master.item's KEEP_ORIENTATION answer is wrong for u355,
    # the honeycomb header banner -- a full-bleed raster that also lives on a
    # master spread. The human Arabic reference flips that banner and leaves it
    # in place. graphic.decorative_bleed's own predicate is narrow (raster +
    # full_bleed + not in a directional component).
    Rule("graphic.decorative_bleed", p_master_decorative_bleed,
         rtl_plan.MIRROR_GRAPHIC, rtl_plan.MIRROR_GRAPHIC, rtl_plan.KEEP_TEXT,
         "decorative composition is RTL-adapted"),
    Rule("master.item", p_master_item, rtl_plan.KEEP_POSITION,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.TEXT_RTL,
         "page-template structure preserved"),
    Rule("master.lesson_badge", p_lesson_badge, rtl_plan.KEEP_POSITION,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.TEXT_RTL,
         "lesson badge remains on right"),
    Rule("structure.vertical_title", p_vertical_title, rtl_plan.KEEP_POSITION,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.TEXT_RTL,
         "vertical lesson title remains on right"),
    Rule("structure.template_band", p_template_band, rtl_plan.KEEP_POSITION,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.TEXT_RTL,
         "set on the page template's side strip; position and size preserved"),

    # Content. Every rule below mirrors the object's place on the page; they
    # differ only in how much of the object's *inside* mirrors with it, and in
    # what the text and orientation fields record.
    #
    # An equation -- found by its own pieces (`math.equation`) or named by
    # its style (`math.styled`) -- a long-division bracket and a math console
    # are the rigid units: each crosses the page as drawn, its own
    # left-to-right order untouched. Every other composition mirrors its inside as well, because
    # only a page whose every piece is reflected about the same axis is
    # guaranteed not to overlap itself -- a group moved as a block while the
    # labels drawn over it are reflected one by one lands the labels on the
    # wrong boxes.
    # A decorative photograph on the page itself -- a strip down one side, a
    # corner picture -- is part of the page's arrangement: it crosses the page
    # and its picture turns round with it.
    Rule("graphic.content_bleed", p_decorative_bleed,
         rtl_plan.RTL_MIRROR, rtl_plan.MIRROR_GRAPHIC, rtl_plan.KEEP_TEXT,
         "decorative picture mirrors with the page and is turned round"),
    Rule("math.equation", p_math_equation, rtl_plan.RTL_REPOSITION,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.TEXT_RTL_LTR_PINNED,
         "an equation's pieces are a rigid block: it is repositioned for "
         "RTL as one unit and its own order is never rearranged"),
    Rule("math.styled", p_math_styled, rtl_plan.RTL_REPOSITION,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.TEXT_RTL,
         "mathematical structure crosses the page as one unit, its own "
         "order unchanged"),
    Rule("graphic.translated_artwork", p_translated_artwork,
         rtl_plan.RTL_MIRROR, rtl_plan.KEEP_ORIENTATION,
         rtl_plan.KEEP_TEXT, "translated type is burned into the pixels; "
         "the picture moves but is never turned round"),
    Rule("component.direction_line", p_direction_line,
         rtl_plan.RTL_MIRROR, rtl_plan.KEEP_ORIENTATION,
         rtl_plan.TEXT_RTL, "direction line mirrors with its sentence"),
    Rule("component.directional_pair", p_directional_component,
         rtl_plan.RTL_MIRROR, rtl_plan.KEEP_ORIENTATION,
         rtl_plan.TEXT_RTL, "directional content component mirrors"),
    Rule("math.vector_art", p_vector_art, rtl_plan.RTL_MIRROR,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.KEEP_TEXT,
         "placed artwork mirrors with the page; the picture itself is never "
         "turned round"),
    Rule("nav.control", p_nav_control, rtl_plan.RTL_MIRROR,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.TEXT_RTL,
         "directional navigation moves to the RTL side"),
    Rule("table.default", p_table, rtl_plan.RTL_MIRROR,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.TEXT_RTL,
         "table frame mirrors with the page; TableDirection orders its columns"),
    Rule("text.prose", p_prose_text, rtl_plan.RTL_MIRROR,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.TEXT_RTL,
         "text frame mirrors with the page and reads right to left"),
    Rule("text.ltr_only", p_ltr_only_text, rtl_plan.RTL_MIRROR,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.TEXT_RTL_LTR_PINNED,
         "frame mirrors with the page; the expression keeps its own order"),
    # An answer blank is drawn over the sentence it belongs to, so it goes
    # wherever that sentence goes.
    Rule("form.field", p_form_field, rtl_plan.RTL_MIRROR,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.KEEP_TEXT,
         "answer field mirrors with the text it sits in"),
    Rule("default.mirror", p_always, rtl_plan.RTL_MIRROR,
         rtl_plan.KEEP_ORIENTATION, rtl_plan.KEEP_TEXT,
         "page content mirrors"),
)

_MARKERS = DirectionMarkers(
    paragraph_styles=frozenset({
        "_Family Letter:FL caret", "_Family Letter:FL caret 1st",
        "Direction line (Lesson)", "Direction line (Practice)"}),
    object_styles=frozenset({"long division arrow 1", "long division arrow 2"}),
    component_ids=frozenset(),
)

_REGISTRY: dict = {}


def register(table: RuleTable) -> None:
    _REGISTRY[table.family] = table


def get_rules(family: str | None = None, language: str | None = None) -> RuleTable:
    """The table for `family`, or the default when it is not registered.

    `language` is accepted for callers that pass it, and no longer changes the
    table: a half-mirrored page -- some content across the page, the rest where
    English left it -- overlaps itself in any RTL language, not only Arabic.
    """
    actual_family = family or DEFAULT_FAMILY
    return _REGISTRY.get(actual_family, _REGISTRY[DEFAULT_FAMILY])


register(RuleTable(
    family=DEFAULT_FAMILY, rules=_RULES, markers=_MARKERS,
    mirror_decorative_bleed=True, never_flip_links=frozenset()))
