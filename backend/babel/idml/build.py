"""PDF → IDML. The missing initiation point.

`IDML_WORKFLOW.md` says the production path is blocked on a client-supplied
`.idml`/`.indd`. This module removes that block: it turns a plain PDF into a
valid IDML package, so a PDF-only client still lands in the high-fidelity
path (`translate_idml` → InDesign reflow → PDF + INDD).

Fidelity strategy — **graphics stay raster, text becomes live frames**:

1. Every text glyph is redacted from a scratch copy of the page, leaving only
   diagrams, rules, tables and images.
2. That graphics-only page is rendered to PNG and placed as a full-page
   background rectangle.
3. Each source line becomes its own InDesign TextFrame, positioned at the
   original bbox, on top of the background.

The result: charts and worksheets look identical, while every word is live,
editable, reflowable text that InDesign re-lays-out when Spanish runs longer.

Coordinates (verified empirically against Scribus 1.7.3 and InDesign output):
a spread is centred on x=0, so for a SINGLE-page spread the page spans
[-W/2, +W/2] and a PDF point (x, y) lands at (x - W/2, y - H/2) in spread
space. Do not copy transforms from a facing-page (2-up) reference file — those
put pages at x=-W and x=0 instead, and readers derive the page origin from the
spread's page count, not from the page's own ItemTransform X.
"""

from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass
from xml.sax.saxutils import escape, quoteattr

import fitz

from babel.ingest.pdf import extract_lines
from babel.models import Line, Segment

IDML_MIME = "application/vnd.adobe.indesign-idml-package"
DOM_VERSION = "10.0"
PKG_NS = "http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging"
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'

# Page items must name a layer that exists in designmap.xml; a layerless or
# dangling-style item is silently discarded by IDML readers.
LAYER_ID = "layer1"
DEFAULT_FONT = "Minion Pro"
BACKGROUND_DPI = 200


class IdGen:
    def __init__(self) -> None:
        self._n = 0

    def __call__(self, prefix: str = "u") -> str:
        self._n += 1
        return f"{prefix}{self._n:05d}"


@dataclass
class FrameSpec:
    """One text frame to emit: where it goes and what it says."""

    bbox: tuple[float, float, float, float]
    text: str
    size: float = 10.0
    bold: bool = False
    italic: bool = False
    opaque: bool = False  # paint a white box behind it (masks burned-in text)
    # Knockout text (a white problem number on a dark disc) must stay white, or
    # it prints black-on-black and collides with the artwork behind it.
    knockout: bool = False
    # How many lines the source occupied — the editorial contract for the
    # target, and what the preview measures overflow against.
    line_count: int = 1


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------

def _path_geometry(x0: float, y0: float, x1: float, y1: float) -> str:
    """Frame outline. Points are frame-local, so always centred on 0,0."""
    w, h = (x1 - x0) / 2.0, (y1 - y0) / 2.0
    pts = [(-w, -h), (-w, h), (w, h), (w, -h)]
    body = "".join(
        f'<PathPointType Anchor="{x:.4f} {y:.4f}" '
        f'LeftDirection="{x:.4f} {y:.4f}" RightDirection="{x:.4f} {y:.4f}"/>'
        for x, y in pts
    )
    return (
        '<Properties><PathGeometry><GeometryPathType PathOpen="false">'
        f"<PathPointArray>{body}</PathPointArray>"
        "</GeometryPathType></PathGeometry></Properties>"
    )


# --------------------------------------------------------------------------
# XML parts
# --------------------------------------------------------------------------

def _story_xml(story_id: str, spec: FrameSpec, font: str) -> str:
    """One Story per frame; one paragraph per source line (editorial rule:
    the translated block keeps the same number of lines as the source)."""
    style = font
    if spec.bold and spec.italic:
        style = font
    paragraphs = spec.text.split("\n") or [""]
    body = []
    for para in paragraphs:
        body.append(
            '<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/$ID/NormalParagraphStyle">'
            '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            f'PointSize="{max(4.0, min(72.0, spec.size)):.2f}" '
            f'FillColor="{"Color/Paper" if spec.knockout else "Color/Black"}"'
            + (' FontStyle="Bold"' if spec.bold and not spec.italic else "")
            + (' FontStyle="Italic"' if spec.italic and not spec.bold else "")
            + (' FontStyle="Bold Italic"' if spec.italic and spec.bold else "")
            + ">"
            f'<Properties><AppliedFont type="string">{escape(style)}</AppliedFont></Properties>'
            f"<Content>{escape(para)}</Content>"
            "</CharacterStyleRange></ParagraphStyleRange>"
        )
    return (
        XML_HEAD
        + f'<idPkg:Story xmlns:idPkg="{PKG_NS}" DOMVersion="{DOM_VERSION}">'
        + f'<Story Self="{story_id}" AppliedTOCStyle="n" TrackChanges="false" '
          'StoryTitle="$ID/" AppliedNamedGrid="n">'
        + '<StoryPreference OpticalMarginAlignment="false" OpticalMarginSize="12" '
          'FrameType="TextFrameType" StoryOrientation="Horizontal" '
          'StoryDirection="LeftToRightDirection"/>'
        + "".join(body)
        + "</Story></idPkg:Story>"
    )


def _image_rect(rect_id: str, bbox, cx: float, cy: float, png: str) -> str:
    x0, y0, x1, y1 = bbox
    tx, ty = (x0 + x1) / 2.0 - cx, (y0 + y1) / 2.0 - cy
    bw, bh = x1 - x0, y1 - y0
    uri = "file:///" + os.path.abspath(png).replace("\\", "/").lstrip("/")
    return (
        f'<Rectangle Self="{rect_id}" ItemTransform="1 0 0 1 {tx:.4f} {ty:.4f}" '
        f'ContentType="GraphicType" ItemLayer="{LAYER_ID}" Locked="false" '
        'Visible="true" Name="$ID/" '
        'AppliedObjectStyle="ObjectStyle/$ID/[Normal Graphics Frame]" StrokeWeight="0">'
        + _path_geometry(x0, y0, x1, y1)
        + f'<Image Self="{rect_id}_img" ItemTransform="1 0 0 1 {-bw / 2:.4f} {-bh / 2:.4f}" '
          'ImageTypeName="$ID/Portable Network Graphics (PNG)" '
          f'ActualPpi="{BACKGROUND_DPI} {BACKGROUND_DPI}" '
          f'EffectivePpi="{BACKGROUND_DPI} {BACKGROUND_DPI}">'
          "<Properties><Profile type=\"string\">$ID/Embedded</Profile>"
          f'<GraphicBounds Left="0" Top="0" Right="{bw:.4f}" Bottom="{bh:.4f}"/>'
          "</Properties>"
          f'<Link Self="{rect_id}_link" LinkResourceURI={quoteattr(uri)} '
          'StoredState="Normal" LinkClientID="257" LinkResourceFormat="$ID/PNG"/>'
          "</Image></Rectangle>"
    )


def _spread_xml(spread_id: str, page_no: int, width: float, height: float,
                frames: list[tuple[str, str, FrameSpec]],
                background: str | None, ids: IdGen,
                equations: list[tuple] | None = None) -> str:
    cx, cy = width / 2.0, height / 2.0
    out = [
        XML_HEAD,
        f'<idPkg:Spread xmlns:idPkg="{PKG_NS}" DOMVersion="{DOM_VERSION}">',
        f'<Spread Self="{spread_id}" FlattenerOverride="Default" PageCount="1" '
        'BindingLocation="0" AllowPageShuffle="true" ItemTransform="1 0 0 1 0 0" '
        'ShowMasterItems="true" PageTransitionType="None" '
        'PageTransitionDirection="NotApplicable" PageTransitionDuration="Medium">',
        '<FlattenerPreference LineArtAndTextResolution="300" '
        'GradientAndMeshResolution="150" ClipComplexRegions="false" '
        'ConvertAllStrokesToOutlines="false" ConvertAllTextToOutlines="false"/>',
        f'<Page Self="{spread_id}_page" Name="{page_no}" AppliedMaster="master" '
        f'GeometricBounds="0 0 {height:.4f} {width:.4f}" '
        f'ItemTransform="1 0 0 1 {-cx:.4f} {-cy:.4f}" OverrideList="" TabOrder="" '
        'GridStartingPoint="TopOutside" UseMasterGrid="true" '
        'MasterPageTransform="1 0 0 1 0 0" LayoutRule="Off" OptionalPage="false"/>',
    ]

    # background first so text frames stack above it
    if background:
        out.append(_image_rect(ids("rect"), (0.0, 0.0, width, height), cx, cy, background))

    # Equations go in as pictures of the original, at the original position:
    # their extracted text is corrupt, and math must never be translated.
    for bbox, png in (equations or []):
        out.append(_image_rect(ids("rect"), bbox, cx, cy, png))

    for frame_id, story_id, spec in frames:
        x0, y0, x1, y1 = spec.bbox
        tx, ty = (x0 + x1) / 2.0 - cx, (y0 + y1) / 2.0 - cy
        fill = "Color/Paper" if spec.opaque else "Swatch/None"
        out.append(
            f'<TextFrame Self="{frame_id}" ParentStory="{story_id}" '
            'PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" '
            f'ItemLayer="{LAYER_ID}" Locked="false" Visible="true" Name="$ID/" '
            f'FillColor="{fill}" '
            'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
            f'ItemTransform="1 0 0 1 {tx:.4f} {ty:.4f}">'
            + _path_geometry(x0, y0, x1, y1)
            # Grow downward rather than overset: Spanish is longer than the
            # English the box was measured from, and an overset frame silently
            # hides text in InDesign.
            + '<TextFramePreference TextColumnCount="1" TextColumnGutter="0" '
              'VerticalJustification="TopAlign" '
              'AutoSizingType="HeightOnly" '
              'AutoSizingReferencePoint="TopLeftPoint" '
              'UseMinimumHeightForAutoSizing="true" '
              'UseNoLineBreaksForAutoSizing="false">'
              '<Properties><InsetSpacing type="list">'
              '<ListItem type="unit">0</ListItem><ListItem type="unit">0</ListItem>'
              '<ListItem type="unit">0</ListItem><ListItem type="unit">0</ListItem>'
              "</InsetSpacing></Properties></TextFramePreference>"
            + "</TextFrame>"
        )
    out.append("</Spread></idPkg:Spread>")
    return "".join(out)


def _master_spread_xml(width: float, height: float) -> str:
    cx, cy = width / 2.0, height / 2.0
    return (
        XML_HEAD
        + f'<idPkg:MasterSpread xmlns:idPkg="{PKG_NS}" DOMVersion="{DOM_VERSION}">'
        + '<MasterSpread Self="master" Name="A-Master" NamePrefix="A" '
          'BaseName="Master" PageCount="1" ItemTransform="1 0 0 1 0 0" '
          'ShowMasterItems="true">'
        + f'<Page Self="master_page" Name="A" GeometricBounds="0 0 {height:.4f} {width:.4f}" '
          f'ItemTransform="1 0 0 1 {-cx:.4f} {-cy:.4f}" OverrideList="" TabOrder="" '
          'GridStartingPoint="TopOutside" UseMasterGrid="true"/>'
        + "</MasterSpread></idPkg:MasterSpread>"
    )


def _resources(font: str) -> dict[str, str]:
    graphic = (
        XML_HEAD
        + f'<idPkg:Graphic xmlns:idPkg="{PKG_NS}" DOMVersion="{DOM_VERSION}">'
        + '<Color Self="Color/Black" Model="Process" Space="CMYK" '
          'ColorValue="0 0 0 100" ColorOverride="Normal" Name="Black"/>'
        + '<Color Self="Color/Paper" Model="Process" Space="CMYK" ColorValue="0 0 0 0" '
          'ColorOverride="Specialpaper" Name="Paper"/>'
        + '<Swatch Self="Swatch/None" Name="None" ColorEditable="false" '
          'ColorRemovable="false"/>'
        + '<StrokeStyle Self="StrokeStyle/$ID/Solid" Name="$ID/Solid"/>'
        + "</idPkg:Graphic>"
    )
    fonts = (
        XML_HEAD
        + f'<idPkg:Fonts xmlns:idPkg="{PKG_NS}" DOMVersion="{DOM_VERSION}">'
        + f'<FontFamily Self="fontfamily1" Name={quoteattr(font)}>'
        + "".join(
            f'<Font Self="fontfamily1font{i}" FontFamily={quoteattr(font)} '
            f'Name={quoteattr(font + " " + style)} '
            f'PostScriptName={quoteattr(font.replace(" ", "") + "-" + style.replace(" ", ""))} '
            f'Status="Installed" FontStyleName={quoteattr(style)} FontType="OpenTypeCFF"/>'
            for i, style in enumerate(("Regular", "Bold", "Italic", "Bold Italic"), start=1)
        )
        + "</FontFamily></idPkg:Fonts>"
    )
    styles = (
        XML_HEAD
        + f'<idPkg:Styles xmlns:idPkg="{PKG_NS}" DOMVersion="{DOM_VERSION}">'
        + '<RootCharacterStyleGroup Self="charstyles">'
          '<CharacterStyle Self="CharacterStyle/$ID/[No character style]" '
          'Name="$ID/[No character style]"/></RootCharacterStyleGroup>'
        + '<RootParagraphStyleGroup Self="parastyles">'
          '<ParagraphStyle Self="ParagraphStyle/$ID/NormalParagraphStyle" '
          'Name="$ID/NormalParagraphStyle" FillColor="Color/Black">'
          f'<Properties><AppliedFont type="string">{escape(font)}</AppliedFont></Properties>'
          "</ParagraphStyle></RootParagraphStyleGroup>"
        + '<RootObjectStyleGroup Self="objstyles">'
          '<ObjectStyle Self="ObjectStyle/$ID/[None]" Name="$ID/[None]" '
          'FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0"/>'
          '<ObjectStyle Self="ObjectStyle/$ID/[Normal Text Frame]" '
          'Name="$ID/[Normal Text Frame]" FillColor="Swatch/None" '
          'StrokeColor="Swatch/None" StrokeWeight="0" '
          'AppliedParagraphStyle="ParagraphStyle/$ID/NormalParagraphStyle"/>'
          '<ObjectStyle Self="ObjectStyle/$ID/[Normal Graphics Frame]" '
          'Name="$ID/[Normal Graphics Frame]" FillColor="Swatch/None" '
          'StrokeColor="Swatch/None" StrokeWeight="0"/>'
          "</RootObjectStyleGroup>"
        + '<RootTableStyleGroup Self="tablestyles"/><RootCellStyleGroup Self="cellstyles"/>'
        + "</idPkg:Styles>"
    )
    prefs = (
        XML_HEAD
        + f'<idPkg:Preferences xmlns:idPkg="{PKG_NS}" DOMVersion="{DOM_VERSION}">'
        + '<ViewPreference HorizontalMeasurementUnits="Points" '
          'VerticalMeasurementUnits="Points" RulerOrigin="PageOrigin"/>'
        + "<TransparencyPreference/></idPkg:Preferences>"
    )
    return {
        "Resources/Graphic.xml": graphic,
        "Resources/Fonts.xml": fonts,
        "Resources/Styles.xml": styles,
        "Resources/Preferences.xml": prefs,
    }


def _static() -> dict[str, str]:
    return {
        "META-INF/container.xml": (
            XML_HEAD
            + '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" '
              'version="1.0"><rootfiles><rootfile full-path="designmap.xml" '
              'media-type="text/xml"/></rootfiles></container>'
        ),
        "META-INF/metadata.xml": (
            XML_HEAD
            + '<?aid style="50" type="document" readerVersion="6.0" featureSet="257" ?>'
              '<Metadata xmlns:x="adobe:ns:meta/"><x:xmpmeta/></Metadata>'
        ),
        "XML/BackingStory.xml": (
            XML_HEAD
            + f'<idPkg:BackingStory xmlns:idPkg="{PKG_NS}" DOMVersion="{DOM_VERSION}">'
              '<XmlStory Self="backingstory" AppliedTOCStyle="n" TrackChanges="false" '
              'StoryTitle="$ID/" AppliedNamedGrid="n"/></idPkg:BackingStory>'
        ),
        "XML/Tags.xml": (
            XML_HEAD
            + f'<idPkg:Tags xmlns:idPkg="{PKG_NS}" DOMVersion="{DOM_VERSION}">'
              '<XMLTag Self="XMLTag/Root" Name="Root"/></idPkg:Tags>'
        ),
    }


def _designmap(spreads: list[str], stories: list[str], story_ids: list[str]) -> str:
    parts = [
        XML_HEAD,
        '<?aid style="50" type="document" readerVersion="6.0" featureSet="257" '
        'product="10.0(70)" ?>\n',
        f'<Document xmlns:idPkg="{PKG_NS}" DOMVersion="{DOM_VERSION}" Self="doc" '
        f'StoryList={quoteattr(" ".join(story_ids))} ActiveLayer="{LAYER_ID}" '
        'ZeroPoint="0 0">',
        f'<Layer Self="{LAYER_ID}" Name="Layer 1" Visible="true" Locked="false" '
        'IgnoreWrap="false" ShowGuides="true" LockGuides="false" UI="true" '
        'Expendable="true" Printable="true"/>',
        '<idPkg:Graphic src="Resources/Graphic.xml"/>',
        '<idPkg:Fonts src="Resources/Fonts.xml"/>',
        '<idPkg:Styles src="Resources/Styles.xml"/>',
        '<idPkg:Preferences src="Resources/Preferences.xml"/>',
        '<idPkg:MasterSpread src="MasterSpreads/MasterSpread_master.xml"/>',
    ]
    parts += [f'<idPkg:Spread src={quoteattr(s)}/>' for s in spreads]
    parts += [f'<idPkg:Story src={quoteattr(s)}/>' for s in stories]
    parts.append('<idPkg:BackingStory src="XML/BackingStory.xml"/>')
    parts.append("</Document>")
    return "".join(parts)


# --------------------------------------------------------------------------
# background rendering
# --------------------------------------------------------------------------

def render_backgrounds(src_pdf: str, asset_dir: str, dpi: int = BACKGROUND_DPI) -> dict[int, str]:
    """Render each page with all live text removed.

    What survives is exactly what we cannot turn into editable text: diagrams,
    grids, rules, tables and photos. Those become the page background so the
    IDML looks like the source while the words stay live.
    """
    os.makedirs(asset_dir, exist_ok=True)
    doc = fitz.open(src_pdf)
    out: dict[int, str] = {}
    try:
        for pno in range(doc.page_count):
            page = doc.load_page(pno)
            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") == 0:
                    page.add_redact_annot(fitz.Rect(block["bbox"]))
            # keep images and vector art, drop only the glyphs
            page.apply_redactions(
                images=fitz.PDF_REDACT_IMAGE_NONE,
                graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                text=fitz.PDF_REDACT_TEXT_REMOVE,
            )
            path = os.path.join(asset_dir, f"page_{pno + 1:04d}.png")
            page.get_pixmap(dpi=dpi).save(path)
            out[pno] = path
    finally:
        doc.close()
    return out


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

def _covered(bbox, zones: list[tuple[float, float, float, float]],
             overlap: float = 0.6) -> bool:
    """True when `bbox` lies mostly inside one of `zones`."""
    x0, y0, x1, y1 = bbox
    area = max((x1 - x0) * (y1 - y0), 1e-6)
    for zx0, zy0, zx1, zy1 in zones:
        ix = max(0.0, min(x1, zx1) - max(x0, zx0))
        iy = max(0.0, min(y1, zy1) - max(y0, zy0))
        if ix * iy >= area * overlap:
            return True
    return False


def specs_from_lines(lines: list[Line],
                     skip_zones: dict[int, list] | None = None) -> dict[int, list[FrameSpec]]:
    """Frames for the source text, grouped into their original blocks.

    One frame per *visual line* is what a naive conversion does, and it is
    wrong for translation: Spanish runs 20-30% longer than English, so every
    line overflows its own tight box and prints over the line beside it. A
    paragraph gets one frame spanning the block it came from, so the target
    text re-wraps inside the same column the source occupied — which is also
    what keeps the page looking like the original.

    `skip_zones` are areas already handled another way — equation regions,
    which are placed as images rather than as text, because the extracted text
    for them is corrupt ((-5^5)^2 comes out of the PDF as "(255)2") and because
    math must never reach a translation engine.
    """
    by_page: dict[int, list[FrameSpec]] = {}
    groups: dict[tuple[int, int], list[tuple[Line, list]]] = {}
    order: list[tuple[int, int]] = []

    for ln in lines:
        if not ln.raw_text.strip():
            continue
        spans = [s for s in ln.spans if s.text.strip()]
        zones = (skip_zones or {}).get(ln.page)
        if zones:
            # Test each span, not the line. A worksheet line often holds the
            # problem-number badge *and* the expression; skipping by line either
            # loses the badge or double-draws the equation over its own image.
            spans = [s for s in spans if not _covered(s.bbox, zones)]
        if not spans:
            continue

        # Knockout numerals sit on top of artwork and must stay their own frame,
        # never merged into the paragraph beside them.
        knockout = _is_knockout(max(spans, key=lambda s: s.bbox[2] - s.bbox[0]).color)
        key = (ln.page, -id(ln) if knockout else ln.block)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append((ln, spans))

    for key in order:
        for members in _paragraph_runs(groups[key]):
            _emit(members, by_page)
    return by_page


def _paragraph_runs(members: list[tuple[Line, list]]) -> list[list[tuple[Line, list]]]:
    """Split a PyMuPDF block into runs that are genuinely one paragraph.

    A block is not always a paragraph. Table rows land in one block, so the
    header cells "Hours" and "Number of People" — side by side, not stacked —
    would merge into a single frame and print one above the other. Two lines
    only continue each other when they overlap horizontally (same column) and
    sit on consecutive baselines.

    Rotated text (an axis label) is left alone: its box is taller than it is
    wide, and wrapping it as prose spells the word downwards, one letter to a
    line.
    """
    runs: list[list[tuple[Line, list]]] = []
    for line, spans in members:
        box = _span_bbox(spans)
        rotated = (box[3] - box[1]) > (box[2] - box[0]) * 1.5 and len(line.raw_text.strip()) > 2
        if rotated or not runs:
            runs.append([(line, spans)])
            continue

        prev_line, prev_spans = runs[-1][-1]
        prev = _span_bbox(prev_spans)
        overlap = min(box[2], prev[2]) - max(box[0], prev[0])
        width = min(box[2] - box[0], prev[2] - prev[0]) or 1.0
        gap = box[1] - prev[3]
        height = max(prev[3] - prev[1], 1.0)

        if overlap >= width * 0.4 and -height <= gap <= height * 1.2:
            runs[-1].append((line, spans))
        else:
            runs.append([(line, spans)])
    return runs


def _join_spans(spans: list) -> str:
    """Concatenate a line's spans, restoring gaps that were positional.

    An axis scale is drawn as separate spans spaced across the page, not as one
    string with spaces in it. Joining them naively gives "2345678910 11"; the
    gap between spans has to become whitespace to read as a scale again.
    """
    ordered = sorted(spans, key=lambda s: s.bbox[0])
    out: list[str] = []
    for i, span in enumerate(ordered):
        if i:
            gap = span.bbox[0] - ordered[i - 1].bbox[2]
            if gap > max(1.0, span.size * 0.22) and not out[-1].endswith(" "):
                out.append(" " * max(1, int(gap / max(span.size * 0.5, 1.0))))
        out.append(span.text)
    return "".join(out).strip()


def _span_bbox(spans: list) -> tuple[float, float, float, float]:
    return (
        min(s.bbox[0] for s in spans), min(s.bbox[1] for s in spans),
        max(s.bbox[2] for s in spans), max(s.bbox[3] for s in spans),
    )


def _emit(members: list[tuple[Line, list]], by_page: dict[int, list[FrameSpec]]) -> None:
    if True:
        page = members[0][0].page
        all_spans = [s for _, spans in members for s in spans]
        rows = [_join_spans(spans) for _, spans in members]
        text = "\n".join(r for r in rows if r)
        if not text:
            return

        bbox = _span_bbox(all_spans)
        dom = max(all_spans, key=lambda s: s.bbox[2] - s.bbox[0])
        first = members[0][0]
        by_page.setdefault(page, []).append(
            FrameSpec(bbox=bbox, text=text, size=dom.size or 10.0,
                      bold=first.is_bold, italic=first.is_italic,
                      knockout=_is_knockout(dom.color),
                      line_count=len(rows))
        )


def _is_knockout(colour: int) -> bool:
    """Near-white text — only legible over dark artwork, so keep it white."""
    r, g, b = (int(colour) >> 16) & 0xFF, (int(colour) >> 8) & 0xFF, int(colour) & 0xFF
    return min(r, g, b) >= 0xF0


def specs_from_segments(segments: list[Segment]) -> dict[int, list[FrameSpec]]:
    """Frames carrying translated text.

    Editorial rule from the client: a source block of N lines must come back as
    N lines. A segment remembers the line boxes it was merged from, so the
    target is split back across the same number of lines and each frame keeps
    its original box.
    """
    by_page: dict[int, list[FrameSpec]] = {}
    for seg in segments:
        text = seg.restored_target().strip() if seg.target else seg.restored_source().strip()
        if not text:
            continue
        boxes = seg.bboxes or [seg.bbox]
        if len(boxes) == 1:
            by_page.setdefault(seg.page, []).append(
                FrameSpec(bbox=tuple(boxes[0]), text=text, size=seg.size or 10.0,
                          bold=seg.bold, italic=seg.italic)
            )
            continue
        # merged paragraph: one frame over the union, N paragraphs inside, so
        # InDesign keeps the same line count without us guessing break points
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes)
        y1 = max(b[3] for b in boxes)
        by_page.setdefault(seg.page, []).append(
            FrameSpec(bbox=(x0, y0, x1, y1), text=text, size=seg.size or 10.0,
                      bold=seg.bold, italic=seg.italic)
        )
    return by_page


def build_idml(
    src_pdf: str,
    out_path: str,
    segments: list[Segment] | None = None,
    font: str = DEFAULT_FONT,
    backgrounds: bool = True,
    asset_dir: str | None = None,
    extra_frames: dict[int, list[FrameSpec]] | None = None,
    equation_images: dict[int, list[tuple]] | None = None,
) -> dict:
    """Convert `src_pdf` into an IDML package at `out_path`.

    `segments` — if given, their (translated) text is written instead of the
    source text, so this doubles as the ES-IDML writer for a PDF-origin job.
    `extra_frames` — extra per-page frames, e.g. OCR'd text recovered from
    inside images (see `ingest.ocr`).
    """
    doc = fitz.open(src_pdf)
    page_sizes = {p.number: (p.rect.width, p.rect.height) for p in doc}
    doc.close()

    skip_zones = {
        pno: [bbox for bbox, _ in items]
        for pno, items in (equation_images or {}).items()
    }
    if segments is not None:
        by_page = specs_from_segments(segments)
    else:
        by_page = specs_from_lines(extract_lines(src_pdf), skip_zones=skip_zones)

    if extra_frames:
        for pno, specs in extra_frames.items():
            by_page.setdefault(pno, []).extend(specs)

    asset_dir = asset_dir or os.path.join(
        os.path.dirname(os.path.abspath(out_path)),
        os.path.splitext(os.path.basename(out_path))[0] + "_assets",
    )
    bg = render_backgrounds(src_pdf, asset_dir) if backgrounds else {}

    ids = IdGen()
    files: dict[str, str] = {}
    spread_files: list[str] = []
    story_files: list[str] = []
    story_ids: list[str] = []

    for pno in sorted(page_sizes):
        width, height = page_sizes[pno]
        spread_id = ids("spread")
        frames: list[tuple[str, str, FrameSpec]] = []
        for spec in by_page.get(pno, []):
            story_id, frame_id = ids("story"), ids("frame")
            frames.append((frame_id, story_id, spec))
            name = f"Stories/Story_{story_id}.xml"
            files[name] = _story_xml(story_id, spec, font)
            story_files.append(name)
            story_ids.append(story_id)

        name = f"Spreads/Spread_{spread_id}.xml"
        files[name] = _spread_xml(spread_id, pno + 1, width, height, frames,
                                  bg.get(pno), ids,
                                  (equation_images or {}).get(pno))
        spread_files.append(name)

    first = page_sizes.get(0, (612.0, 792.0))
    files["MasterSpreads/MasterSpread_master.xml"] = _master_spread_xml(*first)
    files.update(_resources(font))
    files.update(_static())
    files["designmap.xml"] = _designmap(spread_files, story_files, story_ids)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        # IDML, like EPUB/ODF, requires `mimetype` first and uncompressed.
        z.writestr(zipfile.ZipInfo("mimetype"), IDML_MIME,
                   compress_type=zipfile.ZIP_STORED)
        for name in ["designmap.xml", *sorted(k for k in files if k != "designmap.xml")]:
            z.writestr(name, files[name])

    return {
        "output": out_path,
        "pages": len(page_sizes),
        "frames": len(story_ids),
        "backgrounds": len(bg),
        "asset_dir": asset_dir if bg else None,
    }
