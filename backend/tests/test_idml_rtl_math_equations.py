"""An equation crosses the page whole; its own order never turns round.

A designer builds

    3  ·  4  =  12
    2  ·  4  =   8
    1  ·  4  =   4

out of one text frame per token, laid out on a grid. Every other composition
on the page mirrors piece by piece -- that is what stops a mirrored page
overlapping itself -- but doing it here reflects each token about the page
axis on its own and prints the first row as `12 = 4 · 3`, and reflecting each
row about its own union instead pulls rows of different widths out of
alignment with one another.

So the block is a component (`rtl_components`, kind `"equation"`), the rule
is `math.equation` -> `RTL_REPOSITION`, and the executor moves every member
by one delta measured once from the block's union. These tests are written
against that contract, not against any one book: no page, lesson or
coordinate from a real document appears here.
"""

from lxml import etree

from pagebirdy import script
from pagebirdy.idml import rtl, rtl_components, rtl_features, rtl_plan, rtl_rules

# A single 612pt page, so the mirror axis is 306 and every expected number
# below is arithmetic anyone can redo by hand.
PAGE_WIDTH = 612.0
AXIS = PAGE_WIDTH / 2.0

SPREAD = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Spread xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  <{tag} Self="spr" PageCount="1" ItemTransform="1 0 0 1 0 0">
    <Page Self="p1" GeometricBounds="0 0 783 612" ItemTransform="1 0 0 1 0 -391.5"/>
    {items}
  </{tag}>
</idPkg:Spread>
"""

STORIES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="16.0">
  {stories}
</idPkg:Story>
"""


def _geometry(x0, y0, x1, y1):
    return (f'<Properties><PathGeometry><GeometryPathType PathOpen="false">'
            f'<PathPointArray>'
            f'<PathPointType Anchor="{x0} {y0}"/>'
            f'<PathPointType Anchor="{x0} {y1}"/>'
            f'<PathPointType Anchor="{x1} {y1}"/>'
            f'<PathPointType Anchor="{x1} {y0}"/>'
            f'</PathPointArray></GeometryPathType></PathGeometry></Properties>')


def _text_frame(self_id, story_id, box, **attrs):
    extra = "".join(f' {k}="{v}"' for k, v in attrs.items())
    return (f'<TextFrame Self="{self_id}" ParentStory="{story_id}" '
            f'ItemTransform="1 0 0 1 0 0" ItemLayer="layer"{extra}>'
            f'{_geometry(*box)}</TextFrame>')


def _bracket(self_id, x0, x1, y0, y1):
    """An asymmetric outline -- a long-division bracket -- drawn as artwork.

    Asymmetric on purpose: a rectangle reflects into an identical rectangle,
    so only a shape like this can show whether `reflect_path` ran on a piece
    of an equation that should have been left exactly as drawn.
    """
    mid_y = (y0 + y1) / 2.0
    return (f'<Polygon Self="{self_id}" ItemTransform="1 0 0 1 0 0" '
            f'ItemLayer="layer">'
            f'<Properties><PathGeometry><GeometryPathType PathOpen="true">'
            f'<PathPointArray>'
            f'<PathPointType Anchor="{x0} {y0}"/>'
            f'<PathPointType Anchor="{x1} {mid_y}"/>'
            f'<PathPointType Anchor="{x0} {y1}"/>'
            f'</PathPointArray></GeometryPathType></PathGeometry></Properties>'
            f'</Polygon>')


def _story(story_id, text, style="Body"):
    return (f'<Story Self="{story_id}">'
            f'<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/{style}">'
            f'<CharacterStyleRange><Content>{text}</Content></CharacterStyleRange>'
            f'</ParagraphStyleRange></Story>')


def _docs(items, stories, master=False):
    tag = "MasterSpread" if master else "Spread"
    name = "MasterSpreads/M.xml" if master else "Spreads/S.xml"
    return {
        name: etree.fromstring(
            SPREAD.format(tag=tag, items="".join(items)).encode()),
        "Stories/Story.xml": etree.fromstring(
            STORIES.format(stories="".join(stories)).encode()),
    }


def _row(prefix, tokens, y0, y1, x=100.0, width=18.0, gap=6.0):
    """One equation row: a frame per token, `gap` apart, left to right.

    Returns (items, stories, placements) where placements is
    `[(self_id, text, x0, x1), ...]` in the order they were drawn.
    """
    items, stories, placements = [], [], []
    cursor = x
    for i, text in enumerate(tokens):
        self_id, story_id = f"{prefix}{i}", f"s_{prefix}{i}"
        items.append(_text_frame(self_id, story_id, (cursor, y0, cursor + width, y1)))
        stories.append(_story(story_id, text))
        placements.append((self_id, text, cursor, cursor + width))
        cursor += width + gap
    return items, stories, placements


def _element(docs, self_id):
    for tree in docs.values():
        hit = tree.find(f".//*[@Self='{self_id}']")
        if hit is not None:
            return hit
    raise AssertionError(f"no element {self_id!r}")


def _x0(docs, self_id):
    """`self_id`'s left edge in spread space, wherever it sits in the tree."""
    el = _element(docs, self_id)
    parent = rtl.IDENTITY
    for ancestor in reversed([a for a in el.iterancestors()
                              if rtl._is_page_item(a)]):
        parent = rtl.compose(parent, rtl.parse_transform(
            ancestor.get("ItemTransform")))
    return rtl.item_bounds(el, parent)[0]


def _matrix(docs, self_id):
    """`self_id`'s own `ItemTransform`, as written."""
    return rtl.parse_transform(_element(docs, self_id).get("ItemTransform"))


def _reading_order(docs, placements):
    """The tokens as they now read left to right across the page."""
    return [text for _, text in
            sorted((_x0(docs, self_id), text) for self_id, text, _, _ in placements)]


def _run(docs, language="ar"):
    plan = rtl_plan.build_plan(docs, document="doc", language=language)
    rtl.apply_plan(docs, plan)
    return plan


def _equation_decisions(plan):
    return [d for d in plan.decisions if d.component_kind == "equation"]


# ---- the text test, which everything else is built on ----------------------


def test_only_mathematics_reads_as_mathematics():
    for text in ("3", "·", "4", "=", "12", "-8", "____", "-2",
                 "x", "2(x + 3) = 10", "3/4", "x²", "-1 · 4 = ____"):
        assert script.is_math_expression(text), text
    for text in ("Divide", "the answer", "12 cm", "Lesson 12", "page 3",
                 "العدد", "العدد 12", "", "   ", ".", "("):
        assert not script.is_math_expression(text), text


def test_a_bare_number_is_not_evidence_of_an_equation():
    """`is_math_expression` says a token *may* be part of one; only an
    operator says one is there. Without this a figure label beside a folio
    would be frozen as mathematics."""
    assert script.is_math_expression("12") and not script.contains_math_operator("12")
    for text in ("=", "+", "3 · 4", "x × 2", "a ÷ b"):
        assert script.contains_math_operator(text), text


# ---- 1-3, 5: one row, in each of the shapes the source uses ----------------


def _one_row_case(tokens):
    items, stories, placements = _row("t", tokens, y0=200.0, y1=212.0)
    docs = _docs(items, stories)
    before = {self_id: _x0(docs, self_id) for self_id, _, _, _ in placements}
    plan = _run(docs)
    after = {self_id: _x0(docs, self_id) for self_id, _, _, _ in placements}
    return docs, plan, placements, before, after


def test_a_simple_equation_keeps_its_order_and_its_spacing():
    docs, _plan, placements, before, after = _one_row_case(
        ["3", "·", "4", "=", "12"])

    assert _reading_order(docs, placements) == ["3", "·", "4", "=", "12"]
    deltas = {after[k] - before[k] for k in before}
    assert len(deltas) == 1, f"members moved by different deltas: {deltas}"


def test_a_negative_number_equation_keeps_its_order():
    docs, _, placements, before, after = _one_row_case(
        ["-2", "·", "4", "=", "-8"])
    assert _reading_order(docs, placements) == ["-2", "·", "4", "=", "-8"]
    assert len({after[k] - before[k] for k in before}) == 1


def test_an_equation_ending_in_a_blank_keeps_its_order():
    docs, _, placements, before, after = _one_row_case(
        ["-1", "·", "4", "=", "____"])
    assert _reading_order(docs, placements) == ["-1", "·", "4", "=", "____"]
    assert len({after[k] - before[k] for k in before}) == 1


def test_an_equation_with_the_blank_in_the_middle_keeps_its_order():
    """The blank is an operand like any other: it has to stay in the slot the
    question put it in, or the question changes."""
    docs, _, placements, before, after = _one_row_case(
        ["-2", "·", "____", "=", "-8"])
    assert _reading_order(docs, placements) == ["-2", "·", "____", "=", "-8"]
    assert len({after[k] - before[k] for k in before}) == 1


# ---- 4, 6: several rows, which have to stay aligned with one another -------


def _three_rows():
    rows = [["3", "·", "4", "=", "12"],
            ["2", "·", "4", "=", "8"],
            ["1", "·", "4", "=", "4"]]
    items, stories, placements = [], [], []
    for r, tokens in enumerate(rows):
        y0 = 200.0 + r * 18.0
        i, s, p = _row(f"r{r}c", tokens, y0=y0, y1=y0 + 12.0)
        items += i
        stories += s
        placements += p
    return _docs(items, stories), placements


def test_vertically_aligned_rows_are_one_block_and_move_by_one_delta():
    docs, placements = _three_rows()
    before = {self_id: _x0(docs, self_id) for self_id, _, _, _ in placements}
    plan = _run(docs)
    after = {self_id: _x0(docs, self_id) for self_id, _, _, _ in placements}

    decisions = _equation_decisions(plan)
    assert len(decisions) == len(placements), "the rows did not form one block"
    assert len({d.component for d in decisions}) == 1

    deltas = {round(after[k] - before[k], 6) for k in before}
    assert len(deltas) == 1, f"rows drifted apart: {deltas}"


def test_every_relative_offset_inside_a_multi_row_block_is_unchanged():
    """The strongest statement of the contract: whatever the block's new
    origin is, the arrangement inside it is the arrangement that was drawn.
    Asserted over every pair, so a reversal, a per-row reflection and a
    single stray member are each caught."""
    docs, placements = _three_rows()
    before = {self_id: _x0(docs, self_id) for self_id, _, _, _ in placements}
    _run(docs)
    after = {self_id: _x0(docs, self_id) for self_id, _, _, _ in placements}

    ids = [self_id for self_id, _, _, _ in placements]
    for a in ids:
        for b in ids:
            assert after[a] - after[b] == before[a] - before[b], (a, b)


# ---- 7, 8: the block moves; its children are not mirrored one by one -------


def test_the_block_itself_is_repositioned_to_the_rtl_side_of_the_page():
    docs, placements = _three_rows()
    x0_before = min(_x0(docs, i) for i, _, _, _ in placements)
    plan = _run(docs)

    anchor = next(d for d in _equation_decisions(plan) if not d.position_bound)
    assert anchor.rule == "math.equation"
    assert anchor.action == rtl_plan.RTL_REPOSITION

    widths = [x1 - x00 for _, _, x00, x1 in placements]
    span = (max(x1 for _, _, _, x1 in placements)
            - min(x00 for _, _, x00, _ in placements))
    x0_after = min(_x0(docs, i) for i, _, _, _ in placements)
    # The block started on the left of the page and the whole of it is now on
    # the right: its union reflected about the page axis.
    assert x0_before < AXIS - span
    assert x0_after == 2 * AXIS - (x0_before + span)
    assert widths  # the fixture really did draw separate frames


def test_no_child_of_the_block_is_reflected_on_its_own_account():
    """The failure this exists to prevent, stated as the arithmetic that
    produces it.

    Reflecting a member about the page axis on its own puts it at
    `2*axis - (x0 + x1)`, and doing that to every member reverses each row --
    which is exactly what the page mirror does to any other composition. The
    block instead takes one delta from its own union, so the assertion is
    that every member landed on the shared-delta layout and that the layout
    it did *not* land on reads backwards.
    """
    docs, placements = _three_rows()
    span = (min(x0 for _, _, x0, _ in placements),
            max(x1 for _, _, _, x1 in placements))
    shared = 2 * AXIS - (span[0] + span[1])

    _run(docs)

    for self_id, _, x0, _ in placements:
        assert _x0(docs, self_id) == x0 + shared, self_id
    # ...and the layout that was refused really is the reversed one.
    first_row = [p for p in placements if p[0].startswith("r0c")]
    reversed_layout = sorted(
        (x0 + (2 * AXIS - (x0 + x1)), text) for _, text, x0, x1 in first_row)
    assert [t for _, t in reversed_layout] == ["12", "=", "4", "·", "3"]
    for r in range(3):
        row = [p for p in placements if p[0].startswith(f"r{r}c")]
        assert _reading_order(docs, row) == [text for _, text, _, _ in row]


def test_a_piece_of_artwork_in_the_block_travels_with_it_and_is_not_turned_round():
    """A long-division bracket means the opposite of itself reversed. It
    joins the block -- so it keeps its place among the tokens -- and its own
    outline is left exactly as drawn, unlike a direction arrow's."""
    items, stories, placements = _row("t", ["12", "=", "4"], y0=200.0, y1=212.0)
    items.append(_bracket("brk", 170.0, 182.0, 200.0, 212.0))
    docs = _docs(items, stories)

    def anchors():
        el = _element(docs, "brk")
        return [float(p.get("Anchor").split()[0]) for p
                in el.find("./Properties/PathGeometry").iter("PathPointType")]

    before_outline = anchors()
    before = {i: _x0(docs, i) for i, _, _, _ in placements}
    before["brk"] = _x0(docs, "brk")

    plan = _run(docs)

    assert "brk" in {d.object for d in _equation_decisions(plan)}
    after = {i: _x0(docs, i) for i, _, _, _ in placements}
    after["brk"] = _x0(docs, "brk")
    assert len({round(after[k] - before[k], 6) for k in before}) == 1
    assert anchors() == before_outline, "the bracket's own outline turned round"


# ---- the shapes a designer draws an equation in ----------------------------


def test_a_group_the_designer_drew_the_equation_with_moves_as_one_unit():
    items, stories, placements = _row("t", ["3", "·", "4", "=", "12"],
                                      y0=200.0, y1=212.0)
    grouped = [('<Group Self="grp" ItemTransform="1 0 0 1 0 0" '
                'ItemLayer="layer">' + "".join(items) + "</Group>")]
    docs = _docs(grouped, stories)
    before = {i: _x0(docs, i) for i, _, _, _ in placements}

    plan = _run(docs)

    group = next(d for d in plan.decisions if d.object == "grp")
    assert group.rule == "math.equation"
    assert group.action == rtl_plan.RTL_REPOSITION
    after = {i: _x0(docs, i) for i, _, _, _ in placements}
    assert len({round(after[k] - before[k], 6) for k in before}) == 1
    assert _reading_order(docs, placements) == ["3", "·", "4", "=", "12"]


def test_an_equation_among_a_mirroring_groups_children_travels_whole():
    """A worked example: a heading that mirrors with the group, and under it
    an equation that must not. The group is not an equation, so it mirrors
    its arrangement -- and the equation is one of the things being
    rearranged, as a single unit rather than five."""
    items, stories, placements = _row("t", ["3", "·", "4", "=", "12"],
                                      y0=220.0, y1=232.0)
    items.append(_text_frame("head", "s_head", (100.0, 200.0, 280.0, 214.0)))
    stories.append(_story("s_head", "Find the product"))
    grouped = [('<Group Self="grp" ItemTransform="1 0 0 1 0 0" '
                'ItemLayer="layer">' + "".join(items) + "</Group>")]
    docs = _docs(grouped, stories)
    before = {i: _x0(docs, i) for i, _, _, _ in placements}

    plan = _run(docs)

    group = next(d for d in plan.decisions if d.object == "grp")
    assert group.rule != "math.equation"
    assert {d.object for d in _equation_decisions(plan)} == set(before)
    after = {i: _x0(docs, i) for i, _, _, _ in placements}
    assert len({round(after[k] - before[k], 6) for k in before}) == 1
    assert _reading_order(docs, placements) == ["3", "·", "4", "=", "12"]


# ---- what must not change --------------------------------------------------


def test_two_bare_numbers_side_by_side_are_not_an_equation():
    """No operator, no block: a figure label beside a folio still mirrors
    like any other page content, exactly as it did before this rule."""
    items, stories, _placements = _row("t", ["12", "7"], y0=200.0, y1=212.0)
    docs = _docs(items, stories)
    plan = _run(docs)
    assert _equation_decisions(plan) == []


def test_prose_beside_an_expression_never_joins_the_block():
    items, stories, _placements = _row("t", ["3", "=", "3"], y0=200.0, y1=212.0)
    items.append(_text_frame("prose", "s_prose", (166.0, 200.0, 320.0, 212.0)))
    stories.append(_story("s_prose", "Explain your answer"))
    docs = _docs(items, stories)
    plan = _run(docs)
    assert "prose" not in {d.object for d in _equation_decisions(plan)}


def test_normal_arabic_text_still_gets_normal_rtl_processing():
    """The translated prose on the page is untouched by any of this: it
    mirrors about the page axis and its story is turned right to left."""
    docs = _docs(
        [_text_frame("para", "s_para", (100.0, 200.0, 400.0, 240.0))],
        [_story("s_para", "اضرب العدد في أربعة")])
    before = _x0(docs, "para")
    plan = _run(docs)

    para = next(d for d in plan.decisions if d.object == "para")
    assert para.rule == "text.prose"
    assert para.action == rtl_plan.RTL_MIRROR
    assert para.component_kind is None
    # 100..400 on a 612pt page reflects to 212..512.
    assert _x0(docs, "para") == 2 * AXIS - (before + 300.0)


def test_master_items_are_still_excluded_even_when_they_hold_an_equation():
    """Page furniture takes part in no composition, mathematics included: a
    running head or a folio that happens to read as an expression stays
    exactly where the template put it."""
    items, stories, placements = _row("t", ["3", "·", "4", "=", "12"],
                                      y0=200.0, y1=212.0)
    docs = _docs(items, stories, master=True)
    before = {i: _x0(docs, i) for i, _, _, _ in placements}

    plan = _run(docs)

    assert _equation_decisions(plan) == []
    assert {d.rule for d in plan.decisions} == {"master.item"}
    assert [d for d in plan.decisions if d.moves] == []
    assert {i: _x0(docs, i) for i, _, _, _ in placements} == before


def test_the_lesson_badge_still_keeps_its_position():
    """The badge sits where the page template put it whatever else changed
    on the page, and a rule added ahead of the content block must not have
    reached it."""
    docs = _docs([_text_frame("badge", "s_badge", (500.0, 40.0, 560.0, 70.0))],
                 [_story("s_badge", "12", style="_Master Page Styles%3aFL Lesson %23")])
    before = _x0(docs, "badge")
    plan = _run(docs)
    badge = next(d for d in plan.decisions if d.object == "badge")
    assert badge.rule == "master.lesson_badge"
    assert badge.action == rtl_plan.KEEP_POSITION
    assert _x0(docs, "badge") == before


def test_a_directional_component_still_outranks_the_equation_rule():
    """A family that has named a composition directional has said something
    about it `math.equation` cannot know, so the marker wins -- the same
    deference `math.styled` already shows."""
    feature_table = rtl_rules.get_rules()
    comp = rtl_components.Component(
        component_id="equation:a", kind="equation", member_ids=("a",),
        bounds=(0.0, 0.0, 100.0, 20.0), page_index=0, spread="spr",
        directional=True, evidence="marker", math=True)
    assert not rtl_rules.p_math_equation(None, None, comp, feature_table)
    comp = rtl_components.replace(comp, directional=False)
    assert rtl_rules.p_math_equation(None, None, comp, feature_table)


def test_the_rule_is_inert_without_a_component_that_claims_mathematics():
    table = rtl_rules.get_rules()
    assert not rtl_rules.p_math_equation(None, None, None, table)
    comp = rtl_components.Component(
        component_id="cluster:a", kind="cluster", member_ids=("a",),
        bounds=(0.0, 0.0, 100.0, 20.0), page_index=0, spread="spr",
        directional=False, evidence="none")
    assert comp.math is False
    assert not rtl_rules.p_math_equation(None, None, comp, table)


# ---- the axes, stated separately ------------------------------------------


def test_a_block_moves_along_the_page_only_and_never_down_it():
    """X and Y are not symmetric here and the contract only permits one.

    A mirror is a reflection about a *vertical* axis, so the executor edits
    `tx` and nothing else -- `a b c d` are never negated (the module-wide
    rule) and `ty` is never written. Asserted on the whole matrix of every
    member, because "relative X/Y offsets are unchanged" is only true if the
    Y offsets were never touched in the first place.
    """
    docs, placements = _three_rows()
    before = {i: _matrix(docs, i) for i, _, _, _ in placements}

    _run(docs)

    for self_id, _, _, _ in placements:
        a, b, c, d, tx, ty = _matrix(docs, self_id)
        was = before[self_id]
        assert (a, b, c, d) == was[:4] == (1.0, 0.0, 0.0, 1.0), self_id
        assert ty == was[5], self_id
        assert tx != was[4], self_id
    # Vertical offsets between every pair therefore survive exactly.
    ids = [i for i, _, _, _ in placements]
    for x in ids:
        for y in ids:
            assert (_matrix(docs, x)[5] - _matrix(docs, y)[5]
                    == before[x][5] - before[y][5]), (x, y)


def test_a_fraction_built_from_stacked_frames_keeps_its_numerator_on_top():
    """A fraction set as numerator / rule / denominator is three items whose
    arrangement is vertical. The rule bar is artwork with no text, so it
    joins as a neutral piece rather than seeding, and the whole fraction
    travels as part of the expression it sits in."""
    items, stories, _placements = _row("t", ["1", "+"], y0=200.0, y1=212.0)
    # The fraction, to the right of "1 +": numerator over denominator with a
    # ruled bar between them.
    items.append(_text_frame("num", "s_num", (148.0, 194.0, 166.0, 206.0)))
    stories.append(_story("s_num", "3"))
    items.append(_bracket("bar", 148.0, 166.0, 206.0, 206.0))
    items.append(_text_frame("den", "s_den", (148.0, 208.0, 166.0, 220.0)))
    stories.append(_story("s_den", "4"))
    docs = _docs(items, stories)

    before = {i: _x0(docs, i) for i in ("t0", "t1", "num", "bar", "den")}
    before_y = {i: _matrix(docs, i)[5] for i in ("num", "bar", "den")}

    plan = _run(docs)

    claimed = {d.object for d in _equation_decisions(plan)}
    assert {"t0", "t1", "num", "bar", "den"} <= claimed
    after = {i: _x0(docs, i) for i in before}
    assert len({round(after[k] - before[k], 6) for k in before}) == 1
    # The numerator is still above the bar and the denominator still below.
    for i in ("num", "bar", "den"):
        assert _matrix(docs, i)[5] == before_y[i]


# ---- the math-font evidence path, and what it does without its styles -----


def _math_font_docs(font):
    docs = _docs(
        [_text_frame("f0", "s0", (100.0, 200.0, 118.0, 212.0))],
        [_story("s0", "26", style="Equation")])
    docs["Resources/Styles.xml"] = etree.fromstring((
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<idPkg:Styles xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging"'
        ' DOMVersion="16.0"><RootParagraphStyleGroup Self="rps">'
        f'<ParagraphStyle Self="ParagraphStyle/Equation" Name="Equation">'
        f'<Properties><AppliedFont type="string">{font}</AppliedFont></Properties>'
        '</ParagraphStyle></RootParagraphStyleGroup></idPkg:Styles>').encode())
    return docs


def test_an_operator_written_as_a_math_font_glyph_still_counts_as_one():
    """These books set `-6` as the character `2` in a symbol face, so no
    text test can see the sign. The face is the evidence instead -- but only
    for a frame whose text already reads as an expression."""
    docs = _math_font_docs("Mathematical Pi LT 1")
    index = rtl_features.math_font_story_index(docs)
    assert index["s0"] is True
    feature = next(f for f in rtl_features.collect(docs) if f.self_id == "f0")
    assert feature.math_text and feature.math_operator


def test_an_ordinary_face_is_not_evidence_of_an_operator():
    docs = _math_font_docs("Myriad Pro")
    assert rtl_features.math_font_story_index(docs)["s0"] is False
    feature = next(f for f in rtl_features.collect(docs) if f.self_id == "f0")
    assert feature.math_text and not feature.math_operator


def test_a_math_font_is_never_evidence_on_its_own_over_prose():
    """A sentence carrying one `=` glyph resolves a math font too. Most
    math-font stories in the corpus are exactly that, so the face may only
    ever confirm text that already reads as an expression."""
    docs = _docs(
        [_text_frame("f0", "s0", (100.0, 200.0, 300.0, 212.0))],
        [_story("s0", "Area is equal to the number of unit squares",
                style="Equation")])
    docs["Resources/Styles.xml"] = _math_font_docs(
        "Mathematical Pi LT 1")["Resources/Styles.xml"]
    assert rtl_features.math_font_story_index(docs)["s0"] is True
    feature = next(f for f in rtl_features.collect(docs) if f.self_id == "f0")
    assert not feature.math_text and not feature.math_operator


def test_without_its_styles_the_font_evidence_goes_quiet_rather_than_wrong():
    """`build_plan` sees only what a package has already parsed. With no
    `Resources/Styles.xml` the face cannot be resolved, so every story
    answers False and the visible-operator test stands alone -- a quieter
    rule, never a wrong one. `pagebirdy.cli`'s read-only plan commands parse the
    entry for this reason (`cli._parse_plan_inputs`), so what they print is
    the plan `apply_rtl` carries out."""
    docs = _math_font_docs("Mathematical Pi LT 1")
    del docs["Resources/Styles.xml"]
    assert rtl_features.math_font_story_index(docs)["s0"] is False
    feature = next(f for f in rtl_features.collect(docs) if f.self_id == "f0")
    assert feature.math_text and not feature.math_operator
