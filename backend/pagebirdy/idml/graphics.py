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
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote, urlparse

import fitz

from pagebirdy.fonts import resolve
from pagebirdy.ingest.ocr import merge_ocr_lines, ocr_image_regions
from pagebirdy.ingest.pdf import extract_lines
from pagebirdy.protect.mathguard import build_segments
from pagebirdy.reassemble.pdf import rebuild_pdf
from pagebirdy.translate.translator import Translator

logger = logging.getLogger("pagebirdy.idml.graphics")

# Anchored to the attribute's own quotes (unlike a bare substring match) so
# scanning picks up each URI whole, never a prefix of a longer one
# (e.g. "SAY.ai" vs "SAY.ai.bak").
_LINK_ATTR_RE = re.compile(rb'LinkResourceURI="([^"]*)"')
_PSD_EXTS = (".psd",)
_LINKABLE_EXTS = (".ai", ".eps", ".pdf") + _PSD_EXTS
_LINKED_PREFIXES = ("Spreads/", "MasterSpreads/", "Stories/")

# Mascot assets (Buzz the dog, Boom the cat, …) carry the character's own name
# as tiny live vector text on a collar/name-tag — e.g. "BUZZ" stacked one
# letter per line at ~2-6pt on a "GO!" callout's dog. Real callout/label text
# in these same linked graphics runs 19-21.5pt. Below this floor is always
# that decorative name-tag, never content: translating it fragments a proper
# noun into single-letter LLM calls that come back as garbage, and it renders
# back into the same tiny stacked-vertical layout, corrupting the artwork.
_MIN_LIVE_TEXT_SIZE = 10.0


def _worth_translating(line) -> bool:
    return all(s.size >= _MIN_LIVE_TEXT_SIZE for s in line.spans)


def _grow_canvas_for_translation(path: str, segments: "list", lang) -> tuple[str, "list"]:
    """A word-art badge's canvas is cropped tight to the SOURCE word's own ink
    (e.g. "SAY" on a 58.5x23.8pt artboard, glyph bbox alone) — there is no
    slack. `rebuild_pdf`'s ordinary auto-fit would shrink a longer translation
    ("DIZER") to keep it inside that box, visibly smaller than the source word
    despite plenty of open canvas around it in the composed page (the arrow/
    speech-bubble shape lives in a separate InDesign object, not this file).

    InDesign places these via a fixed `ItemTransform` with `ClippingType=None`
    (confirmed against a real translated .idml's Spread XML) — nothing crops
    the placed graphic to its nominal page box, and the source art already
    bleeds past its own artboard on this asset class (glyph descenders/
    overshoot). So widening the artboard and NOT shrinking the font is safe:
    the extra width just extends into already-unclipped space instead of
    forcing the word smaller.

    Returns (possibly rewritten path, possibly widened segments). Only
    touches segments at/above `_MIN_LIVE_TEXT_SIZE` (real callout words, not
    the tiny mascot name-tag text already filtered by `_worth_translating`).
    """
    import dataclasses

    growable = [s for s in segments if s.is_translatable and s.size >= _MIN_LIVE_TEXT_SIZE]
    if not growable:
        return path, segments

    extra = 0.0
    widths: dict[str, float] = {}
    for s in growable:
        text = " ".join(s.restored_target().split()) if s.target else ""
        if not text:
            continue
        font_path = resolve(lang.fonts.get("bold" if s.bold else "regular", []))
        if not font_path:
            continue
        font = fitz.Font(fontfile=font_path)
        needed = font.text_length(text, s.size) + 4.0  # small breathing margin
        current = s.bbox[2] - s.bbox[0]
        widths[s.id] = needed
        extra = max(extra, needed - current)

    if extra <= 0:
        return path, segments

    doc = fitz.open(path)
    try:
        page = doc[0]
        r = page.rect
        wide = fitz.Rect(r.x0, r.y0, r.x1 + extra, r.y1)
        # InDesign/Illustrator place a linked PDF/.ai by its ArtBox (visible
        # content bounds), not MediaBox — confirmed against a real translated
        # .idml's Spread XML, whose <GraphicBounds> matches the source
        # ArtBox exactly. Widening only MediaBox (as an earlier version of
        # this fix did) leaves ArtBox/CropBox/TrimBox/BleedBox stale or
        # dropped entirely on save, so InDesign composites against the OLD
        # bounds while our text is drawn in the new ones — the two disagree
        # and the mismatch shows as a wrong-colored patch behind the word.
        page.set_mediabox(wide)
        page = doc.reload_page(page)  # other boxes must validate against the NEW MediaBox
        # Shrunk by a hair: the other *Box setters require strict containment
        # within MediaBox, and a float round-trip through the PDF's own
        # string serialization can make an exactly-equal rect fail that
        # check by an epsilon.
        snug = fitz.Rect(wide.x0, wide.y0, wide.x1 - 0.01, wide.y1 - 0.01)
        page.set_cropbox(snug)
        page.set_artbox(snug)
        page.set_trimbox(snug)
        page.set_bleedbox(snug)
        grown = os.path.join(
            os.path.dirname(path) or ".",
            f".grown-{os.path.basename(path)}",
        )
        doc.save(grown)
    finally:
        doc.close()

    def _widen(s):
        if s.id not in widths:
            return s
        # Only `bbox` grows (drives the typeset/draw width in `_place`).
        # `bboxes` stays at its original tight size on purpose: rebuild_pdf's
        # redaction step erases exactly those rects (`s.bboxes or [s.bbox]`),
        # and erasing the padded area too paints a same-size white rectangle
        # that shows through as a mismatched patch against a colored
        # background behind the graphic (see this function's docstring).
        x0, y0, _, y1 = s.bbox
        return dataclasses.replace(s, bbox=(x0, y0, x0 + widths[s.id], y1))

    return grown, [_widen(s) for s in segments]


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


def _psd_to_pdf(path: str) -> str:
    """Composite a linked `.psd` to a flat image and wrap it in a one-page
    PDF, written to a temp file whose path is returned.

    PyMuPDF — and everything downstream that opens a linked graphic
    (`extract_lines`, `ocr_image_regions`, `rebuild_pdf`) — only understands
    PDF-compatible input, which a PSD isn't. Any text baked into the PSD's
    pixels is still recoverable by OCR once it's sitting on a PDF page; a
    PSD text LAYER (if the asset has one) is not preserved as live text
    here — it's flattened into the composite along with every other layer,
    same as any other raster source. The caller is responsible for deleting
    the temp file."""
    from psd_tools import PSDImage

    image = PSDImage.open(path).composite()
    if image.mode != "RGB":
        image = image.convert("RGB")
    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    image.save(tmp_path, "PDF")
    return tmp_path


def translate_graphic(path: str, out_path: str, lang, primary, secondary,
                       with_ocr: bool = True) -> bool:
    """Translate a single linked graphic in place (as a one-page PDF/.ai file).

    A linked `.psd` is composited to a flat image and wrapped in a synthetic
    one-page PDF first (`_psd_to_pdf`) — PyMuPDF can't open PSD directly —
    then goes through the exact same OCR/translate/rebuild path as any other
    linked graphic; it never has live text (PSD layers aren't preserved),
    only the OCR pass ever finds anything in one.

    Returns False (no file written) if the graphic has no extractable prose —
    the common case, since most placed assets are pure artwork."""
    is_psd = path.lower().endswith(_PSD_EXTS)
    work_path = _psd_to_pdf(path) if is_psd else path
    try:
        lines = [ln for ln in extract_lines(work_path) if _worth_translating(ln)]
        if with_ocr:
            try:
                doc = fitz.open(work_path)
                page_rect = tuple(doc[0].rect)
                doc.close()
                # An explicit region (the whole page) rather than
                # detect_image_regions: that only finds RASTER images, but the
                # text this is meant to catch is typically vector outlines with
                # no raster backing at all — OCR still reads it fine off the
                # rendered pixels, it just needs to be told where to look.
                ocr_lines, note = ocr_image_regions(work_path, regions={0: [page_rect]})
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
        Translator(primary, secondary, target_lang=lang.code).run(segments)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        render_path, segments = _grow_canvas_for_translation(work_path, segments, lang)
        try:
            rebuild_pdf(render_path, segments, out_path, target_lang=lang.code)
        finally:
            if render_path != work_path:
                os.remove(render_path)
    finally:
        if is_psd:
            os.remove(work_path)
    return True


def _content_hash(path: str) -> str:
    """sha1 of the file's own bytes — used as the cache/disambiguation key so
    two uploads of the byte-identical linked graphic (the common case for a
    batch of documents sharing one Links folder) hash to the same key
    regardless of which job's temp directory the file happens to live in."""
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _output_filename(path: str, content_hash: str) -> str:
    """basename, disambiguated by a hash of the source's own CONTENT — two
    different linked graphics that happen to share a filename (a recurring
    reused-asset-name pattern across chapters/vendors) must not collide onto
    the same output file under one shared Links_<lang>/ directory. Hashing
    content rather than path also makes this the cache key: the same asset
    reused across many jobs (or attached to a batch of documents that all
    share one Links folder) maps to the same output file, so it is OCR'd and
    translated once, not once per job.

    A `.psd` source keeps its `.ext` swapped to `.pdf`: `translate_graphic`
    never reconstructs real PSD layers, it writes PDF-format bytes (same as
    every other linked graphic) — naming the output `foo.psd` would be a
    lie InDesign takes at face value and fails to open."""
    base, ext = os.path.splitext(os.path.basename(path))
    if ext.lower() in _PSD_EXTS:
        ext = ".pdf"
    return f"{base}-{content_hash}{ext}"


def _basename_any(path: str) -> str:
    """Filename of a path that may use POSIX or Windows separators — the URIs
    written into an IDML carry the original designer's OS paths (often
    `C:/...` or `C:\\...\\`), so `os.path.basename` alone is not enough."""
    return re.split(r"[/\\]", path)[-1]


def translate_linked_graphics(entries: dict[str, bytes], lang, primary, secondary,
                               out_dir: str, with_ocr: bool = True,
                               local_links_dir: str | None = None) -> dict[str, str]:
    """Translate every linked graphic with live or OCR-recoverable text;
    returns {old_uri: new_uri} for the ones actually rewritten, so the caller
    can repoint the IDML's links.

    `local_links_dir`, if given, is searched by basename for any graphic whose
    recorded absolute path (the original designer's machine) is not present
    locally — lets an operator drop a `Links/` folder next to the uploaded
    IDML instead of reproducing the original path."""
    links = find_linked_graphics(entries)
    graphics_dir = os.path.join(out_dir, f"Links_{lang.code}")
    mapping: dict[str, str] = {}

    # First pass (cheap, local-disk only): resolve each URI's path, hash its
    # bytes, and settle every cache hit — leaving only the graphics that
    # actually need OCR + an LLM call queued up for the parallel pass below.
    pending: list[tuple[str, str, str, str]] = []  # (uri, path, out_path, empty_marker)
    for uri, path in links.items():
        if not os.path.isfile(path):
            fallback = (os.path.join(local_links_dir, _basename_any(path))
                        if local_links_dir else None)
            if fallback and os.path.isfile(fallback):
                logger.info("linked graphic resolved via local Links dir: %s -> %s",
                            path, fallback)
                path = fallback
            else:
                logger.info("linked graphic not found on disk, skipping: %s", path)
                continue

        content_hash = _content_hash(path)
        out_path = os.path.join(graphics_dir, _output_filename(path, content_hash))
        # `Links_<lang>/` is shared across every job translated to this
        # language (see the module docstring), and `out_path`/`empty_marker`
        # are keyed by the graphic's own bytes — so a document batch that
        # attaches the same Links folder to several uploads (or the same
        # reused asset recurring across unrelated documents) OCRs and
        # translates each distinct graphic exactly once, not once per job.
        empty_marker = os.path.join(graphics_dir, f".{content_hash}.empty")
        if os.path.isfile(out_path):
            mapping[uri] = "file:" + os.path.abspath(out_path)
            logger.info("linked graphic cache hit (translated): %s -> %s", path, out_path)
            continue
        if os.path.isfile(empty_marker):
            logger.info("linked graphic cache hit (nothing to translate): %s", path)
            continue
        pending.append((uri, path, out_path, empty_marker))

    if not pending:
        return mapping

    # Each graphic is an independent OCR + LLM-translate + PDF rebuild call —
    # running them one at a time was the actual cause of a document with a
    # few dozen linked callouts taking as long as the whole rest of the job.
    # Matches the worker count `translate_links_folder` already uses for the
    # same call on a standalone batch of linked graphics.
    _MAX_CONCURRENT_GRAPHICS = 6

    def _translate_one(uri: str, path: str, out_path: str, empty_marker: str):
        try:
            translated = translate_graphic(path, out_path, lang, primary, secondary,
                                            with_ocr=with_ocr)
        except Exception as e:  # a malformed/unusual linked file must not abort the job
            logger.info("linked graphic translate failed, left as-is: %s (%s)", path, e)
            return uri, path, out_path, empty_marker, None
        return uri, path, out_path, empty_marker, translated

    with ThreadPoolExecutor(max_workers=_MAX_CONCURRENT_GRAPHICS) as ex:
        futures = [ex.submit(_translate_one, *task) for task in pending]
        for fut in as_completed(futures):
            uri, path, out_path, empty_marker, translated = fut.result()
            if translated:
                new_uri = "file:" + os.path.abspath(out_path)
                mapping[uri] = new_uri
                logger.info("linked graphic translated: %s -> %s", path, out_path)
            elif translated is not None:
                os.makedirs(graphics_dir, exist_ok=True)
                open(empty_marker, "w").close()
    return mapping


def relink_story_tree(tree, mapping: dict[str, str], seen: set[str] | None = None) -> int:
    """Repoint LinkResourceURI attributes on an already-parsed lxml tree, in
    place. Generic over any IDML tree despite the name — `IdmlPackage.relink`
    uses it for Stories, Spreads and MasterSpreads alike, since all three are
    re-serialized from their parsed tree at save time.

    Returns the number of distinct graphics relinked in THIS tree. Pass a
    shared `seen` set to accumulate distinct URIs across several trees — the
    same graphic is commonly placed on more than one spread, and the caller
    reports graphics, not occurrences."""
    if not mapping:
        return 0
    relinked: set[str] = set()
    for el in tree.iter():
        uri = el.get("LinkResourceURI")
        new_uri = mapping.get(uri) if uri else None
        if new_uri is not None:
            el.set("LinkResourceURI", new_uri)
            relinked.add(uri)
    if seen is not None:
        seen.update(relinked)
    return len(relinked)
