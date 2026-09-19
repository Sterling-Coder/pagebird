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

from pagebirdy.idml.render import _nums
from pagebirdy.models import Segment
from pagebirdy.protect.mathguard import _TOKEN_RE, Allocator

# An .idml is a zip of XML uploaded by the user — parsing it with lxml's
# default settings (external entity/DTD resolution on) is a classic XXE
# vector (local file read, SSRF, or billion-laughs DoS via a crafted
# Stories/Spreads/MasterSpreads XML). Every `etree.fromstring` call in this
# module must go through this hardened parser instead of the bare default.
_XML_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)

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
        # INVARIANT: once parsed, these three dicts are the SOLE source of
        # truth for their zip-entry prefixes. `save()` re-serializes every
        # `Stories/`, `Spreads/` and `MasterSpreads/` entry from its tree and
        # never consults `self._entries` for those prefixes again — so any
        # future byte-level mutation of them (another `relink`-style edit,
        # say) is silently discarded. Mutate the tree instead. (`_entries`
        # remains the source of truth, and the place to patch, for every
        # OTHER entry — e.g. `Resources/Preferences.xml` in
        # `_flip_page_binding`.)
        self._stories: dict[str, etree._Element] = {}
        self._spreads: dict[str, etree._Element] = {}
        self._master_spreads: dict[str, etree._Element] = {}
        self._node_index: dict[str, etree._Element] = {}
        # Segment id -> the run's embedded marker children (`<?ACE 7?>` etc.)
        # with the text each one followed; see `_content_text`/`_write_content`.
        self._markers: dict[str, list[tuple[object, str]]] = {}
        # Segment id -> the `<Story Self>` it lives in, so `apply()` knows
        # which stories were rewritten and `_auto_size_frames` can grow
        # exactly those stories' frames.
        self._segment_story: dict[str, str] = {}

        with zipfile.ZipFile(path) as z:
            self._names = z.namelist()
            for n in self._names:
                data = z.read(n)
                self._entries[n] = data
                if n.startswith("Stories/") and n.endswith(".xml"):
                    self._stories[n] = etree.fromstring(data, parser=_XML_PARSER)
                elif n.startswith("Spreads/") and n.endswith(".xml"):
                    self._spreads[n] = etree.fromstring(data, parser=_XML_PARSER)
                elif n.startswith("MasterSpreads/") and n.endswith(".xml"):
                    self._master_spreads[n] = etree.fromstring(data, parser=_XML_PARSER)

        self._style_size_cache: dict[str, float | None] = {}
        self._style_justification_cache: dict[str, str | None] = {}
        self._style_font_cache: dict[str, str | None] = {}
        self._style_defs = _parse_style_defs(self._entries.get("Resources/Styles.xml"))
        # A single CharacterStyleRange can hold several Content runs (split by
        # a <Br/> or special character), each becoming its own Segment — so
        # `apply()` can revisit the same range more than once per call. Once
        # shrunk, the range's PointSize attribute itself becomes the new
        # "explicit" value, so a naive re-resolve on a second visit would
        # shrink it again on top of the first — cache the target by node
        # identity to shrink each range exactly once.
        #
        # The cache value holds the node itself (not just its size) because
        # lxml hands out a fresh Python wrapper per traversal; once the one
        # `id()` was taken from is garbage collected, that `id()` can be
        # reused for a wrapper around a completely different node, silently
        # merging two unrelated ranges' cache entries. Keeping a live
        # reference here pins the id for the object's whole lifetime.
        self._shrunk_ranges: dict[int, tuple[object, float]] = {}
        # Same node-identity-pinning trick, for paragraph ranges whose
        # Justification we've already flipped — several CharacterStyleRanges
        # (several segments) commonly share one ParagraphStyleRange, and
        # unlike a size shrink, flipping justification is not idempotent:
        # a second flip on a re-visit would flip it straight back.
        self._flipped_paragraphs: dict[int, object] = {}
        # Equation assemblies (see `_is_assembly`) are scaled once per
        # PARAGRAPH, not per run — same node-identity pinning, same reason
        # as `_shrunk_ranges`: the review loop re-applies the whole
        # document after an approved edit and must not compound the scale.
        self._assembly_cache: dict[int, tuple[object, bool]] = {}
        self._scaled_assemblies: dict[int, object] = {}

    # ---- style resolution ------------------------------------------------

    def _resolve_style_size(self, self_id: str | None) -> float | None:
        """Walk BasedOn until a style in the chain declares PointSize, or the
        chain runs out (no BasedOn recorded — the implicit document default)."""
        if self_id is None:
            return None
        if self_id in self._style_size_cache:
            return self._style_size_cache[self_id]
        seen: set[str] = set()
        cur = self_id
        result = None
        while cur and cur not in seen:
            seen.add(cur)
            entry = self._style_defs.get(cur, {})
            if entry.get("PointSize") is not None:
                result = entry["PointSize"]
                break
            cur = entry.get("BasedOn")
        self._style_size_cache[self_id] = result
        return result

    def _resolve_style_justification(self, self_id: str | None) -> str | None:
        """Same BasedOn walk as `_resolve_style_size`, for Justification."""
        if self_id is None:
            return None
        if self_id in self._style_justification_cache:
            return self._style_justification_cache[self_id]
        seen: set[str] = set()
        cur = self_id
        result = None
        while cur and cur not in seen:
            seen.add(cur)
            entry = self._style_defs.get(cur, {})
            if entry.get("Justification") is not None:
                result = entry["Justification"]
                break
            cur = entry.get("BasedOn")
        self._style_justification_cache[self_id] = result
        return result

    def _effective_size(self, char_style_range) -> float:
        """The size a run actually renders at, walking CharacterStyle first
        (it wins over ParagraphStyle in InDesign), then ParagraphStyle, then
        the document's default paragraph style."""
        explicit = char_style_range.get("PointSize")
        if explicit:
            return float(explicit)
        size = self._resolve_style_size(char_style_range.get("AppliedCharacterStyle"))
        if size is not None:
            return size
        para = char_style_range.getparent()
        if para is not None and _localname(para) == "ParagraphStyleRange":
            size = self._resolve_style_size(para.get("AppliedParagraphStyle"))
            if size is not None:
                return size
        default_size = self._style_defs.get(_DEFAULT_PARAGRAPH_STYLE, {}).get("PointSize")
        return default_size if default_size is not None else 12.0

    def _effective_justification(self, para_range) -> str:
        """The alignment a paragraph actually renders at: direct attribute,
        else resolved through its ParagraphStyle's BasedOn chain, else
        InDesign's implicit default (flush left) when nothing in the chain
        ever set it."""
        explicit = para_range.get("Justification")
        if explicit:
            return explicit
        resolved = self._resolve_style_justification(para_range.get("AppliedParagraphStyle"))
        if resolved is not None:
            return resolved
        default = self._style_defs.get(_DEFAULT_PARAGRAPH_STYLE, {}).get("Justification")
        return default if default is not None else "LeftAlign"

    def _resolve_style_font(self, self_id: str | None) -> str | None:
        """Same BasedOn walk as `_resolve_style_size`, for AppliedFont."""
        if self_id is None:
            return None
        if self_id in self._style_font_cache:
            return self._style_font_cache[self_id]
        seen: set[str] = set()
        cur = self_id
        result = None
        while cur and cur not in seen:
            seen.add(cur)
            entry = self._style_defs.get(cur, {})
            if entry.get("AppliedFont") is not None:
                result = entry["AppliedFont"]
                break
            cur = entry.get("BasedOn")
        self._style_font_cache[self_id] = result
        return result

    def _effective_font(self, content) -> str:
        """The font a run actually renders in: its own inline AppliedFont,
        else its CharacterStyle's BasedOn chain, else its paragraph's
        ParagraphStyle chain, else the document default paragraph style.

        Real client files set their math face on a NAMED character style
        (`CharacterStyle/MathPi 1`), not on the run — reading only the run
        saw no font, decided the run was prose, and sent a bare `5` (which
        draws as `=` in that face) to the engine as a number. Measured on
        one such file: 217 -> 739 protected runs once the chain is walked."""
        inline = _font_of(content)
        if inline:
            return inline
        run = content.getparent()
        while run is not None and _localname(run) != "CharacterStyleRange":
            run = run.getparent()
        if run is None:
            return ""
        font = self._resolve_style_font(run.get("AppliedCharacterStyle"))
        if font is not None:
            return font
        para = run.getparent()
        if para is not None and _localname(para) == "ParagraphStyleRange":
            font = self._resolve_style_font(para.get("AppliedParagraphStyle"))
            if font is not None:
                return font
        default = self._style_defs.get(_DEFAULT_PARAGRAPH_STYLE, {}).get("AppliedFont")
        return default or ""

    # ---- extract -------------------------------------------------------------

    def segments(self) -> list[Segment]:
        segs: list[Segment] = []
        counter = 0
        for name, tree in self._stories.items():
            short = name.split("/")[-1].rsplit(".", 1)[0]
            story_self = _story_self(tree)
            for content in _iter_content(tree):
                text, markers = _content_text(content)
                if not text.strip():
                    continue
                font = self._effective_font(content)
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
                if story_self:
                    self._segment_story[sid] = story_self
                if markers:
                    self._markers[sid] = markers
                segs.append(seg)
        return segs

    # ---- linked graphics (SAY/GO!-style .ai word-art, see idml.graphics) -----

    def raw_entries(self) -> dict[str, bytes]:
        """Every zip entry as raw bytes, INCLUDING Stories — a placed
        graphic's `<Link>` lives in Spreads/MasterSpreads, but an
        inline/anchored graphic (e.g. a "SAY" callout set mid-sentence) is
        part of the paragraph flow, so its `<Link>` lives inside its own
        story instead. Used only for scanning (`find_linked_graphics`);
        these bytes are never the save-time source of truth for Stories,
        Spreads or MasterSpreads (the parsed trees are), so mutating them
        here would be silently discarded — see `relink`."""
        return self._entries

    def relink(self, mapping: dict[str, str]) -> int:
        """Repoint LinkResourceURI occurrences to translated graphics, on
        every parsed tree this package holds. See
        `pagebirdy.idml.graphics.translate_linked_graphics` for building `mapping`.

        Stories, Spreads and MasterSpreads are all re-serialized from their
        parsed lxml tree at save time (never from `self._entries` for those
        prefixes — see the invariant in `__init__`), so the edit must happen
        on the tree directly or it is silently lost. A placed graphic's
        `<Link>` lives on a Spread/MasterSpread; an inline/anchored one lives
        inside its own story.

        Returns the number of DISTINCT graphics relinked — the same word-art
        is commonly placed on several spreads, and the QA report's
        `graphics_translated` counts graphics, not XML occurrences."""
        from pagebirdy.idml.graphics import relink_story_tree
        seen: set[str] = set()
        for trees in (self._stories, self._spreads, self._master_spreads):
            for tree in trees.values():
                relink_story_tree(tree, mapping, seen=seen)
        return len(seen)

    # ---- write back ----------------------------------------------------------

    def apply(self, segments: list[Segment], idml_font: str | None = None,
              size_delta: float = 0.0, direction: str | None = None) -> int:
        """Write translated text back into Content nodes. Math-font runs are left
        untouched. When idml_font is given, every rewritten run's AppliedFont is
        overridden to it (FillColor is untouched) — the original font's script
        rarely covers a non-Latin target language.

        `size_delta` shaves points off a run's effective PointSize — resolved
        through the style chain (CharacterStyle wins over ParagraphStyle,
        each walked via BasedOn, falling back to the document's default
        paragraph style) when the run has no direct PointSize override, since
        most runs in a real design set size via a named style rather than
        direct formatting. The resolved-and-shrunk value is then written as
        an explicit override on just this run — it does not touch the shared
        style definition, so other runs using the same style are unaffected.
        (Dense scripts like CJK/Hangul render heavier than Latin at the same
        point size, and InDesign doesn't auto-shrink text on reflow, so these
        are the runs that need the explicit head start.)

        `direction="rtl"` flips every Story's `StoryDirection` to
        `RightToLeftDirection`, the document's `PageBinding` to
        `RightToLeft` (`Resources/Preferences.xml`), and each rewritten
        run's paragraph `Justification` (flush-left <-> flush-right; centre,
        fully-justified, and the binding-relative values are left alone —
        they already mean the same thing regardless of direction). Writing
        the target text alone is not enough: InDesign still composes a story
        left-to-right, keeps the spine on the left, and sets Arabic/Hebrew
        prose flush left, unless each of these is told otherwise — none of
        it follows from the language of the text alone.

        Every free-floating page item (text frames, images, decorative
        shapes) on a content Spread is also moved to its mirrored position
        about that spread's horizontal center (`_mirror_spread`) — matching
        real RTL book layout, not just text alignment. The move is
        translate-only: an item's orientation and contents are never
        flipped, only its position changes. Items with no path geometry of
        their own (normally `Group`s) stay put — see `_mirror_spread`.
        Anchored/inline objects are untouched; they reposition naturally
        with their paragraph's new RTL flow.

        MasterSpreads — the shared template chrome (a lesson badge, a
        running-head side-tab, the footer, the page number) that repeats
        identically on every page — are deliberately NOT mirrored. Verified
        against a real client's Portuguese/Arabic edition pair: that
        chrome sits in the exact same position in both languages, while
        each page's own content (placed on its own Spread) mirrors. An
        earlier version of this mirrored MasterSpreads too, which visibly
        collided that chrome into space a page's own (correctly mirrored)
        content was already using.
        """
        applied = 0
        rewritten: set[str] = set()
        for s in segments:
            if s.has_math_font or s.target is None:
                continue
            if s.status not in ("translated", "tm_hit", "approved", "edited"):
                continue
            node = self._node_index.get(s.id)
            if node is not None:
                _write_content(node, s.restored_target(), self._markers.get(s.id, ()))
                story = self._segment_story.get(s.id)
                if story:
                    rewritten.add(story)
                if idml_font:
                    _set_applied_font(node, idml_font)
                if size_delta:
                    para = _paragraph_of(node)
                    if para is not None and self._is_assembly(para):
                        self._scale_assembly(para, size_delta)
                    else:
                        self._shrink_point_size(node, size_delta)
                if direction == "rtl":
                    self._flip_justification(node)
                applied += 1
        if direction == "rtl":
            for tree in self._stories.values():
                _set_story_direction(tree, "RightToLeftDirection")
            self._flip_page_binding()
            # Content Spreads mirror; MasterSpreads (the shared template
            # chrome — badge circle, running-head side-tab, footer, page
            # number) deliberately do NOT. Verified against a real client's
            # Portuguese/Arabic edition pair: page furniture that repeats
            # identically on every lesson page stays in the exact same
            # position in both languages, while that page's own content
            # (photos, titles, callouts placed on its own Spread) mirrors.
            # An earlier version of this also mirrored MasterSpreads, which
            # visibly collided master-spread chrome into space content was
            # already using after both moved independently.
            for tree in self._spreads.values():
                _mirror_spread(tree)
        if rewritten:
            self._auto_size_frames(rewritten)
        return applied

    def _auto_size_frames(self, story_ids: set[str]) -> int:
        """Let every text frame holding a rewritten story grow DOWNWARD.

        Translated text usually needs more vertical room than the English
        the frame was drawn for. InDesign marks such a frame overset and
        renders the surplus as nothing — an empty box with no error. Setting
        `AutoSizingType="HeightOnly"` from `TopLeftPoint` has the same
        effect as a person dragging the bottom edge down until it fits.

        `MinimumHeightForAutoSizing` is pinned to the frame's existing drawn
        height, so the frame can only grow, never shrink: without it a
        shorter translation would close up whitespace the designer left
        deliberately.

        Scoped to `story_ids` only — a frame holding untouched English keeps
        the size the designer drew. A frame the designer already set to
        auto-size (any type other than Off) is left exactly alone. Covers
        placed frames on Spreads and MasterSpreads, and anchored frames
        inside stories (`<TextFrame>` nested in a CharacterStyleRange —
        matched by its OWN `ParentStory`, not the story it sits in).

        Height-only by design: width is never changed (that would move the
        frame's right edge into whatever sits beside it), and position is
        never moved. Idempotent — a second pass sees HeightOnly and skips.
        Returns the number of frames changed."""
        changed = 0
        for trees in (self._spreads, self._master_spreads, self._stories):
            for tree in trees.values():
                for tf in tree.iter():
                    if _localname(tf) != "TextFrame":
                        continue
                    if tf.get("ParentStory") not in story_ids:
                        continue
                    if _set_height_only_auto_size(tf):
                        changed += 1
        return changed

    def _flip_justification(self, content) -> None:
        p = content.getparent()
        while p is not None and _localname(p) != "CharacterStyleRange":
            p = p.getparent()
        if p is None:
            return
        para = p.getparent()
        if para is None or _localname(para) != "ParagraphStyleRange":
            return
        key = id(para)
        cached = self._flipped_paragraphs.get(key)
        if cached is not None and cached is para:
            return
        current = self._effective_justification(para)
        flipped = _JUSTIFICATION_FLIP.get(current, current)
        para.set("Justification", flipped)
        self._flipped_paragraphs[key] = para

    def _flip_page_binding(self) -> None:
        """`Resources/Preferences.xml`'s `DocumentPreference/@PageBinding`:
        `LeftToRight` -> `RightToLeft`. This is a document-level setting
        (InDesign doesn't support mixed binding on one document), stored as
        raw bytes like every non-Story entry, so it's patched and written
        straight back into `self._entries` rather than through a parsed
        tree kept for the object's lifetime like Stories are."""
        name = "Resources/Preferences.xml"
        data = self._entries.get(name)
        if not data:
            return
        tree = etree.fromstring(data, parser=_XML_PARSER)
        changed = False
        for el in tree.iter():
            if _localname(el) == "DocumentPreference" and el.get("PageBinding"):
                el.set("PageBinding", "RightToLeft")
                changed = True
        if changed:
            self._entries[name] = etree.tostring(
                tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    def _shrink_point_size(self, content, delta: float, floor: float = 4.0) -> None:
        p = content.getparent()
        while p is not None and _localname(p) != "CharacterStyleRange":
            p = p.getparent()
        if p is None:
            return
        key = id(p)
        cached = self._shrunk_ranges.get(key)
        if cached is not None and cached[0] is p:
            target = cached[1]
        else:
            effective = self._effective_size(p)
            target = max(floor, effective - delta)
            self._shrunk_ranges[key] = (p, target)
        p.set("PointSize", f"{target:.2f}")

    # ---- equation assemblies ------------------------------------------------

    def _is_assembly(self, para) -> bool:
        """Does this paragraph contain a hand-built equation?

        InDesign has no equation editor: an inline fraction is a pen-plotter
        program of ordinary runs — numerator lifted with BaselineShift, a
        blank spacer with `Tracking="-1000"` backing the pen up, a math-face
        `.....` rule drawn underneath, another spacer, the denominator.
        Every distance in that program is relative to the runs' shared size,
        so the parts must be resized together or the alignment breaks.

        The signal is the pen-backup spacer: Tracking at or below
        `_ASSEMBLY_TRACKING` (1/1000 em). Optical tightening lives within
        ±50; the assembly idiom sits near -1000. NOT the presence of a math
        font — a lone inline ½ is just a character with no coupling to its
        neighbours, and using the font as the signal would sweep up ~11% of
        paragraphs instead of the ~3% that actually hold an assembly. Across
        82 real packages every one of 588 hand-built fraction rules sat in a
        paragraph that also carried a spacer.

        Cached per paragraph — several runs in one paragraph each ask."""
        key = id(para)
        cached = self._assembly_cache.get(key)
        if cached is not None and cached[0] is para:
            return cached[1]
        found = False
        for run in para:
            if _localname(run) != "CharacterStyleRange":
                continue
            try:
                if float(run.get("Tracking", "0")) <= _ASSEMBLY_TRACKING:
                    found = True
                    break
            except ValueError:
                continue
        self._assembly_cache[key] = (para, found)
        return found

    def _scale_assembly(self, para, delta: float, floor: float = 4.0) -> None:
        """Resize an equation paragraph as one rigid body — the way a person
        would select the whole thing and shrink it in one go.

        One ratio for the paragraph: `delta` is taken off the LARGEST run's
        effective size (the body size the reduction is meant to act on, and
        the size the program was written for) and `target / base` is then
        applied to EVERY run — prose digits, the math-face glyphs and rule,
        the blank spacers. A flat per-run reduction would give a 12pt run
        73% of itself and a 10pt run 68%, and two runs built to line up
        would drift apart. A single shared ratio makes the operation a
        similarity transform, so every alignment survives exactly.

        Per run: PointSize = own effective size × ratio (a genuine
        superscript stays proportionally smaller rather than being flattened
        to one value); every absolute-point attribute present
        (`_ABSOLUTE_POINT_ATTRS`) × ratio; a numeric `Properties/Leading`
        × ratio (`Auto` left alone). Em-relative (Tracking, KerningValue)
        and percentage (HorizontalScale, VerticalScale) attributes already
        follow the size and are NOT touched — scaling them too would
        double-scale.

        The math-run exemption (`apply` never rewrites a math segment, and
        `_shrink_point_size` is never reached for one) still holds outside
        an assembly. Inside one, the math run is a component of the program
        and keeping it at the old size is precisely what broke the program.

        Floor: the ratio is raised, if needed, so the SMALLEST run lands at
        `floor` — still one ratio, still a similarity transform.
        Idempotent by paragraph identity."""
        key = id(para)
        cached = self._scaled_assemblies.get(key)
        if cached is not None and cached is para:
            return
        self._scaled_assemblies[key] = para

        runs = [r for r in para if _localname(r) == "CharacterStyleRange"]
        if not runs:
            return
        sizes = [self._effective_size(r) for r in runs]
        base = max(sizes)
        if base <= 0:
            return
        ratio = max(floor, base - delta) / base
        smallest = min(sizes)
        if smallest > 0:
            ratio = max(ratio, floor / smallest)
        if ratio >= 1.0:
            return

        for run, size in zip(runs, sizes):
            run.set("PointSize", f"{size * ratio:.2f}")
            # `_shrink_point_size` must never revisit this run on a later
            # pass (a second Content in the same range, say).
            self._shrunk_ranges[id(run)] = (run, size * ratio)
            for attr in _ABSOLUTE_POINT_ATTRS:
                val = run.get(attr)
                if val is None:
                    continue
                try:
                    run.set(attr, _fmt_pt(float(val) * ratio))
                except ValueError:
                    continue  # an enum value (Position="Superscript") — leave it
            for props in run:
                if _localname(props) != "Properties":
                    continue
                for child in props:
                    if _localname(child) != "Leading":
                        continue
                    try:
                        child.text = _fmt_pt(float(child.text or "") * ratio)
                    except ValueError:
                        pass  # `Auto` (type="enumeration")

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
                elif n in self._spreads:
                    data = etree.tostring(
                        self._spreads[n], xml_declaration=True, encoding="UTF-8",
                        standalone=True,
                    )
                elif n in self._master_spreads:
                    data = etree.tostring(
                        self._master_spreads[n], xml_declaration=True, encoding="UTF-8",
                        standalone=True,
                    )
                else:
                    data = self._entries[n]
                z.writestr(n, data)


def _parse_style_defs(styles_xml: bytes | None) -> dict[str, dict]:
    """`Resources/Styles.xml` -> {style Self id: {"PointSize", "BasedOn",
    "Justification", "AppliedFont"}}.

    `AppliedFont` is not an attribute but a `Properties/AppliedFont` child
    element (same shape as on a CharacterStyleRange).

    Most CharacterStyle/ParagraphStyle definitions declare none of these — a
    style only records an attribute when someone explicitly set it in
    InDesign, and only records BasedOn when it was deliberately based on
    another named style rather than the implicit document default. All are
    `None`/absent for the common case, and the caller walks the chain / falls
    back to the document default paragraph style (`$ID/[No paragraph
    style]`, always present with an explicit PointSize) when it runs out of
    chain to walk.
    """
    defs: dict[str, dict] = {}
    if not styles_xml:
        return defs
    tree = etree.fromstring(styles_xml, parser=_XML_PARSER)
    for el in tree.iter():
        if not isinstance(el.tag, str):
            continue
        if etree.QName(el).localname not in ("CharacterStyle", "ParagraphStyle"):
            continue
        self_id = el.get("Self")
        if not self_id:
            continue
        size = el.get("PointSize")
        font = None
        for props in el:
            if _localname(props) != "Properties":
                continue
            for child in props:
                if _localname(child) == "AppliedFont" and child.text:
                    font = child.text
        defs[self_id] = {
            "PointSize": float(size) if size else None,
            "BasedOn": el.get("BasedOn") or None,
            "Justification": el.get("Justification") or None,
            "AppliedFont": font,
        }
    return defs


_DEFAULT_PARAGRAPH_STYLE = "ParagraphStyle/$ID/[No paragraph style]"

# A CharacterStyleRange with Tracking at or below this (1/1000 em) is the
# pen-backup spacer of a hand-built equation — see `IdmlPackage._is_assembly`.
_ASSEMBLY_TRACKING = -100.0

# Run attributes measured in absolute points, which do NOT follow PointSize
# on their own and so must be scaled alongside it inside an assembly. The
# underline/strike-through ones matter because the lower grades draw their
# fraction rule with Underline rather than a math-face `.....` run.
# `Position` is normally an enum (Superscript/Subscript) and is skipped when
# it doesn't parse as a number.
_ABSOLUTE_POINT_ATTRS = (
    "BaselineShift", "Position",
    "UnderlineOffset", "UnderlineWeight",
    "StrikeThroughOffset", "StrikeThroughWeight",
)


def _fmt_pt(v: float) -> str:
    """Point values as real IDML writes them: bare integers where whole,
    otherwise up to 4 decimals with trailing zeros dropped."""
    return f"{v:.4f}".rstrip("0").rstrip(".")


def _paragraph_of(content):
    """The ParagraphStyleRange enclosing a Content node, or None."""
    p = content.getparent()
    while p is not None and _localname(p) != "CharacterStyleRange":
        p = p.getparent()
    if p is None:
        return None
    para = p.getparent()
    if para is None or _localname(para) != "ParagraphStyleRange":
        return None
    return para

# Mirrors the PDF path's own LTR<->RTL align flip (`reassemble/pdf.py`'s
# `_place`: `{"left": "right", "right": "left"}`). Centre, full justification,
# and the binding-relative values (`ToBindingSide`/`AwayFromBindingSide`,
# which already mean "whichever side the spine ends up on") already mean the
# same thing regardless of direction, so they're left out and pass through
# `_JUSTIFICATION_FLIP.get(value, value)` unchanged.
_JUSTIFICATION_FLIP = {
    "LeftAlign": "RightAlign",
    "RightAlign": "LeftAlign",
    "LeftJustified": "RightJustified",
    "RightJustified": "LeftJustified",
}


def _iter_content(tree):
    for el in tree.iter():
        if _localname(el) == "Content":
            yield el


def _content_text(content) -> tuple[str, list[tuple[object, str]]]:
    """A Content node's FULL text, plus its embedded marker children.

    InDesign writes special characters as processing instructions inside
    the run — `<?ACE 7?>` is Indent To Here, `<?ACE 8?>` Right Indent Tab,
    and so on — so `<Content>1.\t<?ACE 7?>Count the dots.</Content>` is one
    run whose text is split around a child. lxml's `.text` only reads up to
    the first child; reading just that stripped a run to its prefix (or to
    nothing, and it was skipped entirely) and the rest of the sentence never
    reached the engine — 36 segments stayed English in one real file.

    Returns `(text, markers)` where `markers` is each child node paired with
    the text it followed — from the previous marker (or the run's start) up
    to itself. That prefix is how `_write_content` puts the marker back.
    """
    text = content.text or ""
    markers: list[tuple[object, str]] = []
    prefix = text
    for child in content:
        markers.append((child, prefix))
        prefix = child.tail or ""
        text += prefix
    return text, markers


def _write_content(content, text: str, markers) -> None:
    """Write `text` into a Content node, re-embedding each marker after the
    same prefix it originally followed.

    `<?ACE 7?>` pins every wrapped line of the paragraph to the x-position
    it sits at, so WHERE it lands matters: a bullet whose marker sat at the
    start (continuation lines flush to the margin) must not have it stranded
    at the end of the translated sentence (continuation lines pushed to
    wherever the sentence reached — a staircase against the right edge).
    In every observed case the prefix is whitespace or a list number
    (`""`, `"1.\t"`), both of which survive translation verbatim, so
    matching it is exact. When the prefix genuinely does not survive, the
    marker goes to its proportional position in the new text rather than
    the end — never the end, which is the failure this exists to prevent.
    """
    if not markers:
        content.text = text
        return
    # Original positions, for the proportional fallback.
    orig_len = sum(len(pfx) for _, pfx in markers) + len(markers[-1][0].tail or "")
    orig_pos, acc = [], 0
    for _, pfx in markers:
        acc += len(pfx)
        orig_pos.append(acc)

    for child in list(content):
        content.remove(child)

    cursor = 0  # where the next prefix search begins in `text`
    cuts: list[int] = []
    for i, (child, pfx) in enumerate(markers):
        rest = text[cursor:]
        if rest.startswith(pfx):
            pos = cursor + len(pfx)
        elif pfx and (found := rest.find(pfx)) != -1:
            pos = cursor + found + len(pfx)
        else:
            pos = round(orig_pos[i] / orig_len * len(text)) if orig_len else 0
            pos = max(cursor, min(pos, len(text)))
        cuts.append(pos)
        cursor = pos

    content.text = text[:cuts[0]]
    for i, (child, _) in enumerate(markers):
        end = cuts[i + 1] if i + 1 < len(cuts) else len(text)
        child.tail = text[cuts[i]:end]
        content.append(child)


def _reflect_transform(transform: str, center_x: float, item_center_x: float) -> str:
    """Move an item to its mirrored position about `center_x` — TRANSLATION
    ONLY: `a b c d` (and `ty`) come back exactly as they went in.

    A negative-determinant `ItemTransform` is precisely how InDesign encodes
    "Flip Horizontal" applied to an item, so negating the transform's linear
    part (`a'=-a, c'=-c`, the textbook affine reflection) does not merely
    reposition the item — it mirrors everything composed inside it, and the
    translated Arabic in a mirrored TextFrame renders backwards. Same
    distinction the PDF path already draws between `mirror_bbox` (position
    only, for translated text) and `mirror_page` (full content flip, for
    baked artwork only).

    The math: with `idml.render._apply`'s convention, a local point `(x, y)`
    lands at `X = a*x + c*y + tx`. Shifting `tx` by `dx` shifts every one of
    the item's points by exactly `dx`, so the item's whole X-extent (and its
    center, `item_center_x`) translates rigidly. Reflecting that extent about
    `center_x` means sending its center to `2*center_x - item_center_x`, i.e.
    `dx = 2*(center_x - item_center_x)` and `tx' = tx + dx`. The extent's
    width is unchanged, so mirroring the center mirrors the whole extent.
    (Check on the axis-aligned case `a=1,b=0,c=0,d=1` with local x in
    `[0, w]`: extent `[tx, tx+w]`, center `tx+w/2`; the new center is
    `tx + 2*(center_x - tx - w/2) + w/2 = 2*center_x - (tx + w/2)` ✓.)
    `item_center_x` comes from `_item_center_x`, which transforms the item's
    own `<PathPointType Anchor>` geometry the same way `render._frame_bbox`
    already does — so this is coordinate-system-general, and correct for a
    rotated frame too (verified against the real 90°-rotated side-tab frame
    from a client file; see the design spec's Math section).

    Only the `tx` token is rewritten; the other five are passed through
    verbatim, so no float round-trip can perturb the item's orientation or
    scale. The fallback path (a transform that isn't exactly six
    whitespace-separated tokens) formats with `:.10g` rather than Python's
    default float repr — `_nums` parses every token as `float`, so a
    whole-number value like `20.0` would otherwise be written as `"20.0"`
    instead of `"20"`, needlessly diverging from how real IDML files write
    these attributes (confirmed against a real client file:
    `ItemTransform="1 0 0 1 0 -391.5"`, bare integers except where a value is
    genuinely fractional). 10 significant digits comfortably exceeds the
    precision InDesign itself writes for these coordinates.
    """
    a, b, c, d, tx, ty = _nums(transform)
    new_tx = tx + 2 * (center_x - item_center_x)

    def fmt(v: float) -> str:
        if v == 0:
            v = 0.0  # -0.0 formats as the string "-0" under :g — normalize
                      # it away rather than let a value formatting-diverge
                      # from the untouched, always-positive-zero case.
        return f"{v:.10g}"

    tokens = transform.split()
    if len(tokens) == 6:
        tokens[4] = fmt(new_tx)
        return " ".join(tokens)
    return " ".join(fmt(v) for v in (a, b, c, d, new_tx, ty))


def _page_ranges(spread_tree) -> list[tuple[float, float]] | None:
    """Each of a Spread's (or MasterSpread's) own Pages' own horizontal
    extent in spread-space, as a `(left, right)` pair per Page. `None` if no
    Page has resolvable geometry — the caller skips mirroring that spread
    entirely rather than guessing.

    A multi-page spread (two facing pages side by side, the common case —
    7 of 9 spreads in a real client file checked here) must NOT be
    collapsed into one combined center: that center sits exactly on the
    seam between the two pages, so mirroring an item about it moves the
    item onto the OTHER page's side entirely — content belonging to one
    page (e.g. a lesson's blue "Activity" page) lands on the facing page
    (a differently-templated "Explore" page), which is what reads as "the
    page backgrounds got swapped." Each item must mirror about the center
    of the specific page it's actually on — see `_mirror_spread`.

    Assumes each Page's own `ItemTransform` is a pure translation
    (`a=1,b=0,c=0,d=1`) — verified true for every Page in a real client
    file checked while writing this (see the design spec). A Page
    transform outside that shape is treated as unresolvable, same as a
    missing Page.
    """
    ranges: list[tuple[float, float]] = []
    for pg in spread_tree.iter():
        if _localname(pg) != "Page":
            continue
        gb = _nums(pg.get("GeometricBounds", ""))
        it = _nums(pg.get("ItemTransform", "1 0 0 1 0 0"))
        if len(gb) != 4 or len(it) != 6:
            continue
        a, b, c, d, tx, ty = it
        if (a, b, c, d) != (1, 0, 0, 1):
            continue
        y1, x1, y2, x2 = gb
        ranges.append((tx + x1, tx + x2))
    return ranges or None


_MIRRORABLE_ELEMENTS = ("TextFrame", "Rectangle", "Polygon", "GraphicLine",
                        "Group", "Oval")


def _item_own_anchors(el) -> list[tuple[float, float]]:
    """Every `<PathPointType Anchor="x y">` belonging to THIS item's own path
    geometry, in the item's own local coordinates.

    Descends the item's subtree but stops at the boundary of any nested
    mirrorable element: a `Group`'s children carry their own geometry in
    their own coordinate space (relative to the group), so folding those
    anchors in with the group's transform would be meaningless. In practice
    that means a leaf item (TextFrame/Rectangle/Polygon/GraphicLine/Oval)
    returns its full outline — exactly what `render._frame_bbox` collects —
    and a `Group`, which carries no path geometry of its own, returns
    nothing.
    """
    out: list[tuple[float, float]] = []

    def walk(node) -> None:
        for child in node:
            name = _localname(child)
            if name in _MIRRORABLE_ELEMENTS:
                continue  # nested item — its geometry is in its own space
            if name == "PathPointType":
                a = _nums(child.get("Anchor", ""))
                if len(a) == 2:
                    out.append((a[0], a[1]))
            walk(child)

    walk(el)
    return out


def _item_center_x(el, m: list[float]) -> float | None:
    """Horizontal midpoint of an item's own outline in SPREAD space, applying
    its current transform `m = [a, b, c, d, tx, ty]` to each of its anchors
    (`X = a*x + c*y + tx`, `render._apply`'s convention — only X matters
    here). `None` when the item has no anchors of its own, i.e. its position
    is unresolvable; the caller then leaves the item alone."""
    anchors = _item_own_anchors(el)
    if not anchors:
        return None
    a, _b, c, _d, tx, _ty = m
    xs = [a * x + c * y + tx for x, y in anchors]
    return (min(xs) + max(xs)) / 2


def _mirror_spread(spread_tree) -> bool:
    """Mirror every top-level TextFrame/Rectangle/Polygon/GraphicLine/Group/
    Oval on this Spread (or MasterSpread — the function itself doesn't care
    which) about its own horizontal center.

    `IdmlPackage.apply()` only calls this on content Spreads, deliberately
    never on MasterSpreads — that's a caller-side scoping decision (shared
    template chrome shouldn't move), not something this function enforces.

    Mirroring is translate-only: an item moves to the mirrored position its
    own geometry implies, but its orientation, scale and content are left
    exactly as they were (see `_reflect_transform` for why flipping the
    linear part is wrong).

    Only DIRECT children of the `<Spread>`/`<MasterSpread>` element are
    touched — a `Group`'s own children keep their transform untouched
    (it's relative to the group, so it stays correct; see the design spec's
    Math section for why recursing into group contents is unnecessary).
    Anchored/inline objects have no top-level ItemTransform of their own, so
    `.iter()` naturally never selects them.

    KNOWN LIMITATION: an item with no `<PathPointType>` geometry of its own
    has no resolvable position, and is left completely untouched rather than
    guessed at. That is normally every `Group` — a group's extent is implicit
    in its children, so grouped artwork stays where it was on a mirrored
    spread (15 of them in the real client file checked). Compounding a
    group's extent from its children's transforms is possible but untested
    against real files, and getting it wrong would displace whole clusters of
    artwork; leaving them put is the safer failure.

    Each item mirrors about the center of the specific PAGE it's on, not a
    combined center for the whole spread — see `_page_ranges` for why a
    multi-page spread's combined center is wrong. An item whose own center
    doesn't fall inside any page's range (should be rare — exactly on a
    page seam, or a malformed/unresolvable page) is left untouched rather
    than guessed at, same failure mode as the no-geometry case above.

    Returns False (no-op, spread left untouched) if the spread's own Page
    geometry can't be resolved — see `_page_ranges`.
    """
    page_ranges = _page_ranges(spread_tree)
    if page_ranges is None:
        return False

    # `spread_tree` (from `etree.fromstring` on a Spreads/*.xml file) is the
    # OUTER `<idPkg:Spread>` wrapper — its localname is also "Spread" (same
    # string, different element), but it carries no `Self` attribute and its
    # actual content lives one level deeper in an inner `<Spread Self="...">`.
    # Matching on `spread_tree` itself would silently iterate that wrapper's
    # one child (the inner Spread element) instead of the TextFrames/
    # Rectangles/etc that are the inner element's own children — so this
    # searches descendants for the first Spread/MasterSpread that actually
    # has a `Self`, which works whether the caller passes the outer wrapper
    # or (in a test fixture) the inner element directly.
    root = next((e for e in spread_tree.iter()
                 if _localname(e) in ("Spread", "MasterSpread") and e.get("Self")),
                None)
    if root is None:
        return False

    for el in root:
        if _localname(el) not in _MIRRORABLE_ELEMENTS:
            continue
        transform = el.get("ItemTransform")
        if not transform:
            continue
        nums = _nums(transform)
        if len(nums) != 6:
            continue  # malformed — leave this one item untouched, keep going
        item_center_x = _item_center_x(el, nums)
        if item_center_x is None:
            continue  # no own geometry (typically a Group) — leave it be
        page = next((r for r in page_ranges if r[0] <= item_center_x <= r[1]), None)
        if page is None:
            continue  # doesn't resolve to any single page — leave it be
        page_center_x = (page[0] + page[1]) / 2
        el.set("ItemTransform", _reflect_transform(transform, page_center_x, item_center_x))
    return True


def _story_self(tree) -> str:
    """The inner `<Story Self="...">` id of a parsed Stories/*.xml — what a
    TextFrame's `ParentStory` refers to."""
    for el in tree.iter():
        if _localname(el) == "Story" and el.get("Self"):
            return el.get("Self")
    return ""


def _frame_height(tf) -> float | None:
    """A text frame's drawn height in its OWN local coordinates — the extent
    of its `<PathPointType Anchor>` outline along y. Local, not spread
    space, because that is the axis HeightOnly auto-sizing grows along
    (a 90°-rotated frame still grows along its own height). `None` when
    the frame carries no geometry of its own."""
    anchors = _item_own_anchors(tf)
    if not anchors:
        return None
    ys = [y for _x, y in anchors]
    return max(ys) - min(ys)


def _set_height_only_auto_size(tf) -> bool:
    """Set HeightOnly auto-sizing (from the top-left, floor = current height)
    on one TextFrame. Creates `<TextFramePreference>` when the frame has
    none. Leaves a frame already auto-sizing in any way untouched. Returns
    whether the frame was changed."""
    height = _frame_height(tf)
    if height is None:
        return False
    tfp = next((c for c in tf if _localname(c) == "TextFramePreference"), None)
    if tfp is None:
        tfp = etree.SubElement(tf, "TextFramePreference")
    elif (tfp.get("AutoSizingType") or "Off") != "Off":
        return False
    tfp.set("AutoSizingType", "HeightOnly")
    tfp.set("AutoSizingReferencePoint", "TopLeftPoint")
    tfp.set("UseMinimumHeightForAutoSizing", "true")
    tfp.set("MinimumHeightForAutoSizing", _fmt_pt(height))
    return True


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


def _set_story_direction(tree, direction: str) -> None:
    """Set `<StoryPreference StoryDirection="...">` on a story's root element.

    `direction` is an IDML enum value (`RightToLeftDirection` /
    `LeftToRightDirection`), not our own `lang.direction` — the caller maps
    that. A story with no StoryPreference at all (never observed in a real
    export, but IDML doesn't require the element) is left alone rather than
    fabricating one from scratch with guessed sibling attributes.
    """
    root = tree.getroot() if hasattr(tree, "getroot") else tree
    for el in root.iter():
        if _localname(el) == "StoryPreference":
            el.set("StoryDirection", direction)


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
