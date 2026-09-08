"""Linked-graphic translation for the IDML path.

An IDML layout routinely places small `.ai` word-art graphics for stylized
callouts ("SAY", "GO!") instead of setting them as InDesign text — common for
display type that must render exactly regardless of what fonts a machine has.
`IdmlPackage.segments()` only sees `<Content>` text, so these words are
invisible to translation and ship in English.

`.ai` is PDF-compatible (Illustrator's native format is PDF plus private
data), so a linked graphic with live text can go through the exact same
ingest -> protect -> translate -> reassemble core as the PDF path — treating
it as a one-page PDF.

Some display words in these graphics are converted to vector OUTLINES rather
than kept as live text (a common Illustrator step so the exact letterforms
survive regardless of what fonts are installed later) — no text object exists
for them at all, so live-text extraction alone never finds them (this is
exactly how a "SAY" callout and its neighboring "GO!" arrow can be the same
kind of graphic yet only one is real text). Vision OCR reads the RENDERED
pixels instead, which works on outlined vector art exactly as it would on a
scanned image, so it's run on every linked graphic and merged in — the same
`merge_ocr_lines` dedup the main PDF path uses, whose own docstring uses a
"GO!" beside a headline as its worked example of this exact situation.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from urllib.parse import unquote, urlparse

import fitz

from babel.ingest.ocr import merge_ocr_lines, ocr_image_regions
from babel.ingest.pdf import extract_lines
from babel.protect.mathguard import build_segments
from babel.reassemble.pdf import rebuild_pdf
from babel.translate.translator import Translator

logger = logging.getLogger("babel.idml.graphics")

# Anchored to the attribute's own quotes (unlike a bare substring match) so
# relink() can safely replace one URI without touching another that happens
# to share it as a prefix (e.g. "SAY.ai" vs "SAY.ai.bak").
_LINK_ATTR_RE = re.compile(rb'LinkResourceURI="([^"]*)"')
_LINKABLE_EXTS = (".ai", ".eps", ".pdf")
_LINKED_PREFIXES = ("Spreads/", "MasterSpreads/", "Stories/")


def _resolve_uri(uri: str) -> str | None:
    """`file:/Users/x/Links/SAY.ai`, `file:///...`, or a UNC-style
    `file://host/share/SAY.ai` -> a local filesystem path.

    Delegates to `urlparse` rather than hand-stripping slashes so a network
    host in the authority component doesn't get folded into the path (a
    `file://SERVER/share/x` URI resolving to `/SERVER/share/x` would silently
    point at a nonexistent local path instead of the intended `/share/x` —
    or the UNC share, which this still doesn't reach, but at least doesn't
    corrupt into a wrong-but-plausible-looking local path)."""
    if not uri.startswith("file:"):
        return None
    parsed = urlparse(uri)
    path = unquote(parsed.path)
    if os.name == "nt" and path.startswith("/") and len(path) > 2 and path[2] == ":":
        path = path[1:]
    return path


def find_linked_graphics(entries: dict[str, bytes]) -> dict[str, str]:
    """Map each distinct linked-graphic URI (as written in the IDML XML) to its
    resolved local path. Scanned from Spreads/MasterSpreads (a graphic placed
    as its own page item) AND Stories (an inline/anchored graphic — e.g. a
    "SAY" callout placed mid-sentence — is a child of the paragraph flow, so
    its own `<Link>` lives in the story's XML, not the spread's)."""
    found: dict[str, str] = {}
    for name, data in entries.items():
        if not name.startswith(_LINKED_PREFIXES):
            continue
        for m in _LINK_ATTR_RE.finditer(data):
            # IDML is UTF-8 XML; a raw (non-percent-encoded) accented path
            # byte sequence must decode as UTF-8, not ASCII, or it silently
            # mangles into a different, nonexistent filename.
            uri = m.group(1).decode("utf-8", errors="replace")
            path = _resolve_uri(uri)
            if path and path.lower().endswith(_LINKABLE_EXTS):
                found[uri] = path
    return found


def translate_graphic(path: str, out_path: str, lang, tm, primary, secondary,
                       with_ocr: bool = True) -> bool:
    """Translate a single linked graphic in place (as a one-page PDF/.ai file).

    Returns False (no file written) if the graphic has no extractable prose —
    the common case, since most placed assets are pure artwork."""
    lines = extract_lines(path)
    if with_ocr:
        try:
            doc = fitz.open(path)
            page_rect = tuple(doc[0].rect)
            doc.close()
            # An explicit region (the whole page) rather than
            # detect_image_regions: that only finds RASTER images, but the
            # text this is meant to catch is typically vector outlines with
            # no raster backing at all — OCR still reads it fine off the
            # rendered pixels, it just needs to be told where to look.
            ocr_lines, note = ocr_image_regions(path, regions={0: [page_rect]})
            if ocr_lines:
                logger.info("linked graphic OCR: %s -> %s", path, note)
            lines = merge_ocr_lines(lines, ocr_lines)
        except Exception as e:  # OCR is a bonus pass; never let it block live-text translation
            logger.info("linked graphic OCR failed, continuing with live text only: %s (%s)",
                        path, e)
    if not lines:
        return False
    segments = build_segments(lines)
    if not any(s.is_translatable for s in segments):
        return False
    Translator(primary, secondary, tm, target_lang=lang.code).run(segments)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    rebuild_pdf(path, segments, out_path, target_lang=lang.code)
    return True


def _output_filename(path: str) -> str:
    """basename, disambiguated by a short hash of the full source path — two
    different linked graphics that happen to share a filename (a recurring
    reused-asset-name pattern across chapters/vendors) must not collide onto
    the same output file under one shared Links_<lang>/ directory."""
    base, ext = os.path.splitext(os.path.basename(path))
    digest = hashlib.sha1(os.path.abspath(path).encode("utf-8")).hexdigest()[:8]
    return f"{base}-{digest}{ext}"


def translate_linked_graphics(entries: dict[str, bytes], lang, tm, primary, secondary,
                               out_dir: str, with_ocr: bool = True) -> dict[str, str]:
    """Translate every linked graphic with live or OCR-recoverable text;
    returns {old_uri: new_uri} for the ones actually rewritten, so the caller
    can repoint the IDML's links."""
    links = find_linked_graphics(entries)
    graphics_dir = os.path.join(out_dir, f"Links_{lang.code}")
    mapping: dict[str, str] = {}
    for uri, path in links.items():
        if not os.path.isfile(path):
            logger.info("linked graphic not found on disk, skipping: %s", path)
            continue
        out_path = os.path.join(graphics_dir, _output_filename(path))
        try:
            translated = translate_graphic(path, out_path, lang, tm, primary, secondary,
                                            with_ocr=with_ocr)
        except Exception as e:  # a malformed/unusual linked file must not abort the job
            logger.info("linked graphic translate failed, left as-is: %s (%s)", path, e)
            continue
        if translated:
            new_uri = "file:" + os.path.abspath(out_path)
            mapping[uri] = new_uri
            logger.info("linked graphic translated: %s -> %s", path, out_path)
    return mapping


def relink(entries: dict[str, bytes], mapping: dict[str, str]) -> int:
    """Repoint LinkResourceURI attributes in Spreads/MasterSpreads to the
    translated graphics, in place on `entries`. Returns the number of DISTINCT
    graphics relinked (not the number of XML occurrences touched — the same
    graphic is often placed on several spreads).

    Stories/*.xml is deliberately excluded here: `IdmlPackage.save()` always
    re-serializes Story entries from the parsed lxml tree it already holds
    (for Content-node text rewrites), never from raw bytes — so a byte-level
    edit to a Story entry here would be silently discarded at save time. An
    inline/anchored graphic's `<Link>` lives inside its story, and is relinked
    on the tree directly by `IdmlPackage.relink()` instead (see
    `relink_story_tree`)."""
    if not mapping:
        return 0
    relinked: set[str] = set()
    for name in list(entries.keys()):
        if not (name.startswith("Spreads/") or name.startswith("MasterSpreads/")):
            continue
        data = entries[name]

        def _sub(m: re.Match) -> bytes:
            uri = m.group(1).decode("utf-8", errors="replace")
            new_uri = mapping.get(uri)
            if new_uri is None:
                return m.group(0)
            relinked.add(uri)
            return b'LinkResourceURI="' + new_uri.encode("utf-8") + b'"'

        new_data = _LINK_ATTR_RE.sub(_sub, data)
        if new_data != data:
            entries[name] = new_data
    return len(relinked)


def relink_story_tree(tree, mapping: dict[str, str]) -> int:
    """Repoint LinkResourceURI attributes on an already-parsed Story lxml
    tree, in place. Returns the number of distinct graphics relinked."""
    if not mapping:
        return 0
    relinked: set[str] = set()
    for el in tree.iter():
        uri = el.get("LinkResourceURI")
        new_uri = mapping.get(uri) if uri else None
        if new_uri is not None:
            el.set("LinkResourceURI", new_uri)
            relinked.add(uri)
    return len(relinked)
