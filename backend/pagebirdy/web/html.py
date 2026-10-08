"""A web page as `Segment`s, and back — the website adapter.

It fulfils the same contract as an office adapter (`office/adapter.py`), so
protection, the engines, the glossary and the review store are
the shared ones (`office.pipeline.translate_document`).

**What a segment is.** Every maximal run of inline content inside a block —
a paragraph, a list item, a heading, a cell, loose text in a `<div>` — is one
segment, so a sentence reaches the engine whole. Inline elements inside it
(`<a>`, `<b>`, `<span>`…) travel as the office path's paired run tags
`⟦rN⟧…⟦/rN⟧` (`office/runs.py`): the element itself, with every attribute
(`href`, `class`, `style`…), is copied back around the translated words and
never seen by the engine. What sits inline but is not words — an image,
`<code>`, `<kbd>`, a formula, an icon element with no text — is an opaque
`⟦xN⟧` copied back verbatim.

**Never translated:** `<script>`, `<style>`, `<code>`, `<pre>`, `<svg>`,
`<math>`, `<textarea>`, anything marked `translate="no"` or `notranslate`, and
every attribute except the ones a reader sees (`alt`, `title`, `placeholder`,
`aria-label`, a button's `value`, and the page description `<meta>`s).

**The source** is a UTF-8 snapshot of the fetched page (`snapshot`), with the
page's effective `<base href>` written into it, so a rebuild from review rows
never needs the network and resolves every relative URL exactly as the
original did.
"""

from __future__ import annotations

import codecs
import copy
import os
import re
from collections import Counter
from urllib.parse import urljoin

import lxml.html
from lxml import etree

from pagebirdy.languages import Language
from pagebirdy.office.adapter import Issue, blank_segment, reject_tags, writable
from pagebirdy.office.formats import MB, Format
from pagebirdy.office.protect import restore
from pagebirdy.office.runs import Piece, decode, encode
from pagebirdy.web.fetch import FetchError, Page
from pagebirdy.web.sanitize import harden_head, sanitize

# Text-level elements a sentence flows through: their words are translated in
# place, the element is copied back around them.
INLINE = frozenset({
    "a", "abbr", "acronym", "b", "bdi", "bdo", "big", "cite", "data", "del", "dfn", "em",
    "font", "i", "ins", "label", "mark", "nobr", "q", "s", "small", "span", "strike",
    "strong", "sub", "sup", "time", "tt", "u",
})
# Inline, but not words: kept whole, never translated.
OPAQUE = frozenset({
    "area", "audio", "canvas", "code", "embed", "iframe", "img", "input", "kbd", "map",
    "math", "meter", "object", "picture", "pre", "progress", "samp", "script", "source",
    "style", "svg", "template", "textarea", "var", "video", "wbr",
})
# Never walked into at all.
SKIP = frozenset({"script", "style", "template", "code", "pre", "svg", "math", "textarea",
                  "kbd", "samp", "var", "iframe", "object", "embed", "canvas", "audio",
                  "video", "picture", "map"})
TEXT_ATTRS = ("alt", "title", "placeholder", "aria-label", "aria-placeholder", "label")
_BUTTON_INPUTS = frozenset({"button", "submit", "reset"})
_META_NAMES = frozenset({"description", "og:title", "og:description", "og:site_name",
                         "twitter:title", "twitter:description", "apple-mobile-web-app-title",
                         "application-name"})
# HTML's own whitespace: a non-breaking space is content, not layout.
_WS = re.compile(r"[ \t\n\r\f]+")

# Defaults for the largest page a job takes; BABEL_WEB_MAX_SEGMENTS /
# BABEL_WEB_MAX_CHARS override them per deployment (read per job). A long
# article (Wikipedia's "Steve Jobs": 4,246 blocks, 314k characters) needs
# about this much.
MAX_SEGMENTS = 6000
MAX_CHARS = 400_000


def _limit(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, default)))
    except ValueError:
        return default

FORMAT = Format(".html", "website", "Website", "text/html", 5 * MB, None, "pagebirdy.web.html")


def _tag(el) -> str | None:
    return el.tag.lower() if isinstance(el.tag, str) else None


def _no_translate(el) -> bool:
    if (el.get("translate") or "").strip().lower() == "no":
        return True
    classes = (el.get("class") or "").split()
    return "notranslate" in classes


# --- parsing ---------------------------------------------------------------

def parse(data: bytes, charset: str | None = None):
    enc = None
    if charset:
        try:
            enc = codecs.lookup(charset).name
        except LookupError:
            enc = None
    parser = lxml.html.HTMLParser(encoding=enc, remove_blank_text=False, recover=True)
    try:
        root = lxml.html.document_fromstring(data, parser=parser)
    except (etree.ParserError, ValueError):
        raise FetchError("unsupported", "This page couldn't be read.")
    if root is None or root.find("body") is None and not len(root):
        raise FetchError("unsupported", "This page couldn't be read.")
    return root


def _doctype(root) -> str:
    dt = root.getroottree().docinfo.doctype
    return dt or "<!DOCTYPE html>"


def serialize(root) -> bytes:
    """UTF-8 HTML, declared as such in the first `<meta>` of `<head>`."""
    head = root.find("head")
    if head is None:
        head = etree.Element("head")
        root.insert(0, head)
    for m in list(head.iter("meta")):
        if m.get("charset") is not None or (m.get("http-equiv") or "").lower() == "content-type":
            m.getparent().remove(m)
    head.insert(0, etree.Element("meta", charset="utf-8"))
    return lxml.html.tostring(root, encoding="utf-8", method="html", doctype=_doctype(root))


def declared_language(root) -> str | None:
    """The page's declared language, lower-case, or None if it declares none."""
    for value in (root.get("lang"), root.get("{http://www.w3.org/XML/1998/namespace}lang"),
                  root.get("xml:lang")):
        if value and value.strip():
            return value.strip().lower()
    for m in root.iter("meta"):
        if (m.get("http-equiv") or "").lower() == "content-language" and m.get("content"):
            return m.get("content").split(",")[0].strip().lower() or None
    return None


def snapshot(page: Page) -> bytes:
    """The fetched page as this pipeline's source file: UTF-8, English only,
    with its effective `<base href>` (the page's own, resolved against where
    it was fetched from) as the one `<base>`."""
    root = parse(page.body, page.charset)
    lang = declared_language(root)
    if lang and lang.split("-")[0].split("_")[0] != "en":
        raise FetchError("unsupported", "Only English websites can be translated for now; "
                                        f"this page is marked as '{lang[:16]}'.")
    base = page.url
    for b in root.iter("base"):
        if b.get("href"):
            base = urljoin(page.url, b.get("href").strip())
            break
    for b in list(root.iter("base")):
        b.getparent().remove(b)
    head = root.find("head")
    if head is None:
        head = etree.Element("head")
        root.insert(0, head)
    head.insert(0, etree.Element("base", href=base))
    return serialize(root)


def read(path: str):
    with open(path, "rb") as f:
        return parse(f.read(), "utf-8")


# --- finding the segments ----------------------------------------------------

class _Walker:
    """Classifies every child once, so extract and rebuild see the same page."""

    def __init__(self):
        # Keyed by the element itself, never id(): lxml frees a proxy nobody
        # holds and may hand its id to another node.
        self._has_block: dict = {}

    def _contains_block(self, el) -> bool:
        key = el
        if key not in self._has_block:
            found = False
            for d in el.iterdescendants():
                t = _tag(d)
                if t and t not in INLINE and t not in OPAQUE and t != "br":
                    found = True
                    break
            self._has_block[key] = found
        return self._has_block[key]

    def kind(self, el) -> str:
        t = _tag(el)
        if t is None:
            return "object"   # a comment inside a sentence stays where it is
        if t == "br":
            return "break"
        if t in OPAQUE:
            return "object"
        if t in INLINE and not self._contains_block(el):
            if _no_translate(el) or not "".join(el.itertext()).strip():
                return "object"  # an icon element, or a run marked do-not-translate
            return "inline"
        return "block"


class _Group:
    """One maximal run of inline content in `container`: the text held at
    `holder` (`container.text` or a block sibling's `.tail`), then `items`."""

    def __init__(self, container, holder, attr):
        self.container = container
        self.holder = holder
        self.attr = attr          # "text" | "tail"
        self.items: list = []

    def lead(self) -> str:
        return getattr(self.holder, self.attr) or ""


def _groups(root, walker: _Walker) -> list[_Group]:
    out: list[_Group] = []

    def walk(el) -> None:
        t = _tag(el)
        if t is None or t in SKIP or _no_translate(el):
            return
        g = _Group(el, el, "text")
        for child in el:
            if walker.kind(child) == "block":
                out.append(g)
                walk(child)
                g = _Group(el, child, "tail")
            else:
                g.items.append(child)
        out.append(g)

    walk(root)
    return out


def _pieces(group: _Group, walker: _Walker) -> list[Piece]:
    """The group as run pieces. A text piece's `handle` is its chain of inline
    ancestors inside the group; an object's is (element, chain)."""
    pieces: list[Piece] = []
    numbering: dict = {}

    def key(chain) -> str:
        return ",".join(str(numbering.setdefault(e, len(numbering))) for e in chain)

    def text(s: str | None, chain) -> None:
        if s:
            pieces.append(Piece("text", _WS.sub(" ", s), key(chain), chain))

    def emit(el, chain) -> None:
        k = walker.kind(el)
        if k == "break":
            pieces.append(Piece("break", handle=(el, chain)))
        elif k == "object":
            pieces.append(Piece("object", handle=(el, chain)))
        else:
            inner = chain + (el,)
            text(el.text, inner)
            for c in el:
                emit(c, inner)
        text(el.tail, chain)

    text(group.lead(), ())
    for item in group.items:
        emit(item, ())
    return pieces


def _visible(pieces: list[Piece]) -> str:
    return "".join(p.text for p in pieces if p.kind == "text")


def _compact(pieces: list[Piece]) -> list[Piece]:
    """The pieces the engine sees. Whitespace alone is layout, not words: at
    the group's edges it is dropped (`_write_group` puts it back), and between
    two runs it joins the run before it — otherwise the newline after a link
    reaches the engine, and the reviewer, as an empty `⟦r1⟧ ⟦/r1⟧` pair."""
    out = list(pieces)
    while out and out[0].kind == "text" and not out[0].text.strip():
        out.pop(0)
    while out and out[-1].kind == "text" and not out[-1].text.strip():
        out.pop()
    result: list[Piece] = []
    prev: Piece | None = None
    for p in out:
        if p.kind == "text" and not p.text.strip() and prev is not None:
            p = Piece("text", p.text, prev.key, prev.handle)
        result.append(p)
        if p.kind == "text":
            prev = p
    return result


def _attr_targets(root) -> list[tuple[str, object, str]]:
    """(segment id, element, attribute) for every attribute a reader sees,
    outside anything that is never translated."""
    hidden: set = set()  # elements, not ids (see _Walker)
    out = []
    for n, el in enumerate(root.iter()):
        t = _tag(el)
        if t is None:
            continue
        parent = el.getparent()
        if (parent is not None and parent in hidden) or t in SKIP or _no_translate(el):
            hidden.add(el)
            continue
        if t == "meta":
            name = (el.get("name") or el.get("property") or "").lower()
            if name in _META_NAMES and el.get("content"):
                out.append((f"web:e{n}@content", el, "content"))
            continue
        for a in TEXT_ATTRS:
            if el.get(a):
                out.append((f"web:e{n}@{a}", el, a))
        if t == "input" and (el.get("type") or "").lower() in _BUTTON_INPUTS and el.get("value"):
            out.append((f"web:e{n}@value", el, "value"))
    return out


def _units(root):
    walker = _Walker()
    groups = [(f"web:g{i}", g, _pieces(g, walker)) for i, g in enumerate(_groups(root, walker))]
    groups = [(sid, g, p) for sid, g, p in groups if _visible(p).strip()]
    return walker, groups, _attr_targets(root)


# --- writing back ----------------------------------------------------------

class _Emitter:
    """Rebuilds a group's inline content: shells of the original inline
    elements (attributes kept, children replaced) around the translated text,
    reusing an open shell while consecutive text shares its ancestors."""

    def __init__(self):
        self.lead = ""
        self.top: list = []
        self.stack: list[tuple[object, object]] = []   # (original, shell)

    def _children(self):
        return list(self.stack[-1][1]) if self.stack else self.top

    def text(self, s: str) -> None:
        if not s:
            return
        kids = self._children()
        if kids:
            kids[-1].tail = (kids[-1].tail or "") + s
        elif self.stack:
            shell = self.stack[-1][1]
            shell.text = (shell.text or "") + s
        else:
            self.lead += s

    def node(self, n) -> None:
        if self.stack:
            self.stack[-1][1].append(n)
        else:
            self.top.append(n)

    def chain(self, chain) -> None:
        keep = 0
        while (keep < len(self.stack) and keep < len(chain)
               and self.stack[keep][0] is chain[keep]):
            keep += 1
        del self.stack[keep:]
        for orig in chain[keep:]:
            shell = orig.makeelement(orig.tag, dict(orig.attrib))
            self.node(shell)
            self.stack.append((orig, shell))


def _write_group(group: _Group, raw: list[Piece], seg) -> Issue | None:
    pieces = _compact(raw)
    _, layout = encode(pieces)
    outs = decode(seg.target, layout)
    if outs is None:
        return reject_tags(seg, seg.id)
    # A pair the engine kept but emptied ("⟦r4⟧⟦/r4⟧", its words moved outside)
    # passes the gate's count, yet the link or emphasis it stood for would
    # vanish from the page. Same remedy as misordered tags: source kept, a
    # person decides.
    # A pair that only styled its words (a colour, bold) is different: the
    # translation is still whole, so it is written without that styling rather
    # than leaving the English on a translated page. A link never is — its
    # words are where a reader clicks.
    filled = {o.span for o in outs if o.kind == "text" and o.text.strip()}
    # Elements every word of the group sits in (a heading that is one big
    # link) are written anyway; only what the emptied pair alone stood for
    # can be lost.
    shared = set(layout.spans[layout.base][0].handle) if layout.base >= 0 else set()
    unstyled = []
    for span in layout.tags.values():
        words = "".join(p.text for p in layout.spans[span]).strip()
        if span not in filled and words:
            if any(_tag(e) == "a" and e not in shared for e in layout.spans[span][0].handle):
                return reject_tags(seg, seg.id)
            unstyled.append(words)
    # The whitespace at the group's outer edges is layout, not words: the
    # engine never saw it, so it is put back as it was.
    first, last = raw[0], raw[-1]
    lead_ws = " " if first.kind == "text" and first.text[:1] == " " else ""
    trail_ws = " " if last.kind == "text" and last.text[-1:] == " " else ""

    em = _Emitter()
    em.text(lead_ws)
    texts = [i for i, o in enumerate(outs) if o.kind == "text"]
    for i, o in enumerate(outs):
        if o.kind == "text":
            chunk = restore(o.text, seg.placeholders)
            if texts and i == texts[0]:
                chunk = chunk.lstrip() if lead_ws else chunk
            em.chain(layout.spans[o.span][0].handle)
            em.text(chunk)
        elif o.kind == "object":
            el, chain = o.piece.handle
            em.chain(chain)
            clone = copy.deepcopy(el)
            clone.tail = None
            em.node(clone)
        else:
            em.node(etree.Element("br"))
    em.chain(())
    em.text(trail_ws)

    container = group.container
    for item in group.items:
        container.remove(item)
    setattr(group.holder, group.attr, em.lead or None)
    at = 0 if group.holder is container else container.index(group.holder) + 1
    for n in em.top:
        container.insert(at, n)
        at += 1
    if unstyled:
        return Issue("warning", "tags", seg.id, "written without the styling on "
                     + ", ".join(f'"{w}"' for w in unstyled))
    return None


def _set_direction(root, lang: Language) -> None:
    root.set("lang", lang.code)
    if lang.direction == "rtl":
        root.set("dir", "rtl")
    elif (root.get("dir") or "").lower() == "rtl":
        del root.attrib["dir"]


class HtmlAdapter:
    def extract(self, src: str):
        root = read(src)
        _, groups, attrs = _units(root)
        segments = [blank_segment(sid, encode(_compact(p))[0].strip()) for sid, _, p in groups]
        segments += [blank_segment(sid, _WS.sub(" ", el.get(a)).strip())
                     for sid, el, a in attrs]
        segments = [s for s in segments if s.source]
        chars = sum(len(s.source) for s in segments)
        max_segments = _limit("BABEL_WEB_MAX_SEGMENTS", MAX_SEGMENTS)
        max_chars = _limit("BABEL_WEB_MAX_CHARS", MAX_CHARS)
        if len(segments) > max_segments or chars > max_chars:
            raise FetchError("unsupported", "This page has too much text to translate "
                                            f"(limit {max_segments} blocks / "
                                            f"{max_chars // 1000}k characters).")
        if not any(re.search(r"[^\W\d_]", s.source) for s in segments):
            raise FetchError("unsupported", "We couldn't find any text to translate on this "
                                            "page. Pages that build their content with "
                                            "JavaScript aren't supported yet.")
        return segments

    def rebuild(self, src, segments, out, lang):
        root = read(src)
        _, groups, attrs = _units(root)
        by_id = {s.id: s for s in segments}
        issues: list[Issue] = []
        # Attributes first: an element copied into a rebuilt group (an <img>
        # inside a sentence) then carries its translated alt with it.
        for sid, el, a in attrs:
            seg = by_id.get(sid)
            if writable(seg):
                el.set(a, _WS.sub(" ", restore(seg.target, seg.placeholders)).strip())
        for sid, group, pieces in groups:
            seg = by_id.get(sid)
            if writable(seg):
                issue = _write_group(group, pieces, seg)
                if issue is not None:
                    issues.append(issue)
        _set_direction(root, lang)
        sanitize(root)
        data = serialize(root)
        root = parse(data, "utf-8")
        harden_head(root)
        with open(out, "wb") as f:
            f.write(lxml.html.tostring(root, encoding="utf-8", method="html",
                                       doctype=_doctype(root)))
        return issues

    def validate(self, src, out):
        try:
            a, b = read(src), read(out)
        except FetchError as e:
            return [Issue("error", "unreadable", "output", str(e))]
        for el in b.iter():
            t = _tag(el)
            if t in ("script", "iframe", "object", "embed") or (
                    t and any(k.lower().startswith("on") for k in el.attrib)):
                return [Issue("error", "unsafe", t, "executable content survived sanitizing")]
        issues = []

        def links(root):
            return Counter((_tag(e), e.get("href") or e.get("src"))
                           for e in root.iter("a", "img") if e.get("href") or e.get("src"))
        sanitize(a)
        if links(a) != links(b):
            issues.append(Issue("warning", "structure", "links",
                                "links or images differ in count from the source"))
        return issues

    def units(self, src):
        _, groups, attrs = _units(read(src))
        return {"blocks": len(groups), "attributes": len(attrs)}


def render_source(src: str) -> bytes:
    """The untranslated snapshot, made as safe to serve as a translation."""
    root = read(src)
    sanitize(root)
    root = parse(serialize(root), "utf-8")
    harden_head(root)
    return lxml.html.tostring(root, encoding="utf-8", method="html", doctype=_doctype(root))


ADAPTER = HtmlAdapter()
