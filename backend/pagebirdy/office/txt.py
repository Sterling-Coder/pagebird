"""Plain text: one segment per non-blank line.

Everything that is not words survives byte for byte: the newline style (per
line, so a mixed file stays mixed), blank lines, indentation, trailing
whitespace, and whether the file ends with a newline. Input may be UTF-8,
UTF-16 (with BOM) or cp1252; output is always UTF-8, with a BOM iff the source
had one.
"""

from __future__ import annotations

import codecs
import re

from pagebirdy.office.adapter import Issue, blank_segment, writable
from pagebirdy.office.formats import MB, Format, UnsupportedFile
from pagebirdy.office.protect import restore

_LINE = re.compile(r"([^\r\n]*)(\r\n|\n|\r|$)")


def _decode(raw: bytes) -> tuple[str, bool]:
    if raw.startswith(codecs.BOM_UTF8):
        return raw[3:].decode("utf-8"), True
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return raw.decode("utf-16"), True
    if b"\x00" in raw:
        raise UnsupportedFile("This file isn't plain text. Please upload a .txt file.")
    try:
        return raw.decode("utf-8"), False
    except UnicodeDecodeError:
        return raw.decode("cp1252"), False


def _lines(text: str) -> list[tuple[str, str]]:
    """(content, newline) pairs; the last pair's newline may be ''."""
    out = []
    for m in _LINE.finditer(text):
        if m.start() == len(text):
            break
        out.append((m.group(1), m.group(2)))
    return out


def _read(path: str) -> tuple[list[tuple[str, str]], bool]:
    with open(path, "rb") as f:
        text, bom = _decode(f.read())
    return _lines(text), bom


def _core(line: str) -> tuple[str, str, str]:
    """(leading whitespace, words, trailing whitespace)."""
    core = line.strip()
    if not core:
        return line, "", ""
    lead = line[: len(line) - len(line.lstrip())]
    trail = line[len(line.rstrip()):]
    return lead, core, trail


class TxtAdapter:
    def sniff(self, path: str) -> None:
        try:
            _read(path)
        except UnicodeDecodeError:
            raise UnsupportedFile("This text file's encoding isn't recognised. "
                                  "Save it as UTF-8 and try again.")

    def extract(self, src: str):
        lines, _ = _read(src)
        return [blank_segment(f"txt:L{i}", _core(content)[1])
                for i, (content, _) in enumerate(lines) if content.strip()]

    def rebuild(self, src, segments, out, lang):
        lines, bom = _read(src)
        by_id = {s.id: s for s in segments}
        parts = []
        for i, (content, nl) in enumerate(lines):
            seg = by_id.get(f"txt:L{i}")
            if writable(seg):
                lead, _, trail = _core(content)
                # A line holds one line: an engine newline would add one.
                text = re.sub(r"[\r\n  ]+", " ", restore(seg.target, seg.placeholders))
                content = lead + text + trail
            parts.append(content + nl)
        with open(out, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
            f.write("".join(parts))
        return []

    def validate(self, src, out):
        try:
            a, _ = _read(src)
            b, _ = _read(out)
        except (UnicodeDecodeError, UnsupportedFile) as e:
            return [Issue("error", "unreadable", "output", str(e))]
        if len(a) != len(b):
            return [Issue("error", "structure", "file",
                          f"{len(a)} lines in source, {len(b)} in output")]
        for i, (x, y) in enumerate(zip(a, b)):
            if (not x[0].strip()) != (not y[0].strip()) or x[1] != y[1]:
                return [Issue("error", "structure", f"line {i + 1}",
                              "blank lines or line endings moved")]
        return []

    def units(self, src):
        return {"lines": len(_read(src)[0])}


ADAPTER = TxtAdapter()
FORMAT = Format(".txt", "txt", "TXT", "text/plain", 10 * MB, None, "pagebirdy.office.txt")
