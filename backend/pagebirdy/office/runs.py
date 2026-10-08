"""Paired run tags: mid-paragraph formatting through one engine call.

A paragraph is a sequence of runs, each with its own formatting. Sending runs
one at a time breaks sentences into fragments; sending the paragraph as plain
text loses the bold word. Instead, adjacent runs with the same formatting merge
into spans, the style holding most characters is the paragraph's base and stays
untagged, and every other span is wrapped `⟦rN⟧…⟦/rN⟧`. What is not text (a
tab, a field, a drawing) becomes an opaque `⟦xN⟧`; a line break is the shared
`⟦br⟧`. `tag_problem` checks all of these, so a dropped tag keeps the
paragraph's source text on rebuild; `decode` also rejects orderings a multiset cannot see
(closed before opened, nested, an object twice).
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

# Appended to the engine prompt (`build_engines(extra_rules=…)`) only for a
# document that contains these tokens.
TAG_RULES = (
    "\nOFFICE DOCUMENT MARKUP. Two more kinds of token may appear and ALL must "
    "survive verbatim (same token, same count):\n"
    "   - ⟦r1⟧…⟦/r1⟧, ⟦r2⟧…⟦/r2⟧ … : the enclosed words carry special formatting "
    "(bold, a link, a colour). Keep every pair, put it around the translated words "
    "that carry the same meaning, never nest pairs, never drop one.\n"
    "   - ⟦x0⟧, ⟦x1⟧ … : an object inside the sentence (a tab, a field, a picture). "
    "Keep each exactly once, where the target sentence needs it.\n"
)

_TOKEN = re.compile(r"⟦(/?)r(\d+)⟧|⟦x(\d+)⟧|⟦br⟧")


@dataclass
class Piece:
    kind: str                 # "text" | "object" | "break"
    text: str = ""
    key: str = ""             # formatting signature; equal keys share a style
    handle: object = None     # adapter-owned (an lxml element, a tuple…)


@dataclass
class Layout:
    base: int = -1                                       # span left untagged
    spans: list[list[Piece]] = field(default_factory=list)
    tags: dict[int, int] = field(default_factory=dict)   # tag number -> span index
    objects: list[Piece] = field(default_factory=list)
    breaks: list[Piece] = field(default_factory=list)


@dataclass
class Out:
    kind: str                 # "text" | "object" | "break"
    span: int = -1
    text: str = ""
    piece: Piece | None = None


def encode(pieces: list[Piece]) -> tuple[str, Layout]:
    lay = Layout()
    keys: list[str] = []
    seq: list[tuple[str, int]] = []
    for p in pieces:
        if p.kind == "text":
            if not p.text:
                continue
            if seq and seq[-1][0] == "span" and keys[seq[-1][1]] == p.key:
                lay.spans[seq[-1][1]].append(p)
            else:
                lay.spans.append([p])
                keys.append(p.key)
                seq.append(("span", len(lay.spans) - 1))
        elif p.kind == "object":
            lay.objects.append(p)
            seq.append(("obj", len(lay.objects) - 1))
        else:
            lay.breaks.append(p)
            seq.append(("br", len(lay.breaks) - 1))

    weight: Counter = Counter()
    for k, s in zip(keys, lay.spans):
        weight[k] += sum(len(p.text) for p in s)
    # Ties go to the style that appears first.
    base_key = max(weight, key=lambda k: (weight[k], -keys.index(k))) if weight else None

    out: list[str] = []
    n = 0
    for kind, i in seq:
        if kind == "span":
            text = "".join(p.text for p in lay.spans[i])
            if keys[i] == base_key:
                if lay.base < 0:
                    lay.base = i
                out.append(text)
            else:
                n += 1
                lay.tags[n] = i
                out.append(f"⟦r{n}⟧{text}⟦/r{n}⟧")
        elif kind == "obj":
            out.append(f"⟦x{i}⟧")
        else:
            out.append("⟦br⟧")
    return "".join(out), lay


def _pairs(text: str) -> tuple[dict[int, list[str]], str | None]:
    """What each `⟦rN⟧` pair wraps, in order of appearance — or, when the tags
    are malformed in a way `decode` would refuse, why."""
    inner: dict[int, list[str]] = {}
    open_tag: int | None = None
    pos = 0
    for m in _TOKEN.finditer(text):
        close, rnum = m.group(1), m.group(2)
        if rnum is None:
            continue  # ⟦xN⟧ and ⟦br⟧ are not words a pair can wrap
        n = int(rnum)
        if close:
            if open_tag != n:
                return inner, f"⟦/r{n}⟧ closes a pair that is not open"
            words = _TOKEN.sub("", text[pos:m.start()])
            inner.setdefault(n, []).append(words)
            open_tag = None
        else:
            if open_tag is not None:
                return inner, f"⟦r{n}⟧ opens inside ⟦r{open_tag}⟧; pairs must not nest"
            open_tag = n
            pos = m.end()
    if open_tag is not None:
        return inner, f"⟦r{open_tag}⟧ is never closed"
    return inner, None


def tag_problem(source: str, target: str) -> str | None:
    """Why `target`'s formatting tags cannot be written back, or None.

    String-only, so it reaches places that hold no `Layout` (the translator,
    the review store). Catches what a plain token count cannot:
    a pair closed before it opens, nested, or kept but emptied
    ("⟦r1⟧⟦/r1⟧" — its words moved outside), which the website rebuild
    rejects (`web/html.py`) by keeping the English. The reason names the
    English words the pair wraps, so it reads as an instruction both to an
    engine asked again and to a reviewer."""
    want, _ = _pairs(source)
    got, why = _pairs(target)
    if why:
        return why
    for n in got:
        if n not in want:
            return f"⟦r{n}⟧ is not in the source"
    for n, words in got.items():
        wrapped = [w for w in want.get(n, []) if w.strip()]
        if wrapped and not all(w.strip() for w in words):
            return (f"⟦r{n}⟧…⟦/r{n}⟧ is empty — it should wrap the translation of "
                    f"\"{wrapped[0].strip()}\"")
    return None


_RUN_TAG = re.compile(r"⟦/?r\d+⟧")


def pair_words(source: str) -> dict[int, str]:
    """The English words each `⟦rN⟧` pair wraps (first occurrence), for pairs
    that wrap any."""
    inner, _ = _pairs(source)
    return {n: w[0].strip() for n, w in inner.items() if w and w[0].strip()}


def untagged(text: str) -> str:
    """`text` with every `⟦rN⟧`/`⟦/rN⟧` removed and the spacing they leave
    behind closed up."""
    return re.sub(r"[ \t]{2,}", " ", _RUN_TAG.sub("", text)).strip()


def unplaced(source: str, plain: str) -> str:
    """A translation whose styled words could not be found, in the shape the
    website rebuild writes unstyled: every pair present and empty, after the
    text — so the token count still matches and the review screen still shows
    the pair as something a person has to place."""
    order = [int(m.group(1)) for m in re.finditer(r"⟦r(\d+)⟧", source)]
    return plain + "".join(f"⟦r{n}⟧⟦/r{n}⟧" for n in order)


# Arabic-script clitics an engine attaches to a word in a sentence but not to
# the same word on its own ("التنبؤ" in the sentence, "تنبؤ" asked alone).
_CLITICS = ("وال", "بال", "فال", "كال", "لل", "ال", "و", "ب", "ف", "ل", "ك")
_DIACRITICS = re.compile(r"[ً-ْٰـ]")


_ALEF = {"أ": "ا", "إ": "ا", "آ": "ا"}


def _fold_char(c: str) -> str:
    """One character in, exactly one out, so folded offsets stay offsets."""
    return _ALEF.get(c) or (c.lower()[:1] or c)


def _fold(s: str) -> str:
    return "".join(_fold_char(c) for c in _DIACRITICS.sub("", s))


def _folded(plain: str) -> tuple[str, list[int]]:
    """`plain` folded, with each folded character's index in `plain`."""
    keep = [i for i, c in enumerate(plain) if not _DIACRITICS.match(c)]
    return "".join(_fold_char(plain[i]) for i in keep), keep


def _in_word(c: str) -> bool:
    """A letter or digit, or a mark written on one (Arabic short vowels)."""
    return c.isalnum() or unicodedata.category(c) == "Mn"


def _find(plain: str, phrase: str, char_wrapped: bool) -> tuple[int, int] | None:
    """Where `phrase` sits in `plain`, widened to whole words, or None.

    Compared after folding (diacritics, alef forms, case), each character of
    the folded text mapping one-to-one onto the original, so the span found is
    a span of `plain`. A space-wrapped script also tries the phrase with a
    leading clitic dropped, and widens the match to the words it touches; a
    char-wrapped one (zh, ja) has no word edges to widen to."""
    folded, keep = _folded(plain)
    want = _fold(phrase.strip())
    if not want:
        return None
    tries = [want]
    if not char_wrapped:
        tries += [want[len(c):] for c in _CLITICS
                  if want.startswith(c) and len(want) - len(c) >= 2]
    for w in tries:
        at = folded.find(w)
        if at < 0:
            continue
        start, end = keep[at], keep[at + len(w) - 1] + 1
        if not char_wrapped:
            # Only a match that cuts a word in two ("أتمتة" inside "الأتمتة")
            # grows to the whole word; one that already stops at punctuation
            # (".AI" in "Element.AI") is the words it names.
            while start > 0 and _in_word(plain[start - 1]) and _in_word(plain[start]):
                start -= 1
            while end < len(plain) and _in_word(plain[end]) and _in_word(plain[end - 1]):
                end += 1
        return start, end
    return None


def verbatim(plain: str, words: str) -> str | None:
    """`words` when they stand in `plain` exactly as the English has them — a
    brand, an acronym, a number, a word both languages spell alike ("CAM",
    "Bot", ".AI", "⟦=720⟧", "digital") — matched as whole words, ignoring case.
    No model is asked: the text itself is the evidence."""
    words = words.strip()
    if len(words) < 2:
        return None
    lead = r"(?<!\w)" if words[0].isalnum() else ""
    tail = r"(?!\w)" if words[-1].isalnum() else ""
    m = re.search(lead + re.escape(words) + tail, plain, re.IGNORECASE)
    return m.group(0) if m else None


# English words that carry no meaning of their own in a styled phrase.
_FUNCTION_WORDS = frozenset({"a", "an", "the", "of", "and", "or", "for", "to", "in", "on",
                             "at", "by", "with", "from", "&", "+", "-", "/"})


def _content_words(text: str) -> list[str]:
    return [t for t in re.findall(r"[\w.]+", text.lower()) if t.strip(".") not in _FUNCTION_WORDS]


def _same_word(a: str, b: str) -> bool:
    """Two English words for one meaning: equal, or one an inflection of the
    other ("forecast"/"forecasting", "invoice"/"invoices"). Deliberately
    crude: both sides are English, and a near miss only costs the styling."""
    a, b = a.strip("."), b.strip(".")
    if not a or not b:
        return False
    if a == b:
        return True
    n = min(len(a), len(b))
    return n >= 4 and (a.startswith(b[:max(4, len(b) - 3)]) or b.startswith(a[:max(4, len(a) - 3)]))


def gloss_span(plain: str, gloss: list[tuple[str, str]], english: str) -> str | None:
    """The run of `plain` whose glossed meanings are the styled `english`
    words, or None.

    `gloss` is the translation's words in order, each with its English
    meaning in the sentence ("Pronóstico" → "forecast", "de" → "of",
    "demanda" → "demand"). The words whose meaning (or own spelling) matches a
    content word of `english` are found, and the span runs from the first to
    the last of them, so "puntuación de leads" stays whole for "Lead Score".
    Nothing here asks a model which words are styled: asked that, a model
    answers by position ("Demand Forecasting" → the first word, "Pronóstico")
    about one time in four."""
    want = _content_words(re.sub(r"⟦=([^⟧]*)⟧", r"\1", english))
    if not want or not gloss:
        return None
    hits = [i for i, (word, meaning) in enumerate(gloss)
            if any(_same_word(t, u) for t in _content_words(f"{meaning} {word}") for u in want)]
    if not hits:
        return None
    # The glossed words as offsets in `plain`, in order, so the span is a span
    # of the translation itself and not of the model's re-spelling of it.
    folded, keep = _folded(plain)
    pos, offsets = 0, []
    for word, _ in gloss:
        w = _fold(str(word).strip())
        at = folded.find(w, pos) if w else -1
        if at < 0:
            return None
        offsets.append((keep[at], keep[at + len(w) - 1] + 1))
        pos = at + len(w)
    start, end = offsets[min(hits)][0], offsets[max(hits)][1]
    return plain[start:end]


def place_pairs(source: str, plain: str, found: dict[int, str], char_wrapped: bool) -> str | None:
    """Wrap each pair around the words `found` names in `plain` (the target
    without its tags), or None when any cannot be found or two overlap. The
    placement is done here, not by a model: the model only says which of its
    own words render the styled English."""
    spans: list[tuple[int, int, int]] = []
    whole = (len(plain) - len(plain.lstrip()), len(plain.rstrip()))
    for n, words in pair_words(source).items():
        hit = _find(plain, found.get(n, ""), char_wrapped)
        if hit is None:
            return None
        # An answer that is the whole sentence would style all of it; only a
        # pair that wrapped the whole English may wrap the whole translation.
        if hit[0] <= whole[0] and hit[1] >= whole[1] and words != untagged(source):
            return None
        spans.append((hit[0], hit[1], n))
    spans.sort()
    if any(a[1] > b[0] for a, b in zip(spans, spans[1:])):
        return None
    out, pos = [], 0
    for start, end, n in spans:
        out += [plain[pos:start], f"⟦r{n}⟧", plain[start:end], f"⟦/r{n}⟧"]
        pos = end
    out.append(plain[pos:])
    return "".join(out)


def decode(target: str, layout: Layout) -> list[Out] | None:
    """The target as an ordered list of text (with the span whose style it
    takes), objects and breaks — or None when the tags are malformed."""
    out: list[Out] = []
    open_tag: int | None = None
    seen_objects: set[int] = set()
    pos = 0

    def text(chunk: str) -> None:
        if chunk:
            span = layout.tags[open_tag] if open_tag is not None else layout.base
            out.append(Out("text", span=span, text=chunk))

    for m in _TOKEN.finditer(target):
        text(target[pos:m.start()])
        pos = m.end()
        close, rnum, xnum = m.group(1), m.group(2), m.group(3)
        if rnum is not None:
            n = int(rnum)
            if n not in layout.tags:
                return None
            if close:
                if open_tag != n:
                    return None
                open_tag = None
            else:
                if open_tag is not None:
                    return None
                open_tag = n
        elif xnum is not None:
            k = int(xnum)
            if k >= len(layout.objects) or k in seen_objects:
                return None
            seen_objects.add(k)
            out.append(Out("object", piece=layout.objects[k]))
        else:
            out.append(Out("break"))
    text(target[pos:])
    if open_tag is not None:
        return None
    if any(o.kind == "text" and o.span < 0 for o in out):
        return None  # untagged text with no base style to give it
    return out
