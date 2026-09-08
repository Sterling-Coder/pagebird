"""Font resolution for the reassembly stage.

Faces are vendored under `babel/fonts/` so a translated page renders identically
on a developer's Windows box and on a Linux server. System paths stay as a
fallback, but a bundled face always wins — otherwise "it looked fine locally"
means nothing.

The vendored Noto faces are script-specific by design: Noto Sans Hebrew carries
no digits, Noto Naskh Arabic no "." or "/". Since RTL output keeps Western
digits, that would leave `3/4` unsettable in Hebrew — except that MuPDF's
`TextWriter` falls back to another face per missing glyph, so the gap never
reaches the page. Nothing here needs to split runs by coverage; see `_draw_rtl`
in `reassemble/pdf.py`, and the NUL assertion in `tests/test_rtl.py` that guards
the fallback still working.

All bundled faces are SIL Open Font License 1.1; see fonts/OFL.txt.
"""

from __future__ import annotations

import os

_DIR = os.path.join(os.path.dirname(__file__), "fonts")


def bundled(name: str) -> str | None:
    """Absolute path to a vendored face, or None if it isn't bundled."""
    path = os.path.join(_DIR, name)
    return path if os.path.exists(path) else None


def resolve(candidates: list[str] | tuple[str, ...]) -> str | None:
    """First usable face from `candidates`, preferring vendored ones.

    Entries are either a bare filename (looked up in `fonts/`) or an absolute
    system path. Every bundled candidate is considered before any system path,
    so adding a system fallback to a list can never change what a machine that
    has the bundled face renders.
    """
    for name in candidates:
        found = bundled(os.path.basename(name))
        if found:
            return found
    for path in candidates:
        if os.path.isabs(path) and os.path.exists(path):
            return path
    return None
