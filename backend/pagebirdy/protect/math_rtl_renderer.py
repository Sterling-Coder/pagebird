"""UAE Arabic Mathematics RTL + Layout Preservation Engine.

Dedicated module for tokenizing, parsing, transforming, and rendering mathematical
expressions and numericals inside RTL documents (Arabic, Hebrew, Urdu, Farsi).

Key Guarantees:
- ALL numericals stay as-is: left-to-right digit sequence (150 stays 150, NEVER 051).
- NO blind character reversal on numbers or math tokens.
- Directional run classification treats numbers as LTR runs embedded in RTL text.
- Semantic validation gate enforces strict non-reversal of numbers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, List, Optional, Tuple, Union


# --------------------------------------------------------------------------
# Directional Run Classes & Digit Policies
# --------------------------------------------------------------------------

class RunClass(Enum):
    RTL_TEXT = "RTL_TEXT"
    LTR_TEXT = "LTR_TEXT"
    MATH = "MATH"
    NUMBER = "NUMBER"
    SYMBOL = "SYMBOL"
    DIAGRAM_LABEL = "DIAGRAM_LABEL"
    BRAND = "BRAND"
    URL = "URL"


class MathRTLPolicy(Enum):
    PRESERVE_LTR_MATH = "PRESERVE_LTR_MATH"  # Default (LTR math inside RTL text)
    RTL_EQUATION_LEVEL = "RTL_EQUATION_LEVEL"


_ARABIC_INDIC_MAP = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
_WESTERN_ARABIC_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def preserve_numericals_as_is(text: str) -> str:
    """Ensure all numericals remain as-is in left-to-right digit order."""
    return text


def localize_digits(text: str, use_arabic_indic: bool = False) -> str:
    """Digit localization: substitution only when enabled, NEVER digit reversal.

    By default (use_arabic_indic=False), numericals remain as-is (150 -> 150).
    When enabled, 150 -> ١٥٠ (never ٠٥١ or 051).
    """
    if use_arabic_indic:
        return text.translate(_ARABIC_INDIC_MAP)
    return text


# --------------------------------------------------------------------------
# Mathematical Tokenizer
# --------------------------------------------------------------------------

class TokenType(Enum):
    NUMBER = auto()
    VARIABLE = auto()
    OPERATOR = auto()
    RELATION = auto()
    PAREN_OPEN = auto()
    PAREN_CLOSE = auto()
    BRACKET_OPEN = auto()
    BRACKET_CLOSE = auto()
    COMMA = auto()
    POWER = auto()
    SUBSCRIPT = auto()
    ROOT = auto()
    FRACTION = auto()
    SYMBOL = auto()
    TEXT = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    position: int = 0

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r})"


# Superscripts and Subscripts character mappings
_SUPERSCRIPT_MAP = {"²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁰": "0", "¹": "1", "ⁿ": "n", "⁺": "+", "⁻": "-"}
_SUBSCRIPT_MAP = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"}


def tokenize_math(expression: str) -> List[Token]:
    """Tokenize mathematical expressions preserving numericals as-is."""
    tokens: List[Token] = []
    i = 0
    length = len(expression)

    while i < length:
        ch = expression[i]

        if ch.isspace():
            i += 1
            continue

        if ch == '(':
            tokens.append(Token(TokenType.PAREN_OPEN, '(', i))
            i += 1
            continue

        if ch == ')':
            tokens.append(Token(TokenType.PAREN_CLOSE, ')', i))
            i += 1
            continue

        if ch == '[':
            tokens.append(Token(TokenType.BRACKET_OPEN, '[', i))
            i += 1
            continue

        if ch == ']':
            tokens.append(Token(TokenType.BRACKET_CLOSE, ']', i))
            i += 1
            continue

        if ch == ',':
            tokens.append(Token(TokenType.COMMA, ',', i))
            i += 1
            continue

        if ch in '^':
            tokens.append(Token(TokenType.POWER, '^', i))
            i += 1
            continue

        if ch in '_':
            tokens.append(Token(TokenType.SUBSCRIPT, '_', i))
            i += 1
            continue

        if ch in '√':
            tokens.append(Token(TokenType.ROOT, '√', i))
            i += 1
            continue

        if ch in '=<>≤≥≠≈':
            rel_val = ch
            if i + 1 < length and expression[i + 1] == '=' and ch in '<>!':
                rel_val += '='
                i += 1
            tokens.append(Token(TokenType.RELATION, rel_val, i))
            i += 1
            continue

        if ch in '+-*×÷/±·⋅':
            tokens.append(Token(TokenType.OPERATOR, ch, i))
            i += 1
            continue

        # Digits / Numericals (keep as-is, left-to-right order)
        if ch.isdigit() or (ch == '.' and i + 1 < length and expression[i + 1].isdigit()):
            start = i
            has_dot = False
            while i < length and (expression[i].isdigit() or expression[i] == '.'):
                if expression[i] == '.':
                    if has_dot:
                        break
                    has_dot = True
                i += 1
            num_str = expression[start:i]
            tokens.append(Token(TokenType.NUMBER, num_str, start))
            continue

        if ch in _SUPERSCRIPT_MAP:
            tokens.append(Token(TokenType.POWER, _SUPERSCRIPT_MAP[ch], i))
            i += 1
            continue

        if ch in _SUBSCRIPT_MAP:
            tokens.append(Token(TokenType.SUBSCRIPT, _SUBSCRIPT_MAP[ch], i))
            i += 1
            continue

        if ch.isalpha():
            start = i
            while i < length and expression[i].isalpha():
                i += 1
            var_str = expression[start:i]
            tokens.append(Token(TokenType.VARIABLE, var_str, start))
            continue

        tokens.append(Token(TokenType.SYMBOL, ch, i))
        i += 1

    return tokens


# --------------------------------------------------------------------------
# Mathematical AST Nodes
# --------------------------------------------------------------------------

@dataclass
class MathASTNode:
    def to_string(self, policy: MathRTLPolicy = MathRTLPolicy.PRESERVE_LTR_MATH) -> str:
        raise NotImplementedError


@dataclass
class NumberNode(MathASTNode):
    value: str

    def to_string(self, policy: MathRTLPolicy = MathRTLPolicy.PRESERVE_LTR_MATH) -> str:
        return self.value


@dataclass
class VariableNode(MathASTNode):
    name: str

    def to_string(self, policy: MathRTLPolicy = MathRTLPolicy.PRESERVE_LTR_MATH) -> str:
        return self.name


@dataclass
class TermNode(MathASTNode):
    coefficient: Optional[NumberNode]
    variables: List[VariableNode]

    def to_string(self, policy: MathRTLPolicy = MathRTLPolicy.PRESERVE_LTR_MATH) -> str:
        coeff = self.coefficient.to_string(policy) if self.coefficient else ""
        vars_str = "".join(v.to_string(policy) for v in self.variables)
        return f"{coeff}{vars_str}"


@dataclass
class PowerNode(MathASTNode):
    base: MathASTNode
    exponent: MathASTNode

    def to_string(self, policy: MathRTLPolicy = MathRTLPolicy.PRESERVE_LTR_MATH) -> str:
        base_str = self.base.to_string(policy)
        exp_str = self.exponent.to_string(policy)
        if exp_str in ("2", "3", "4", "5", "6", "7", "8", "9", "0"):
            sup_map = {"2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "0": "⁰"}
            return f"{base_str}{sup_map[exp_str]}"
        return f"{base_str}^{{{exp_str}}}"


@dataclass
class SubscriptNode(MathASTNode):
    base: MathASTNode
    subscript: MathASTNode

    def to_string(self, policy: MathRTLPolicy = MathRTLPolicy.PRESERVE_LTR_MATH) -> str:
        base_str = self.base.to_string(policy)
        sub_str = self.subscript.to_string(policy)
        if sub_str in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0"):
            sub_map = {"1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉", "0": "₀"}
            return f"{base_str}{sub_map[sub_str]}"
        return f"{base_str}_{{{sub_str}}}"


@dataclass
class FractionNode(MathASTNode):
    numerator: MathASTNode
    denominator: MathASTNode

    def to_string(self, policy: MathRTLPolicy = MathRTLPolicy.PRESERVE_LTR_MATH) -> str:
        num = self.numerator.to_string(policy)
        den = self.denominator.to_string(policy)
        return f"{num}/{den}"


@dataclass
class CoordinatePairNode(MathASTNode):
    x: MathASTNode
    y: MathASTNode

    def to_string(self, policy: MathRTLPolicy = MathRTLPolicy.PRESERVE_LTR_MATH) -> str:
        x_str = self.x.to_string(policy)
        y_str = self.y.to_string(policy)
        return f"({x_str}, {y_str})"


@dataclass
class BinaryOpNode(MathASTNode):
    left: MathASTNode
    operator: str
    right: MathASTNode

    def to_string(self, policy: MathRTLPolicy = MathRTLPolicy.PRESERVE_LTR_MATH) -> str:
        left_str = self.left.to_string(policy)
        right_str = self.right.to_string(policy)
        if not self.operator:
            return f"{left_str}{right_str}"
        return f"{left_str} {self.operator} {right_str}"


@dataclass
class EquationNode(MathASTNode):
    left: MathASTNode
    relation: str
    right: MathASTNode

    def to_string(self, policy: MathRTLPolicy = MathRTLPolicy.PRESERVE_LTR_MATH) -> str:
        left_str = self.left.to_string(policy)
        right_str = self.right.to_string(policy)

        if policy == MathRTLPolicy.RTL_EQUATION_LEVEL:
            return f"{right_str} {self.relation} {left_str}"

        return f"{left_str} {self.relation} {right_str}"


# --------------------------------------------------------------------------
# Parser Class
# --------------------------------------------------------------------------

class MathParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type: Optional[TokenType] = None) -> Token:
        tok = self.tokens[self.pos]
        if expected_type and tok.type != expected_type:
            raise ValueError(f"Expected token {expected_type}, got {tok.type}")
        self.pos += 1
        return tok

    def parse(self) -> MathASTNode:
        if not self.tokens:
            return NumberNode("")
        left = self.parse_expression()

        tok = self.peek()
        if tok and tok.type == TokenType.RELATION:
            rel_tok = self.consume(TokenType.RELATION)
            right = self.parse_expression()
            return EquationNode(left=left, relation=rel_tok.value, right=right)

        return left

    def parse_expression(self) -> MathASTNode:
        node = self.parse_term()
        while True:
            tok = self.peek()
            if tok and tok.type == TokenType.OPERATOR and tok.value in ('+', '-'):
                op_tok = self.consume()
                right = self.parse_term()
                node = BinaryOpNode(left=node, operator=op_tok.value, right=right)
            else:
                break
        return node

    def parse_term(self) -> MathASTNode:
        node = self.parse_factor()
        while True:
            tok = self.peek()
            if tok and tok.type == TokenType.OPERATOR and tok.value in ('*', '/', '×', '÷', '·', '⋅'):
                op_tok = self.consume()
                right = self.parse_factor()
                if op_tok.value == '/':
                    node = FractionNode(numerator=node, denominator=right)
                else:
                    node = BinaryOpNode(left=node, operator=op_tok.value, right=right)
            elif tok and tok.type in (TokenType.VARIABLE, TokenType.PAREN_OPEN, TokenType.NUMBER):
                right = self.parse_factor()
                if isinstance(node, NumberNode) and isinstance(right, VariableNode):
                    node = TermNode(coefficient=node, variables=[right])
                elif isinstance(node, TermNode) and isinstance(right, VariableNode):
                    node.variables.append(right)
                else:
                    node = BinaryOpNode(left=node, operator="", right=right)
            else:
                break
        return node

    def parse_factor(self) -> MathASTNode:
        node = self.parse_primary()

        tok = self.peek()
        if tok and tok.type == TokenType.POWER:
            p_tok = self.consume(TokenType.POWER)
            if p_tok.value and p_tok.value != '^':
                exp = NumberNode(p_tok.value)
            else:
                exp = self.parse_factor()
            node = PowerNode(base=node, exponent=exp)
        elif tok and tok.type == TokenType.SUBSCRIPT:
            s_tok = self.consume(TokenType.SUBSCRIPT)
            if s_tok.value and s_tok.value != '_':
                sub = NumberNode(s_tok.value)
            else:
                sub = self.parse_factor()
            node = SubscriptNode(base=node, subscript=sub)

        return node

    def parse_primary(self) -> MathASTNode:
        tok = self.peek()
        if not tok:
            return NumberNode("")

        if tok.type == TokenType.NUMBER:
            num_tok = self.consume(TokenType.NUMBER)
            num_node = NumberNode(num_tok.value)
            vars_list: List[VariableNode] = []
            while self.peek() and self.peek().type == TokenType.VARIABLE:
                v_tok = self.consume(TokenType.VARIABLE)
                vars_list.append(VariableNode(v_tok.value))
            if vars_list:
                return TermNode(coefficient=num_node, variables=vars_list)
            return num_node

        if tok.type == TokenType.VARIABLE:
            v_tok = self.consume(TokenType.VARIABLE)
            v_node = VariableNode(v_tok.value)
            vars_list = [v_node]
            while self.peek() and self.peek().type == TokenType.VARIABLE:
                vars_list.append(VariableNode(self.consume(TokenType.VARIABLE).value))
            if len(vars_list) > 1:
                return TermNode(coefficient=None, variables=vars_list)
            return v_node

        if tok.type == TokenType.PAREN_OPEN:
            self.consume(TokenType.PAREN_OPEN)
            inner = self.parse_expression()
            if self.peek() and self.peek().type == TokenType.COMMA:
                self.consume(TokenType.COMMA)
                y_inner = self.parse_expression()
                self.consume(TokenType.PAREN_CLOSE)
                return CoordinatePairNode(x=inner, y=y_inner)
            self.consume(TokenType.PAREN_CLOSE)
            return inner

        self.consume()
        return VariableNode(tok.value)


def parse_math_expression(expression: str) -> MathASTNode:
    tokens = tokenize_math(expression)
    parser = MathParser(tokens)
    return parser.parse()


def build_math_ast(tokens: List[Token]) -> MathASTNode:
    parser = MathParser(tokens)
    return parser.parse()


def classify_math_node(node: MathASTNode) -> str:
    return node.__class__.__name__


def apply_rtl_math_order(ast: MathASTNode, policy: MathRTLPolicy = MathRTLPolicy.PRESERVE_LTR_MATH) -> MathASTNode:
    return ast


def preserve_math_tokens(ast: MathASTNode) -> str:
    return ast.to_string(MathRTLPolicy.PRESERVE_LTR_MATH)


def render_math_ast(ast: MathASTNode, policy: MathRTLPolicy = MathRTLPolicy.PRESERVE_LTR_MATH) -> str:
    return ast.to_string(policy)


# --------------------------------------------------------------------------
# Directional Text Classification & Run Segmentation
# --------------------------------------------------------------------------

_ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")


def classify_text_runs(text: str) -> List[Tuple[RunClass, str]]:
    """Segment line into directional runs ensuring numericals are LTR/NUMBER runs."""
    if not text:
        return []

    runs: List[Tuple[RunClass, str]] = []
    pattern = re.compile(
        r"(⟦m\d+⟧|⟦=[^⟧]+⟧|"
        r"\b\d+(?:\.\d+)?\b|" # Standalone numbers / numericals
        r"\b\d+[a-zA-Z]+\b|"  # e.g., 2y, 10x
        r"\b[a-zA-Z]\b|"     # e.g., x, y
        r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+|\S+)"
    )

    for m in pattern.finditer(text):
        tok = m.group(0)
        if tok.startswith("⟦m") or tok.startswith("⟦="):
            runs.append((RunClass.MATH, tok))
        elif tok.isdigit() or re.match(r"^\d+(?:\.\d+)?$", tok):
            runs.append((RunClass.NUMBER, tok))
        elif _ARABIC_CHAR_RE.search(tok):
            runs.append((RunClass.RTL_TEXT, tok))
        elif re.search(r"^[a-zA-Z0-9=<>\+\-\*/×÷≤≥≠]+$", tok):
            runs.append((RunClass.MATH, tok))
        else:
            runs.append((RunClass.SYMBOL, tok))

    return runs


# --------------------------------------------------------------------------
# Semantic Validation & Hard Failure Checks
# --------------------------------------------------------------------------

def validate_math_semantics(src: str, target: str) -> Tuple[bool, str]:
    """Hard failure detector for numerical or mathematical reversal."""
    # 1. Term reversal check (e.g. 2y -> y2, 10x -> x01)
    for m in re.finditer(r"(\d+)([a-zA-Z]+)", src):
        num, var = m.group(1), m.group(2)
        reversed_term = f"{var}{num[::-1]}"
        if reversed_term in target:
            return False, f"Hard failure: term '{num}{var}' reversed to '{reversed_term}'"

    # 2. Digit / Numerical sequence reversal check (e.g. 150 -> 051)
    for m in re.finditer(r"\b\d{2,}\b", src):
        num = m.group(0)
        reversed_num = num[::-1]
        if reversed_num in target and num not in target:
            return False, f"Hard failure: numerical '{num}' reversed to '{reversed_num}'"

    # 3. Exponent reversal check (e.g. x² -> ²x)
    for m in re.finditer(r"([a-zA-Z])([²³⁴⁵⁶⁷⁸⁹⁰])", src):
        var, exp = m.group(1), m.group(2)
        reversed_exp = f"{exp}{var}"
        if reversed_exp in target:
            return False, f"Hard failure: power '{var}{exp}' reversed to '{reversed_exp}'"

    # 4. Subscript reversal check (e.g. x₁ -> ₁x)
    for m in re.finditer(r"([a-zA-Z])([₁₂₃₄₅₆₇₈₉₀])", src):
        var, sub = m.group(1), m.group(2)
        reversed_sub = f"{sub}{var}"
        if reversed_sub in target:
            return False, f"Hard failure: subscript '{var}{sub}' reversed to '{reversed_sub}'"

    return True, "Valid math and numerical semantics"
