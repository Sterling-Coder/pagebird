"""Direction for DOCX and PPTX. Imported only for a right-to-left target, so an
LTR document is written exactly as the adapters leave it. XLSX gets its text
and nothing else (no sheet is switched to `rightToLeft` in this release).

Alignment was measured in the applications themselves (Word and PowerPoint
via COM, exported to PDF, text positions read back), because the two disagree:

* Word: `w:bidi` makes a paragraph right-to-left, and inside such a paragraph
  `w:jc` left/right name the *leading/trailing* edge — `left` renders on the
  right, like `start`. So setting `w:bidi` alone mirrors the paragraph and
  `w:jc` is left as it is. Runs get `w:rtl`, the complex-script font slot
  (`w:rFonts/@w:cs`) and `w:lang/@w:bidi`; tables get `w:bidiVisual` so their
  columns run right to left.
* PowerPoint: `a:pPr/@algn` is *physical* — `rtl="1"` with no `algn` still
  renders on the left. So the alignment a paragraph actually renders with
  (its own, or inherited from the layout and master) is resolved and `l`/`r`
  swapped; centred and justified text stay so. Runs get `lang` and the
  complex-script typeface `a:cs`.

Children are inserted in schema order: Office refuses a file whose `w:rPr` or
`a:rPr` children are out of sequence.
"""

from __future__ import annotations

from functools import lru_cache

from lxml import etree

from pagebirdy import fonts as pagebirdy_fonts

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

_LANG_TAG = {"ar": "ar-SA", "he": "he-IL", "fa": "fa-IR", "ur": "ur-PK"}
_SWAP = {"l": "r", "r": "l"}

# CT_PPr and CT_RPr child order (ECMA-376 §17.3.1.26, §17.3.2.28).
_PPR_ORDER = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl",
              "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens",
              "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN",
              "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing",
              "mirrorIndents", "suppressOverlap", "jc", "textDirection", "textAlignment",
              "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange"]
_RPR_ORDER = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike",
              "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish",
              "webHidden", "color", "spacing", "w", "kern", "position", "sz", "szCs", "highlight",
              "u", "effect", "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang",
              "eastAsianLayout", "specVanish", "oMath"]
# CT_TextCharacterProperties: what must follow `a:cs`.
_ARPR_AFTER_CS = {A + "sym", A + "hlinkClick", A + "hlinkMouseOver", A + "rtl", A + "extLst"}


def _child(parent, ns: str, name: str, order: list[str]):
    """`parent`'s `name` child, created in schema position if absent."""
    found = parent.find(ns + name)
    if found is not None:
        return found
    el = etree.SubElement(parent, ns + name)
    parent.remove(el)
    rank = order.index(name)
    for i, sibling in enumerate(parent):
        qname = etree.QName(sibling)
        # A sibling outside the known sequence — a w14 text effect, any other
        # extension — and the tracked-change record (`rPrChange`/`pPrChange`,
        # which must be last) all rank after every element we insert.
        if (qname.namespace != ns.strip("{}") or qname.localname not in order
                or qname.localname.endswith("Change")
                or order.index(qname.localname) > rank):
            parent.insert(i, el)
            return el
    parent.append(el)
    return el


@lru_cache(maxsize=16)
def face_name(code: str) -> str:
    """The family name the complex-script slot should name."""
    from PIL import ImageFont

    from pagebirdy import languages

    lang = languages.get(code)
    if lang.idml_font:
        return lang.idml_font
    path = pagebirdy_fonts.resolve(tuple(lang.fonts.get("regular", ())))
    return ImageFont.truetype(path, 12).getname()[0] if path else "Arial"


def _ppr(p, ns: str):
    ppr = p.find(ns + "pPr")
    if ppr is None:
        ppr = etree.Element(ns + "pPr")
        p.insert(0, ppr)
    return ppr


def apply_docx(paragraphs, lang) -> None:
    tag, face = _LANG_TAG.get(lang.code, lang.code), face_name(lang.code)
    tables = {}
    for p in paragraphs:
        _child(_ppr(p, W), W, "bidi", _PPR_ORDER)
        for r in p.iter(W + "r"):
            if r.find(W + "t") is None:
                continue
            rpr = r.find(W + "rPr")
            if rpr is None:
                rpr = etree.Element(W + "rPr")
                r.insert(0, rpr)
            _child(rpr, W, "rtl", _RPR_ORDER)
            _child(rpr, W, "rFonts", _RPR_ORDER).set(W + "cs", face)
            _child(rpr, W, "lang", _RPR_ORDER).set(W + "bidi", tag)
        for tbl in p.iterancestors(W + "tbl"):
            tables[id(tbl)] = tbl
    for tbl in tables.values():
        tbl_pr = tbl.find(W + "tblPr")
        if tbl_pr is not None and tbl_pr.find(W + "bidiVisual") is None:
            # CT_TblPr: tblStyle, tblpPr, tblOverlap, bidiVisual, ...
            el = etree.Element(W + "bidiVisual")
            before = [c for c in tbl_pr if etree.QName(c).localname in ("tblStyle", "tblpPr", "tblOverlap")]
            tbl_pr.insert(tbl_pr.index(before[-1]) + 1 if before else 0, el)


def apply_pptx(paragraphs, lang) -> None:
    """`paragraphs` are (a:p, effective alignment) pairs."""
    tag, face = _LANG_TAG.get(lang.code, lang.code), face_name(lang.code)
    for p, algn in paragraphs:
        ppr = _ppr(p, A)
        ppr.set("rtl", "1")
        if algn in _SWAP:
            ppr.set("algn", _SWAP[algn])
        for r in p.findall(A + "r"):
            rpr = r.find(A + "rPr")
            if rpr is None:
                rpr = etree.Element(A + "rPr")
                r.insert(0, rpr)
            rpr.set("lang", tag)
            cs = rpr.find(A + "cs")
            if cs is None:
                cs = etree.Element(A + "cs")
                after = [c for c in rpr if c.tag in _ARPR_AFTER_CS]
                rpr.insert(rpr.index(after[0]), cs) if after else rpr.append(cs)
            cs.set("typeface", face)
