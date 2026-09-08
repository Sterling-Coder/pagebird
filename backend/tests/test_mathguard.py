from babel.models import Line, Span
from babel.protect.mathguard import build_segment, build_segments


def _line(spans, block=0, page=0, y=0):
    return Line(page=page, bbox=(0, y, 100, y + 10), spans=spans, block=block)


def prose(text):
    return Span(text=text, font="MyriadPro-Regular", size=11, color=0, bbox=(0, 0, 50, 10))


def mathspan(text):
    return Span(text=text, font="MathematicalPiLTStd-1", size=11, color=0, bbox=(0, 0, 50, 10))


def test_numbers_become_value_visible_tokens():
    seg = build_segment(_line([prose("Divide 3/4 by 2 to get the answer")]), 0)
    # Numbers are protected but their value stays visible to the translator.
    assert "⟦=3/4⟧" in seg.source and "⟦=2⟧" in seg.source
    assert not seg.has_math_font
    assert seg.restored_target() == "Divide 3/4 by 2 to get the answer"


def test_coordinate_tuple_protected():
    seg = build_segment(_line([prose("Plot A(-3, -2) on the plane")]), 0)
    # The tuple is wrapped in a single token (value visible for context)...
    assert "⟦=(-3, -2)⟧" in seg.source
    assert list(seg.placeholders.values()) == ["(-3, -2)"]
    # ...and the integrity gate treats it as one protected unit.
    from babel.translate import integrity
    assert integrity.tokens(seg.source) == integrity.tokens("x ⟦=(-3, -2)⟧ y")


def test_en_dash_range_is_one_token():
    seg = build_segment(_line([prose("For problems 1-6 plot each point")]), 0)
    # hyphen/en-dash range collapses to a single value-visible token
    assert "⟦=1-6⟧" in seg.source
    assert seg.restored_target() == "For problems 1-6 plot each point"


def test_math_font_span_is_opaque():
    seg = build_segment(_line([prose("Compute "), mathspan("x²+1")]), 0)
    assert seg.placeholders == {"⟦m0⟧": "x²+1"}
    assert seg.source == "Compute ⟦m0⟧"
    assert seg.has_math_font


def test_identical_numbers_collapse_but_restore_all():
    seg = build_segment(_line([prose("5 and 5 and 5")]), 0)
    assert seg.source == "⟦=5⟧ and ⟦=5⟧ and ⟦=5⟧"
    assert seg.placeholders == {"⟦=5⟧": "5"}
    assert seg.restored_target() == "5 and 5 and 5"


def test_consecutive_prose_lines_merge_into_paragraph():
    lines = [
        _line([prose("If point E is reflected across the")], block=1, y=0),
        _line([prose("x-axis, what are the coordinates?")], block=1, y=12),
    ]
    segs = build_segments(lines)
    assert len(segs) == 1
    assert segs[0].source == "If point E is reflected across the x-axis, what are the coordinates?"
    assert len(segs[0].bboxes) == 2


def test_math_line_breaks_paragraph_and_stays_separate():
    lines = [
        _line([prose("Write the missing digits")], block=1, y=0),
        _line([mathspan("½")], block=1, y=12),
        _line([prose("to make each equation true")], block=1, y=24),
    ]
    segs = build_segments(lines)
    assert len(segs) == 3  # prose, math, prose — not merged across the math line
    assert segs[1].has_math_font


def test_narrow_floating_annotation_does_not_merge_into_wide_paragraph():
    """A single counting-arrow digit ("1") sitting just under a wide sentence
    must not be swept into that sentence as a false continuation line.

    Regression for a real document: `_columns_align` used to measure overlap
    against only the narrower box, so any tiny annotation touching a wide
    line's x-range passed trivially — corrupting the sentence ("...you count
    3. 1") and leaving the annotation's own segment gone, which then shadowed
    out the sibling "2"/"3" labels during reassembly.
    """
    sentence = Line(
        page=0, bbox=(87.0, 299.1, 360.3, 333.0), block=1,
        spans=[Span(text="You can count on from 5 until you reach 8. You count 3.",
                     font="MyriadPro-Regular", size=12, color=0, bbox=(87.0, 310.4, 360.3, 324.0))],
    )
    annotation_1 = Line(
        page=0, bbox=(239.1, 328.3, 248.2, 346.1), block=2,
        spans=[Span(text="1", font="AvenirRdCA-Bold", size=14, color=0,
                     bbox=(239.1, 328.3, 248.2, 346.1))],
    )
    segs = build_segments([sentence, annotation_1])
    assert len(segs) == 2
    assert segs[0].source == "You can count on from ⟦=5⟧ until you reach ⟦=8⟧. You count ⟦=3⟧."
    assert segs[1].source == "⟦=1⟧"


def test_bold_header_does_not_merge_into_plain_entries_below():
    """A bold section header ("Multilingual Glossary") stacked directly above
    plain-weight list entries ("count on", "count back") must stay its own
    segment even though it clears the size-tolerance check.

    Regression for a real document: `_continues_geometry` only rejected a
    size mismatch, not a weight mismatch, so a 12pt bold header and 11pt
    regular entries (well within the 15% size tolerance) merged into one
    segment. That forced the header and the entries through one fit-to-box
    pass, which produced a wildly oversized/undersized result compared to
    every other header/body pair in the same sidebar.
    """
    header = Line(
        page=0, bbox=(452.0, 367.0, 571.3, 381.8), block=1,
        spans=[Span(text="Multilingual Glossary", font="Arial-Bold", size=12, color=0,
                     bbox=(452.0, 367.0, 571.3, 381.8))],
    )
    entry_1 = Line(
        page=0, bbox=(452.0, 381.8, 502.0, 394.5), block=1,
        spans=[Span(text="count on", font="Arial", size=11, color=0,
                     bbox=(452.0, 381.8, 502.0, 394.5))],
    )
    segs = build_segments([header, entry_1])
    assert len(segs) == 2
    assert segs[0].source == "Multilingual Glossary"
    assert segs[0].bold is True
    assert segs[1].source == "count on"
    assert segs[1].bold is False


def test_different_blocks_do_not_merge():
    lines = [
        _line([prose("Title heading")], block=0, y=0),
        _line([prose("Body instruction")], block=2, y=30),
    ]
    segs = build_segments(lines)
    assert len(segs) == 2


def test_ocr_image_line_provenance_carries_onto_segment():
    """A line recovered from OCR inside a graphic must mark its segment so
    reassembly knows to mask the original burned-in pixels."""
    ln = Line(page=0, bbox=(400, 400, 460, 420),
              spans=[prose("GO!")], block=9000, from_ocr=True, in_image=True)
    segs = build_segments([ln])
    assert len(segs) == 1
    assert segs[0].from_ocr is True
    assert segs[0].in_image is True


def test_ordinary_line_is_not_marked_as_ocr():
    seg = build_segment(_line([prose("Body instruction")]), 0)
    assert seg.from_ocr is False
    assert seg.in_image is False
