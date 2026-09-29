"""The transformation plan: one decision per object or component.

Everything downstream reads this and nothing else. The executor applies it,
the debug log prints it, the tests assert on it and the validation harness
scores against it, so a decision can be argued about as data instead of being
reverse-engineered from a rendered page.

**Position, orientation and text are three separate fields**, because they are
three separate questions.

**`text` is advisory; position and orientation are authoritative.** The
executor reads `action` and `new_orientation` and does exactly what they say.
It does not read `text`. Text direction is applied by `set_text_direction` and
`preserve_ltr_content`, which work from the content of each run -- a run
holding nothing but an equation is pinned left-to-right because of what it
contains, not because a rule predicted it would be. Those passes predate this
module, are well covered, and reach the same answer per run that the rule
reaches per object, so rewiring them through the plan would move a decision
that is already correct into a place where it could go wrong.

What `text` is for, then, is the record: it says what treatment the rule
expected, which is what makes a disagreement between the rule's expectation and
the content-driven outcome visible at all. `rtl_validate` reports that
disagreement rather than asserting on it. Do not read `text` in the executor
without also moving the application of text direction into the plan; a field
that is half-honoured is worse than one that is honestly advisory. A decorative banner keeps its position and turns its
picture round; a navigation control moves and keeps its picture as drawn. A
model with one axis cannot say either.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace

# Position semantics.
KEEP_POSITION = "KEEP_POSITION"
TEXT_ONLY_RTL = "TEXT_ONLY_RTL"
RTL_REPOSITION = "RTL_REPOSITION"
MIRROR_GRAPHIC = "MIRROR_GRAPHIC"
RTL_RESTRUCTURE = "RTL_RESTRUCTURE"
KEEP_GEOMETRY = "KEEP_GEOMETRY"
# The page's arrangement mirrors: this object's place is reflected about its
# page's axis and, for a group or a cluster, so is the place of every piece
# inside it -- which is exactly what reflecting every piece about the page axis
# on its own would do, and why the page cannot overlap itself afterwards. A
# piece's own drawing is never turned round (type and pictures stay readable);
# only a purely decorative outline is, via `rtl.reflect_path`. Contrast
# `RTL_REPOSITION`, which moves a unit and keeps its inside exactly as drawn.
RTL_MIRROR = "RTL_MIRROR"

ACTIONS = (KEEP_POSITION, TEXT_ONLY_RTL, RTL_REPOSITION,
           MIRROR_GRAPHIC, RTL_RESTRUCTURE, KEEP_GEOMETRY, RTL_MIRROR)

MOVING_ACTIONS = (RTL_REPOSITION, RTL_RESTRUCTURE, RTL_MIRROR)

# Orientation, independent of position.
KEEP_ORIENTATION = "KEEP_ORIENTATION"

# Text, independent of both.
KEEP_TEXT = "KEEP_TEXT"
TEXT_RTL = "TEXT_RTL"
TEXT_RTL_LTR_PINNED = "TEXT_RTL_LTR_PINNED"


@dataclass(frozen=True)
class Decision:
    page: int | None
    spread: str
    object: str
    component: str | None
    type: str
    layer: str | None
    object_style: str | None
    paragraph_styles: tuple
    bounds: tuple | None
    new_bounds: tuple | None
    orientation: str
    new_orientation: str
    action: str
    text: str
    rule: str
    reason: str
    # True when this object's position is decided by its component rather than
    # by its own rule. A structural fact, not a rule name: the executor has to
    # know that this object is carried by its component's single move, and
    # deciding that by matching the string "component.bound" made a rule id --
    # which is documentation -- load-bearing, so renaming one would silently
    # change what moves.
    position_bound: bool = False
    # "group" | "cluster" | "containment" | "equation" | None, from
    # `rtl_components.Component.kind` -- how `apply_plan` finds this
    # decision's fellow members and what coordinate space they share. A `Decision` with no `component` carries `None`. Given
    # a default so old serialised plans (and hand-built ones in tests) that
    # predate this field still construct.
    component_kind: str | None = None
    # True when this object's own rule keeps its inside as drawn (a styled
    # equation), even though its position may be carried by a component. A
    # mirror that reaches it moves it whole rather than rearranging it.
    rigid: bool = False

    @property
    def moves(self) -> bool:
        return self.action in MOVING_ACTIONS

    @property
    def flips(self) -> bool:
        return self.new_orientation == MIRROR_GRAPHIC


@dataclass
class Plan:
    document: str
    language: str
    rules_family: str
    decisions: list = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {"document": self.document, "language": self.language,
             "rules_family": self.rules_family,
             "decisions": [asdict(d) for d in self.decisions]},
            indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, blob: str) -> "Plan":
        raw = json.loads(blob)
        return cls(
            document=raw["document"], language=raw["language"],
            rules_family=raw["rules_family"],
            decisions=[Decision(**{
                k: (tuple(v) if isinstance(v, list) else v)
                for k, v in d.items()}) for d in raw["decisions"]])

    def by_object(self) -> dict:
        return {d.object: d for d in self.decisions}

    def log_lines(self) -> list:
        """One line per decision, transformed or not.

        An untransformed object is logged too. A page whose furniture stayed
        put is a *decision*, and a log that only shows movement cannot tell it
        apart from a page nothing looked at.
        """
        out = []
        for d in self.decisions:
            new = "unchanged" if d.new_bounds in (None, d.bounds) else \
                "[" + ",".join(f"{v:.1f}" for v in d.new_bounds) + "]"
            old = "-" if d.bounds is None else \
                "[" + ",".join(f"{v:.1f}" for v in d.bounds) + "]"
            out.append(
                f"Page {d.page} | {d.object} | {d.type} | {old} | {new} | "
                f"{d.orientation} | {d.new_orientation} | {d.action} | "
                f"{d.reason}")
        return out


# ---- classification --------------------------------------------------------


def _spread_extents(documents: dict) -> dict:
    """Spread `Self` -> `rtl.page_extents` for that spread, in spread space.

    A rule that needs a real page width -- none does yet, but `PageContext`
    carries the field for one that will -- must recover it honestly, from the
    same `<Page GeometricBounds=... ItemTransform=...>` geometry
    `rtl_features.collect` already reads to build `x_band`, not from a
    guessed constant page size. Nothing here guarantees a book is Letter,
    A4 or anything else.
    """
    from pagebirdy.idml import rtl

    index: dict = {}
    for doc, tree in documents.items():
        if not doc.startswith(("Spreads/", "MasterSpreads/")):
            continue
        for spread in tree.iter("Spread", "MasterSpread"):
            index[spread.get("Self")] = rtl.page_extents(spread)
    return index


def _page_width(feature, spread_extents: dict) -> float | None:
    """`feature`'s own page width in points, or `None` when it has none.

    An anchored object (nested in a story, not a spread) resolves no
    `page_index` at all, and a feature whose spread never made it into
    `spread_extents` (a malformed or partial package) is no better off --
    both get an honest `None` rather than a borrowed width from a page the
    object isn't actually on.
    """
    extents = spread_extents.get(feature.spread)
    if extents is None or feature.page_index is None \
            or feature.page_index >= len(extents):
        return None
    x0, x1 = extents[feature.page_index]
    return x1 - x0


def get_rtl_transformation(feature, page_context, component_context, table):
    """The decision for one object. Pure: no XML, no I/O, no mutation."""
    from pagebirdy.idml import rtl_rules

    rule = rtl_rules.first_match(table, feature, page_context,
                                 component_context)
    return Decision(
        page=feature.page_index, spread=feature.spread,
        object=feature.self_id,
        component=(component_context.component_id
                   if component_context is not None else None),
        component_kind=(component_context.kind
                        if component_context is not None else None),
        type=feature.kind, layer=feature.layer,
        object_style=feature.object_style,
        paragraph_styles=tuple(sorted(feature.paragraph_styles)),
        bounds=feature.bounds, new_bounds=feature.bounds,
        orientation=KEEP_ORIENTATION, new_orientation=rule.orientation,
        action=rule.action, text=rule.text,
        rule=rule.rule_id, reason=rule.reason)


def _select_anchor(comp, by_id):
    """The member whose own classification should govern a cluster's
    decision, when the component has no anchor object of its own (a
    containment component's component_id already resolves to the field
    directly, via by_id.get above -- this only matters for proximity and
    vertical clusters, whose component_id is a synthetic "cluster:..."
    string).

    Prefers the first member (by document order, i.e. member_ids order)
    that is not a form field. A form-field-styled object's own rule is
    always KEEP_POSITION; letting it become the anchor purely because it
    happened to be first in document order would freeze an otherwise
    ordinary, unrelated cluster as a side effect of iteration order -- the
    mirror image of the bug containment clustering (rtl_components.py)
    exists to fix. If every member is a form field, there is nothing else
    to prefer and document order stands -- freezing is the correct answer
    for an all-form-field cluster anyway.
    """
    from pagebirdy.idml import rtl_components

    for member_id in comp.member_ids:
        member = by_id.get(member_id)
        if member is not None and not rtl_components.is_form_field(member):
            return member
    return by_id[comp.member_ids[0]]


# How far short of the group's full width a backdrop may stop: float noise on
# shapes drawn flush with one another, not a design difference.
_BACKDROP_TOL = 0.5


def _sets_text_in_a_box(group, members, host) -> bool:
    """True for an inline group that is a box with text set inside it.

    A backdrop -- a piece that is not a text frame -- spans the group's whole
    width, and at least one text frame is set on it. Only then is a text
    frame's place in the group an indent inside its own box, which turns with
    reading direction; an outline drawn along part of the box (RCM07 L05 rules
    its box only as far as the text runs) turns with it. A picture beside its
    caption, or labels set around an expression that keeps its left-to-right
    order, has no box behind it: that arrangement has a meaning of its own and
    is left as drawn.

    Reflecting the pieces about the group's own vertical axis is a mirror only
    while that axis is the page's, so a group turned off the page, or flowed
    in a frame that is, never qualifies.
    """
    if group.rotated or (host is not None and host.rotated):
        return False
    if any(m.local_bounds is None or m.rotated for m in members):
        return False
    text = [m for m in members if m.kind == "TextFrame"]
    backdrops = [m for m in members if m.kind != "TextFrame"]
    if not text or not backdrops:
        return False
    x0 = min(m.local_bounds[0] for m in members)
    x1 = max(m.local_bounds[2] for m in members)
    return any(b.local_bounds[0] <= x0 + _BACKDROP_TOL
               and b.local_bounds[2] >= x1 - _BACKDROP_TOL for b in backdrops)


def build_plan(documents: dict, *, document: str, language: str,
               family: str | None = None, keep_upright=()) -> Plan:
    """Classify every object and component in a parsed package.

    Components first. A component's decision binds its members, which are then
    not classified again: that is what stops an arrow being flipped while the
    sentence it introduces stays put.

    `KEEP_GEOMETRY` propagates downwards. A number line's tick labels are
    separate frames, and a per-object walk would happily reposition each one;
    the barrier is what makes "do not blindly mirror mathematics" a property of
    the subtree rather than of one frame.
    """
    from pagebirdy.idml import rtl_components, rtl_features, rtl_rules

    table = rtl_rules.get_rules(family, language)
    if keep_upright:
        # A graphic the artwork stage rewrote holds a picture of the
        # translation. Feeding those URIs in as exceptions is how a rule stays
        # pure while still knowing about this run.
        table = rtl_rules.RuleTable(
            family=table.family, rules=table.rules, markers=table.markers,
            mirror_decorative_bleed=table.mirror_decorative_bleed,
            never_flip_links=table.never_flip_links | frozenset(keep_upright))

    features = rtl_features.collect(documents)
    spread_extents = _spread_extents(documents)
    children: dict = {}
    for f in features:
        if f.parent_id is not None:
            children.setdefault(f.parent_id, []).append(f)
    # Page furniture takes part in no composition. A vertical lesson title
    # sitting beside a math console is close enough to cluster with it, and a
    # bound member goes wherever its component goes -- which carried the title
    # clear across the page. Decided without a component on purpose: whether
    # something is template furniture never depends on what it sits next to.
    furniture = {
        f.self_id for f in features
        if rtl_rules.first_match(table, f, rtl_rules.PageContext(
            page_index=f.page_index, page_width=_page_width(f, spread_extents),
            is_master=f.is_master_item), None).rule_id in rtl_rules.FURNITURE_RULES}
    components = rtl_components.detect(
        [f for f in features if f.self_id not in furniture], table.markers)
    by_id = {f.self_id: f for f in features}
    owner = {m: c for c in components for m in c.member_ids}
    for c in components:
        owner.setdefault(c.component_id, c)

    decisions: list = []
    barred: set = set()
    component_action: dict = {}
    component_anchor: dict = {}

    # Components first, in document order of their first member. The
    # component's own decision -- computed on its anchor -- is the one place
    # the real action (RTL_RESTRUCTURE, MIRROR_GRAPHIC, whatever the table
    # says) gets recorded for the whole composition.
    for comp in sorted(components,
                       key=lambda c: by_id[c.member_ids[0]].z_index):
        anchor = by_id.get(comp.component_id) or _select_anchor(comp, by_id)
        ctx = rtl_rules.PageContext(
            page_index=comp.page_index,
            page_width=_page_width(anchor, spread_extents),
            is_master=anchor.is_master_item)
        d = get_rtl_transformation(anchor, ctx, comp, table)
        if comp.kind == "cluster" and d.action == RTL_REPOSITION:
            d = replace(d, action=RTL_MIRROR)
        component_action[comp.component_id] = d.action
        component_anchor[comp.component_id] = anchor.self_id
        if d.action == KEEP_GEOMETRY:
            barred.update(comp.member_ids)

    # What each object's own rule says, before component binding or the
    # barrier rewrite it. The barrier walk needs this: an ordinary frame that
    # `math.styled` or `math.vector_art` locked is neither a component nor a
    # component member, so without a record of its own answer its descendants
    # walk straight out of a locked diagram.
    own_action: dict = {}
    for f in features:
        ctx = rtl_rules.PageContext(
            page_index=f.page_index,
            page_width=_page_width(f, spread_extents),
            is_master=f.is_master_item)
        own_action[f.self_id] = get_rtl_transformation(
            f, ctx, owner.get(f.self_id), table).action

    for f in features:
        comp = owner.get(f.self_id)
        ctx = rtl_rules.PageContext(
            page_index=f.page_index,
            page_width=_page_width(f, spread_extents),
            is_master=f.is_master_item)
        d = get_rtl_transformation(f, ctx, comp, table)

        # A non-anchor member's *position* is not its own to decide -- the
        # component already decided it, above. Re-running first_match per
        # member on this axis is exactly what let one member of a
        # directional pair restructure while its sibling stayed KEEP_POSITION:
        # two different position answers for one composition, the "arrow
        # flips while the sentence stays put" failure this module exists to
        # prevent. Orientation and text are left as get_rtl_transformation
        # already computed them, above, from this object's own properties:
        # they are independent axes -- a decorative photo inside an
        # otherwise-static group still needs its own mirror answer -- and the
        # spec never asks for them to be inherited, only position.
        if d.action in (RTL_REPOSITION, KEEP_GEOMETRY):
            d = replace(d, rigid=True)
            # Rigid means the object's *own* inside is kept as drawn. A
            # proximity cluster is not its inside: an equation that happens to
            # anchor one must not freeze the arrangement of the diagram beside
            # it, so the cluster mirrors piece by piece and the equation, one
            # of those pieces, still crosses the page whole.
            if (comp is not None and comp.kind == "cluster"
                    and d.action == RTL_REPOSITION):
                d = replace(d, action=RTL_MIRROR)
        if comp is not None and f.self_id != component_anchor[comp.component_id]:
            d = replace(d, action=KEEP_POSITION, rule="component.bound",
                        position_bound=True,
                        reason=f"position bound to component "
                               f"{comp.component_id} decision")

        # An anchored object has no page position to change: it is placed by
        # the text flow of the story that owns it, and the executor walks
        # spreads, not stories, so a positional action on one is an
        # instruction nothing carries out. Recording it anyway made the plan
        # claim movement that never happened -- half the corpus's "moved"
        # objects were anchored, so the calibration report overstated what the
        # engine does. Orientation and text still apply: those travel with the
        # object wherever the flow puts it.
        #
        # One thing about an inline group *is* the engine's to change: where
        # a text frame sits inside the box drawn around it. That is an indent,
        # and it turns with the text -- the flow already puts the box against
        # the line's new start edge, and a problem left on the box's old side
        # prints under the picture that mirrored onto that side of the page.
        inline_box = False
        if f.anchored and d.action in MOVING_ACTIONS:
            if (f.kind == "Group" and not d.rigid and not d.position_bound
                    and _sets_text_in_a_box(f, children.get(f.self_id, ()),
                                            by_id.get(f.parent_id))):
                inline_box = True
                d = replace(d, action=RTL_RESTRUCTURE, rule="anchored.text_box",
                            reason="text frame mirrors within its inline box; "
                                   "the box itself is placed by text flow")
            else:
                d = replace(d, action=KEEP_POSITION, rule="anchored.flowed",
                            reason="anchored object is placed by text flow, "
                                   "not by page geometry")

        # A nested page item -- a picture inside its frame, a frame inside a
        # form control, a group's child -- has its `ItemTransform` written in
        # its parent's space, so wherever the parent goes it goes too. Moving
        # it on its own account as well moves it twice, and the executor would
        # measure that second move in spread space while applying it in the
        # parent's. A group's children are rearranged by the group's own
        # mirror (`rtl._mirror_arrangement`), never by a decision of their own.
        # An inline box's parent is the frame flowing its text, which carries
        # the box but does not rearrange it.
        if (f.parent_id is not None and f.parent_id in by_id and not inline_box
                and not d.position_bound and d.action in MOVING_ACTIONS):
            d = replace(d, action=KEEP_POSITION, rule="nested.carried",
                        reason="carried by its parent's move")

        # A barred descendant may not move, whatever the above decided --
        # this wins over component.bound too, so a member of an otherwise
        # ordinary composition that happens to sit inside a KEEP_GEOMETRY
        # ancestor still may not move. `seen` guards a walk that should
        # never cycle (`parent_id` comes from collect()'s single top-down
        # tree walk) but a silent hang is a worse failure than a loud one.
        parent = f.parent_id
        seen: set = set()
        while parent is not None and parent not in seen:
            seen.add(parent)
            # Three ways an ancestor can hold the lock: it is a member of a
            # KEEP_GEOMETRY component, it *is* such a component, or it is an
            # ordinary frame that `math.styled`/`math.vector_art` locked on its
            # own account. The third was missing, so a callout inside a locked
            # diagram frame -- no component anywhere -- was free to be
            # repositioned out of it.
            if (parent in barred
                    or component_action.get(parent) == KEEP_GEOMETRY
                    or own_action.get(parent) == KEEP_GEOMETRY):
                d = replace(d, action=KEEP_GEOMETRY, rule="math.barrier",
                            reason="inside a KEEP_GEOMETRY subtree")
                break
            parent = by_id[parent].parent_id if parent in by_id else None

        decisions.append(d)

    return Plan(document=document, language=language,
                rules_family=table.family, decisions=decisions)
