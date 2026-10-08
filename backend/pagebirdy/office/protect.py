"""Protection for office text.

Everything the image path protects (emails, URLs, then `mathguard.protect_text`:
never-translate names, sub-part labels, numbers) plus the literals business
documents carry: template placeholders (`{name}`, `{{name}}`, `${amount}`,
`%VALUE%`, `<NAME>`, `[VARIABLE]`), file paths and codes (`SKU-4471`). Each
becomes a value-visible `⟦~…⟧` name, so the shared protection scheme keeps
it and the engine can still read what the sentence is about.

Run tags (`⟦r1⟧`), object tokens (`⟦x0⟧`) and `⟦br⟧` pass through untouched:
every pass runs only on the text between tokens already present.
"""

from __future__ import annotations

import re

from pagebirdy.image.classify import EMAIL_RE, URL_RE
from pagebirdy.models import xml_safe
from pagebirdy.protect.mathguard import Allocator, protect_text

_TOKEN = re.compile(r"(⟦[^⟧]*⟧)")
_STRUCTURE = re.compile(r"⟦(?:/?r\d+|x\d+|br)⟧")

_TEMPLATE = re.compile(
    r"\{\{[^{}\n]{1,64}\}\}"            # {{name}}
    r"|\$\{[^{}\n]{1,64}\}"             # ${amount}
    r"|\{[A-Za-z_][\w.\-]{0,63}\}"      # {customer_name}
    r"|%[A-Za-z_]\w{0,63}%"             # %VALUE%
    r"|<[A-Z_][A-Z0-9_]{0,63}>"         # <NAME>
    r"|\[[A-Z_][A-Z0-9_]{0,63}\]"       # [VARIABLE]
)
# A Windows (C:\…, \\server\…) or POSIX path ending in a file name.
_PATH = re.compile(r"(?:\b[A-Za-z]:\\|\\\\|(?<![\w/])/)(?:[\w.\-]+[\\/])*[\w.\-]+\.\w{1,5}\b")
# Upper-case letters and digits joined by hyphens: SKU-4471, INV-2024-001.
_CODE = re.compile(r"\b(?=[A-Z0-9-]*\d)(?=[A-Z0-9-]*[A-Z])[A-Z0-9]+(?:-[A-Z0-9]+)+\b")
# Punctuation that ends the sentence a URL sits in rather than the URL itself.
_URL_TAIL = re.compile(r"[.,!?;:'\"]+$")


def _url_and_tail(url: str) -> tuple[str, str]:
    """`URL_RE` runs to the next space, so "see https://x.com/help." takes the
    full stop with it, and the engine could never move or replace it. The tail
    is handed back as sentence text; a closing bracket only when the URL does
    not open one itself (a Wikipedia-style "/Foo_(bar)" keeps its own)."""
    tail = ""
    while True:
        m = _URL_TAIL.search(url)
        if m:
            url, tail = url[:m.start()], m.group(0) + tail
        elif url.endswith(")") and url.count("(") < url.count(")"):
            url, tail = url[:-1], ")" + tail
        else:
            return url, tail


def _each_text(text: str, fn) -> str:
    parts = _TOKEN.split(text)
    return "".join(p if i % 2 else fn(p) for i, p in enumerate(parts))


def protect(text: str) -> tuple[str, dict[str, str]]:
    """`text` with every protected literal replaced by a placeholder, and the
    token -> literal map. Deterministic: the same text always yields the same
    tokens, which is what lets a stored review target be replayed later."""
    alloc = Allocator()
    # Email before URL ("shop2.com" inside an address), URL before path (a
    # URL's own "/x.com/a" looks like a path), all before the number scan.
    def url(m: re.Match) -> str:
        found, tail = _url_and_tail(m.group(0))
        return alloc.take_name(found) + tail

    text = _each_text(text, lambda p: EMAIL_RE.sub(lambda m: alloc.take_name(m.group(0)), p))
    text = _each_text(text, lambda p: URL_RE.sub(url, p))
    for pattern in (_TEMPLATE, _PATH, _CODE):
        text = _each_text(text, lambda p, pat=pattern: pat.sub(
            lambda m: alloc.take_name(m.group(0)), p))
    text = _each_text(text, lambda p: protect_text(p, alloc))
    return text, alloc.map


def restore(text: str, placeholders: dict[str, str]) -> str:
    """`Segment.restored_target` for one piece of a paragraph, after the
    caller has already split the run tags off."""
    for token, literal in placeholders.items():
        text = text.replace(token, literal)
    text = re.sub(r"⟦[=~]([^⟧]*)⟧", r"\1", text)
    text = re.sub(r"⟦[^⟧]*⟧", "", text)
    return xml_safe(text)


def visible(text: str) -> str:
    """The words a reader sees: run tags, objects and breaks removed."""
    return _STRUCTURE.sub("", text)
