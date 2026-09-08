"""Reconstruct LaTeX from the PDF's own layout — no OCR, no model, no key.

Image recognisers guess at pixels and get digits wrong (`7^5` read as
`\\gamma^5`). But this information was never lost: the PDF still carries it,
just encoded awkwardly.

    * A superscript is a separate span with a smaller size and a raised
      baseline. `6⁴` arrives as span "6" (12pt) + span "4" (8.4pt, raised).
    * A fraction bar is a run of `·` glyphs in MathematicalPiLTStd-3; whatever
      sits above it is the numerator, below it the denominator.
    * Operators are math-font glyphs whose *character code* is unrelated to
      what they draw: MathematicalPiLTStd-1 "2" paints a minus sign, "5" an
      equals, "3" a multiplication cross. Naive text extraction therefore
      turns (−5⁵)² into "(255)2" — which is where the corruption comes from.

Decode those three rules and the equation reconstructs exactly, because it is
being read rather than recognised. The glyph table below was derived from the
sample packets (see the docstring table in the commit) and is specific to this
font family; documents using other math fonts fall back to the image
recogniser in `equations.py`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from babel.models import Line, Span

# --- glyph tables ---------------------------------------------------------
# char code -> what the glyph actually draws
_PI1 = {
    "1": "+",
    "2": "-",
    "3": r"\times",
    "4": r"\div",
    "5": "=",
    "6": r"\pm",
    "8": r"\leq",
    "9": r"\geq",
}
# MathematicalPiLTStd-3 carries oversized delimiters and the fraction rule
_PI3 = {
    "1": "(",
    "2": ")",
    "3": "[",
    "4": "]",
}

_BAR_CHARS = set("·.")
_SUPER_RATIO = 0.88      # a span this much smaller than the line is a script
_BASELINE_EPS = 0.12     # fraction of body size a baseline must shift to count


def _font_key(font: str) -> str:
    name = (font or "").lower().replace(" ", "")
    if "mathematicalpiltstd-3" in name:
        return "pi3"
    if "mathematicalpiltstd" in name:
        return "pi1"
    return ""


def is_fraction_bar(span: Span) -> bool:
    text = span.text.strip()
    return (
        bool(text)
        and _font_key(span.font) == "pi3"
        and all(c in _BAR_CHARS for c in text)
    )


# Typographic characters that stand in for operators in the body font.
_BODY_SYMBOLS = {"•": r"\cdot", "×": r"\times", "÷": r"\div", "−": "-", "–": "-"}


def glyph_text(span: Span) -> str:
    """The characters this span really draws."""
    key = _font_key(span.font)
    if key == "pi1":
        return "".join(_PI1.get(c, c) for c in span.text)
    if key == "pi3":
        return "".join(_PI3.get(c, c) for c in span.text)
    return "".join(_BODY_SYMBOLS.get(c, c) for c in span.text)


@dataclass
class _Tok:
    span: Span
    text: str

    @property
    def x0(self) -> float:
        return self.span.bbox[0]

    @property
    def x1(self) -> float:
        return self.span.bbox[2]

    @property
    def top(self) -> float:
        return self.span.bbox[1]

    @property
    def bottom(self) -> float:
        return self.span.bbox[3]

    @property
    def cy(self) -> float:
        return (self.span.bbox[1] + self.span.bbox[3]) / 2.0

    @property
    def size(self) -> float:
        return self.span.size


def _escape(text: str) -> str:
    """LaTeX-escape literal text, leaving already-emitted commands alone."""
    if text.startswith("\\"):
        return text
    out = []
    for ch in text:
        if ch in "%$#&_{}":
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def _body_size(toks: list[_Tok]) -> float:
    """Nominal body size for the region.

    Oversized delimiters (the ( and ) that wrap a stacked fraction are set in a
    much larger point size) must not define the body, or every ordinary digit
    looks small and gets lifted into a superscript.
    """
    ordinary = [
        t.size for t in toks
        if not is_fraction_bar(t.span) and _font_key(t.span.font) != "pi3"
    ]
    return max(ordinary) if ordinary else max((t.size for t in toks), default=10.0)


def _classify(toks: list[_Tok]) -> dict[int, str]:
    """Render every token once, with the whole region as context.

    Script detection needs neighbours: a lone "x" tells you nothing, but an "x"
    that is smaller than the body and sits above the baseline of the token to
    its left is an exponent. Classifying globally also keeps a token's rendering
    stable no matter which fraction part later claims it.
    """
    body = _body_size(toks)
    full = [t for t in toks
            if t.size >= body * _SUPER_RATIO and _font_key(t.span.font) != "pi3"]

    out: dict[int, str] = {}
    for tok in toks:
        text = tok.text
        if not text.strip():
            out[id(tok)] = " "
            continue
        if tok.size >= body * _SUPER_RATIO or _font_key(tok.span.font) == "pi3":
            out[id(tok)] = _escape(text)
            continue

        # Compare against the nearest full-size glyph on the same visual row.
        # The band must stay under the numerator-to-denominator distance, or a
        # denominator's exponent is measured against the numerator's baseline
        # and comes out as a subscript.
        row = [f for f in full if abs(f.cy - tok.cy) < body * 0.9] or full
        neighbour = min(row, key=lambda f: abs(f.x0 - tok.x0), default=None)
        base_bottom = neighbour.bottom if neighbour else tok.bottom
        shift = base_bottom - tok.bottom

        if shift > body * _BASELINE_EPS:
            out[id(tok)] = "^{" + _escape(text.strip()) + "}"
        elif shift < -body * _BASELINE_EPS:
            out[id(tok)] = "_{" + _escape(text.strip()) + "}"
        else:
            out[id(tok)] = _escape(text)
    return out


def _render_row(toks: list[_Tok], rendered: dict[int, str]) -> str:
    """Emit tokens left to right using the pre-computed classification."""
    if not toks:
        return ""
    parts = [rendered.get(id(t), _escape(t.text)) for t in sorted(toks, key=lambda t: t.x0)]
    return _merge_scripts("".join(parts))


def _merge_scripts(latex: str) -> str:
    """`^{1}^{0}` came from two glyphs of one exponent — make it `^{10}`."""
    prev = None
    while prev != latex:
        prev = latex
        latex = re.sub(r"\^\{([^{}]*)\}\^\{([^{}]*)\}", r"^{\1\2}", latex)
        latex = re.sub(r"_\{([^{}]*)\}_\{([^{}]*)\}", r"_{\1\2}", latex)
    return latex


def _tokens(lines: list[Line]) -> list[_Tok]:
    from babel.protect.equations import is_badge_span

    toks: list[_Tok] = []
    for line in lines:
        for span in line.spans:
            if not span.text.strip() or is_badge_span(span):
                continue
            toks.append(_Tok(span=span, text=glyph_text(span)))
    return toks


def build_latex(lines: list[Line]) -> str | None:
    """LaTeX for one equation region, or None if nothing usable was found.

    Fractions are resolved first — each bar claims the tokens directly above
    and below it — then whatever remains is laid out left to right.
    """
    toks = _tokens(lines)
    if not toks:
        return None

    rendered = _classify(toks)
    bars = [t for t in toks if is_fraction_bar(t.span)]
    rest = [t for t in toks if t not in bars]

    pieces: list[tuple[float, str]] = []
    claimed: set[int] = set()

    for bar in bars:
        # a token belongs to this bar when it sits within the bar's span
        span_x0, span_x1 = bar.x0 - 2.0, bar.x1 + 2.0
        members: list[tuple[int, _Tok]] = [
            (i, tok) for i, tok in enumerate(rest)
            if i not in claimed and tok.x1 >= span_x0 and tok.x0 <= span_x1
            # oversized delimiters wrap the whole fraction, so they belong
            # outside it, not in the numerator that happens to sit beside them
            and _font_key(tok.span.font) != "pi3"
        ]
        above: list[_Tok] = []
        below: list[_Tok] = []
        if len(members) >= 2:
            # The bar glyph's box is much taller than the rule it draws, so its
            # centre is not the divide — a denominator's exponent can sit above
            # it. Split on the widest vertical gap between tokens instead; the
            # numerator/denominator gap always dominates within one fraction.
            members.sort(key=lambda m: m[1].cy)
            gaps = [
                (members[k + 1][1].cy - members[k][1].cy, k)
                for k in range(len(members) - 1)
            ]
            _, cut = max(gaps)
            for idx, (i, tok) in enumerate(members):
                (above if idx <= cut else below).append(tok)
                claimed.add(i)
        else:
            for i, tok in members:
                (above if tok.cy < bar.cy else below).append(tok)
                claimed.add(i)
        num = _render_row(above, rendered).strip()
        den = _render_row(below, rendered).strip()
        if num and den:
            pieces.append((bar.x0, r"\frac{" + num + "}{" + den + "}"))
        elif num or den:
            # Only one side present: the "bar" is a stray rule or the region was
            # clipped. Emitting \frac{x}{?} would be worse than the bare term.
            pieces.append((bar.x0, num or den))

    leftovers = [t for i, t in enumerate(rest) if i not in claimed]
    if leftovers and not pieces:
        return _clean(_render_row(leftovers, rendered))

    # interleave the fractions with the runs either side of them, by x. Adjacent
    # leftovers are emitted as one run so their scripts stay merged.
    for run in _contiguous_runs(leftovers):
        pieces.append((run[0].x0, _render_row(run, rendered)))
    pieces.sort(key=lambda p: p[0])
    return _clean("".join(text for _, text in pieces))


def _contiguous_runs(toks: list[_Tok], gap: float = 6.0) -> list[list[_Tok]]:
    """Split leftovers into horizontal runs so scripts merge within a run."""
    if not toks:
        return []
    ordered = sorted(toks, key=lambda t: t.x0)
    runs: list[list[_Tok]] = [[ordered[0]]]
    for tok in ordered[1:]:
        if tok.x0 - runs[-1][-1].x1 > gap:
            runs.append([tok])
        else:
            runs[-1].append(tok)
    return runs


def _clean(latex: str) -> str:
    latex = re.sub(r"\s+", " ", latex).strip()
    latex = _merge_scripts(latex)
    # Oversized delimiters wrap a stacked fraction, so they must scale with it.
    # Only pair them when the counts match, or \left is left without its \right
    # and the expression will not compile.
    if latex.count("(") == latex.count(")") and r"\frac" in latex:
        latex = latex.replace("(", r"\left(").replace(")", r"\right)")
    latex = re.sub(r"\\left\(\s+", r"\\left(", latex)
    latex = re.sub(r"\s+\\right\)", r"\\right)", latex)
    return latex.strip()


def latex_confidence(latex: str | None, raw_text: str) -> float:
    """Cheap plausibility score for a reconstruction (0-1)."""
    if not latex:
        return 0.0
    score = 1.0
    if "?" in latex:
        score -= 0.4
    if latex.count("{") != latex.count("}"):
        score -= 0.4
    if not re.search(r"[0-9a-zA-Z]", latex):
        score -= 0.4
    return max(0.0, score)
