"""IDML read/translate/write.

IDML is a ZIP of XML. Translatable text lives in `Stories/*.xml` inside
`<Content>` nodes, grouped by `<CharacterStyleRange>` (a styled run) inside
`<ParagraphStyleRange>`. We translate at the run level: each `<Content>` becomes
one Segment, so all inline styling (bold terms, etc.) is preserved exactly and
InDesign re-flows the layout on open — the whole reason IDML is the high-fidelity
path and the source of the eventual INDD output.

Math safety carries over from the PDF path:
  * A run whose applied font is a math face becomes an opaque `⟦m0⟧` placeholder
    and is left untouched on writeback.
  * Numeric tokens inside prose runs use the value-visible `⟦=…⟧` form.
  * A forced line break (U+2028/U+2029) — IDML's soft-return, common mid-run —
    becomes a fixed `⟦br⟧` token; sent raw, at least one LLM corrupts it into
    unrelated control bytes, which then fails the XML writer on save.

Reuses the same Allocator, token regex, Segment, Translator, integrity gate, and
glossary as the PDF path — one translation core, two document formats.
"""

from __future__ import annotations

import re
import zipfile

from lxml import etree

from babel.models import Segment
from babel.protect.mathguard import _TOKEN_RE, Allocator

_MATH_FONT_KEYS = ("math", "pi lt", "pilt", "mathematicalpi")
# InDesign's forced line/paragraph break, embedded mid-run in Content text.
# Sent raw to an LLM, at least one model reliably corrupts it into unrelated
# control bytes in its JSON reply, which then fails the XML writer on save
# ("All strings must be XML compatible") — so it is protected like math/value
# tokens instead (see Allocator.take_break).
_BREAK_RE = re.compile("[\u2028\u2029]")


def _localname(el) -> str:
    if not isinstance(el.tag, str):  # comments / PIs
        return ""
    return etree.QName(el).localname


def is_math_font(name: str) -> bool:
    n = (name or "").lower()
    return any(k in n for k in _MATH_FONT_KEYS)


class IdmlPackage:
    def __init__(self, path: str):
        self.path = path
        self._names: list[str] = []
        self._entries: dict[str, bytes] = {}
        self._stories: dict[str, etree._Element] = {}
        self._node_index: dict[str, etree._Element] = {}

        with zipfile.ZipFile(path) as z:
            self._names = z.namelist()
            for n in self._names:
                data = z.read(n)
                self._entries[n] = data
                if n.startswith("Stories/") and n.endswith(".xml"):
                    self._stories[n] = etree.fromstring(data)

    # ---- extract -------------------------------------------------------------

    def segments(self) -> list[Segment]:
        segs: list[Segment] = []
        counter = 0
        for name, tree in self._stories.items():
            short = name.split("/")[-1].rsplit(".", 1)[0]
            for content in _iter_content(tree):
                text = content.text or ""
                if not text.strip():
                    continue
                font = _font_of(content)
                alloc = Allocator()
                if is_math_font(font):
                    source = alloc.take_math(text)
                else:
                    text = _BREAK_RE.sub(lambda m: alloc.take_break(m.group(0)), text)
                    source = _TOKEN_RE.sub(lambda m: alloc.take_value(m.group(0)), text)
                sid = f"{short}-c{counter}"
                counter += 1
                seg = Segment(
                    id=sid, page=0, bbox=(0, 0, 0, 0), font=font, size=0, color=0,
                    source=source, placeholders=alloc.map,
                    has_math_font=alloc.has_math_font,
                )
                self._node_index[sid] = content
                segs.append(seg)
        return segs

    # ---- linked graphics (SAY/GO!-style .ai word-art, see idml.graphics) -----

    def raw_entries(self) -> dict[str, bytes]:
        """Every zip entry as raw bytes, INCLUDING Stories — a placed
        graphic's `<Link>` lives in Spreads/MasterSpreads, but an
        inline/anchored graphic (e.g. a "SAY" callout set mid-sentence) is
        part of the paragraph flow, so its `<Link>` lives inside its own
        story instead. Used only for scanning (`find_linked_graphics`); the
        Story bytes here are never the save-time source of truth for Content
        text (the parsed tree is), so mutating them here would be silently
        discarded — see `relink`."""
        return self._entries

    def relink(self, mapping: dict[str, str]) -> int:
        """Repoint LinkResourceURI occurrences to translated graphics. See
        `babel.idml.graphics.translate_linked_graphics` for building `mapping`.

        Split two ways because `save()` treats the two kinds of entry
        differently: Spreads/MasterSpreads are written back from raw bytes
        (patched in place), but Story entries are always re-serialized from
        `self._stories`'s parsed tree — so an inline/anchored graphic's link,
        which lives inside a story, must be relinked on that tree directly or
        the edit is silently lost at save time."""
        from babel.idml.graphics import relink as _relink_bytes, relink_story_tree
        count = _relink_bytes(self._entries, mapping)
        for tree in self._stories.values():
            count += relink_story_tree(tree, mapping)
        return count

    # ---- write back ----------------------------------------------------------

    def apply(self, segments: list[Segment], idml_font: str | None = None) -> int:
        """Write translated text back into Content nodes. Math-font runs are left
        untouched. When idml_font is given, every rewritten run's AppliedFont is
        overridden to it (FontStyle/PointSize/FillColor are untouched) — the
        original font's script rarely covers a non-Latin target language."""
        applied = 0
        for s in segments:
            if s.has_math_font or s.target is None:
                continue
            if s.status not in ("translated", "tm_hit", "approved", "edited"):
                continue
            node = self._node_index.get(s.id)
            if node is not None:
                node.text = s.restored_target()
                if idml_font:
                    _set_applied_font(node, idml_font)
                applied += 1
        return applied

    def save(self, out_path: str) -> None:
        import os

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
            # IDML (like EPUB/ODF) requires an uncompressed `mimetype` entry first.
            if "mimetype" in self._entries:
                zi = zipfile.ZipInfo("mimetype")
                zi.compress_type = zipfile.ZIP_STORED
                z.writestr(zi, self._entries["mimetype"])
            for n in self._names:
                if n == "mimetype":
                    continue
                if n in self._stories:
                    data = etree.tostring(
                        self._stories[n], xml_declaration=True, encoding="UTF-8",
                        standalone=True,
                    )
                else:
                    data = self._entries[n]
                z.writestr(n, data)


def _iter_content(tree):
    for el in tree.iter():
        if _localname(el) == "Content":
            yield el


def _font_of(content) -> str:
    p = content.getparent()
    while p is not None:
        if _localname(p) == "CharacterStyleRange":
            for props in p:
                if _localname(props) == "Properties":
                    for af in props:
                        if _localname(af) == "AppliedFont":
                            return af.text or ""
            break
        p = p.getparent()
    return ""


def _set_applied_font(content, font_name: str) -> None:
    """Override the AppliedFont on this run's CharacterStyleRange, creating
    Properties/AppliedFont if the run didn't already declare one inline."""
    p = content.getparent()
    while p is not None and _localname(p) != "CharacterStyleRange":
        p = p.getparent()
    if p is None:
        return

    props = None
    for child in p:
        if _localname(child) == "Properties":
            props = child
            break
    if props is None:
        props = etree.SubElement(p, "Properties")
        p.insert(0, props)  # Properties must precede Content-bearing children

    applied_font = None
    for child in props:
        if _localname(child) == "AppliedFont":
            applied_font = child
            break
    if applied_font is None:
        applied_font = etree.SubElement(props, "AppliedFont")
        applied_font.set("type", "string")

    applied_font.text = font_name
