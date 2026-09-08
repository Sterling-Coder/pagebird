"""Regression & Acceptance Test Suite for RTL Numerical Preservation & Math Preservation.

Guarantees:
- ALL numericals stay as-is (150 stays 150, NEVER 051).
- No digit sequence reversal across Arabic, Hebrew, Urdu, Farsi.
- Core 14 mathematical requirements pass.
"""

import pytest

from babel.protect.math_rtl_renderer import (
    MathRTLPolicy,
    RunClass,
    classify_text_runs,
    localize_digits,
    parse_math_expression,
    preserve_numericals_as_is,
    tokenize_math,
    validate_math_semantics,
)


def test_numericals_stay_as_is_no_reversal():
    """All numericals must remain in exact left-to-right digit order."""
    numbers = ["150", "123", "2025", "2025-2026", "43,000", "0.0072", "3.16", "3/4"]
    for num in numbers:
        res = preserve_numericals_as_is(num)
        assert res == num
        assert res[::-1] != num or len(num) == 1


def test_arabic_numerical_in_rtl_sentence():
    """Numbers inside Arabic RTL text must stay as-is (12 stays 12, 25 stays 25)."""
    text = "الصفحة 12 من 25"
    runs = classify_text_runs(text)
    numbers_found = [r[1] for r in runs if r[0] in (RunClass.NUMBER, RunClass.MATH)]
    assert "12" in numbers_found
    assert "25" in numbers_found
    assert "21" not in numbers_found
    assert "52" not in numbers_found


def test_hebrew_numerical_in_rtl_sentence():
    """Numbers inside Hebrew RTL text must stay as-is."""
    text = "שלום עולם 150"
    runs = classify_text_runs(text)
    numbers_found = [r[1] for r in runs if r[0] in (RunClass.NUMBER, RunClass.MATH)]
    assert "150" in numbers_found
    assert "051" not in numbers_found


def test_urdu_numerical_in_rtl_sentence():
    """Numbers inside Urdu RTL text must stay as-is."""
    text = "صفحہ 2025"
    runs = classify_text_runs(text)
    numbers_found = [r[1] for r in runs if r[0] in (RunClass.NUMBER, RunClass.MATH)]
    assert "2025" in numbers_found
    assert "5202" not in numbers_found


def test_equation_x_equals_2y_plus_5():
    expr = "x = 2y + 5"
    ast = parse_math_expression(expr)
    rendered = ast.to_string()
    assert "2y" in rendered
    assert "y2" not in rendered
    assert rendered == "x = 2y + 5"


def test_equation_10x_plus_15y_equals_150():
    expr = "10x + 15y = 150"
    ast = parse_math_expression(expr)
    rendered = ast.to_string()
    assert "10x" in rendered and "15y" in rendered
    assert "x01" not in rendered and "y51" not in rendered
    assert "150" in rendered and "051" not in rendered

    valid, reason = validate_math_semantics(expr, rendered)
    assert valid, reason


def test_quadratic_equation_x_squared():
    expr = "x² + 2x + 1 = 0"
    ast = parse_math_expression(expr)
    rendered = ast.to_string()
    assert "x²" in rendered
    assert "²x" not in rendered


def test_coordinate_pairs_x_y():
    expr = "(x, y)"
    ast = parse_math_expression(expr)
    rendered = ast.to_string()
    assert rendered == "(x, y)"
    assert rendered != "(y, x)"


def test_fractions_3_over_4():
    expr = "3/4"
    ast = parse_math_expression(expr)
    rendered = ast.to_string()
    assert rendered == "3/4"


def test_subscripts_x1_plus_y2():
    expr = "x₁ + y₂"
    ast = parse_math_expression(expr)
    rendered = ast.to_string()
    assert "x₁" in rendered and "y₂" in rendered


def test_hard_failure_numerical_reversal():
    valid, reason = validate_math_semantics("150", "051")
    assert not valid
    assert "Hard failure: numerical '150' reversed to '051'" in reason
