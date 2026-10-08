"""Is a whole unit (a TXT line, a paragraph, a cell) worth an engine call?

A unit that is only a number, a date, a URL, an email, an ID or a code ships as
written, by the same patterns `image.classify` applies to an image region.
Anything with words in it is translated, and its literals are protected
piecewise by `office.protect`.
"""

from __future__ import annotations

import re

from pagebirdy.image.classify import _CODE_TOKEN, _VALUE, EMAIL_RE, URL_RE

_DATE = re.compile(r"^\s*\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?\s*$")
_LETTER = re.compile(r"[^\W\d_]")
_ID = re.compile(r"^[A-Z0-9]+(?:[-_/][A-Z0-9]+)+$")


def should_translate(text: str) -> bool:
    t = text.strip()
    if not t or not _LETTER.search(t):
        return False
    if URL_RE.fullmatch(t) or EMAIL_RE.fullmatch(t):
        return False
    if _VALUE.match(t) or _DATE.match(t) or _ID.match(t):
        return False
    if " " not in t and _CODE_TOKEN.match(t):
        return False
    return True
