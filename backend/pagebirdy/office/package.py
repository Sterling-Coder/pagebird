"""Write an OOXML package by changing only the parts that were edited.

Letting python-docx / python-pptx save the whole package re-serialises every
XML part it loaded, so masters, themes, notes, styles and relationships come
back as different bytes even though nothing in them changed. Copying the
source zip entry by entry — same order, same compression, same timestamps —
and replacing just the edited parts keeps everything else byte-identical, and
makes "what did translation touch?" answerable by diffing the two files.
"""

from __future__ import annotations

import zipfile

from lxml import etree


def part_bytes(element) -> bytes:
    """An XML part as Office writes it: declaration, UTF-8, standalone."""
    return etree.tostring(element, xml_declaration=True, encoding="UTF-8", standalone=True)


def write_patched(src: str, out: str, replacements: dict[str, bytes]) -> None:
    """Copy `src` to `out`, swapping in `replacements` (zip member -> bytes)."""
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out, "w") as zout:
        for info in zin.infolist():
            data = replacements.get(info.filename)
            zout.writestr(info, data if data is not None else zin.read(info.filename))


def member(partname) -> str:
    """A package part name (`/ppt/slides/slide1.xml`) as a zip member name."""
    return str(partname).lstrip("/")
