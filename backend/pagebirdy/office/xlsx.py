"""Excel (.xlsx): the text in cells, nothing else.

Edited as raw OOXML. openpyxl drops charts, images and drawings when it
re-saves an existing workbook, so instead the package is copied entry by entry
(`package.write_patched`) and only two kinds of node are ever written: the text
of a shared string (`xl/sharedStrings.xml`, plain `<t>` or rich-text `<r>`
runs, carried through the engine as run tags) and the text of an inline string
(`<c t="inlineStr"><is>`). Formulas, cached values, numbers, dates, styles,
merges, hidden rows and columns, panes, defined names, sheet names, sheet
order, charts, drawings and comments are not read, so they cannot change.

A string is not translated when it is not prose (`office.classify`: numbers,
dates, codes, IDs, URLs, emails), or when the same text appears as a string
literal in a formula, a data-validation rule or a defined name: translating
the key of `VLOOKUP("Apple", …)` or one choice of a `"Yes,No"` list would
break the workbook the next time Excel recalculates it.

Right-to-left targets get their text and nothing more: a sheet is not
switched to `rightToLeft` in this release.
"""

from __future__ import annotations

import copy
import posixpath
import re
import zipfile

from lxml import etree

from pagebirdy.office.adapter import Issue, blank_segment, reject_tags, writable
from pagebirdy.office.formats import MB, Format
from pagebirdy.office.package import part_bytes, write_patched
from pagebirdy.office.protect import restore
from pagebirdy.office.runs import Piece, decode, encode

S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
_LITERAL = re.compile(r'"((?:[^"]|"")*)"')
_FORMULA_TAGS = (S + "f", S + "formula", S + "formula1", S + "formula2")


# Every part comes from an upload, so external entities are never resolved and
# nothing is fetched: a DOCTYPE cannot read a local file or reach the network.
_SAFE_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False,
                               huge_tree=False)


def _parse(z: zipfile.ZipFile, name: str):
    return etree.fromstring(z.read(name), parser=_SAFE_PARSER)


def _resolve(target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join("xl", target))


def _workbook(z: zipfile.ZipFile) -> tuple[list[tuple[str, str]], str | None]:
    """([(sheet name, part)], shared strings part or None), in workbook order."""
    rels = {r.get("Id"): r for r in _parse(z, "xl/_rels/workbook.xml.rels").iter(PKG + "Relationship")}
    sheets = []
    for sh in _parse(z, "xl/workbook.xml").iter(S + "sheet"):
        rel = rels.get(sh.get(R_ID))
        if rel is not None and rel.get("TargetMode") != "External":
            sheets.append((sh.get("name"), _resolve(rel.get("Target"))))
    shared = next((_resolve(r.get("Target")) for r in rels.values()
                   if r.get("Type", "").endswith("/sharedStrings")), None)
    return sheets, shared


def _column(n: int) -> str:
    letters = ""
    while n:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _inline_cells(root):
    """(address, cell) for every inline-string cell. `r` is optional on rows
    and cells, so a missing one is counted on from its predecessor, as Excel
    does — an address is always real and never repeats."""
    row_no = 0
    for row in root.iter(S + "row"):
        row_no = int(row.get("r") or row_no + 1)
        col = 0
        for c in row.findall(S + "c"):
            ref = c.get("r")
            if ref:
                letters = re.match(r"[A-Z]+", ref).group(0)
                col = 0
                for ch in letters:
                    col = col * 26 + ord(ch) - 64
            else:
                col += 1
                ref = f"{_column(col)}{row_no}"
            if c.get("t") == "inlineStr" and c.find(S + "is") is not None:
                yield ref, c


def formula_literals(z: zipfile.ZipFile, sheet_parts) -> set[str]:
    """Every string literal a formula, validation rule or defined name uses,
    and every table column name — text that must keep its spelling for the
    workbook to still work. Case-folded: Excel compares strings without case,
    so "apple" in a formula still looks up the cell that says "Apple"."""
    texts = [el.text or "" for el in _parse(z, "xl/workbook.xml").iter(S + "definedName")]
    for part in sheet_parts:
        root = _parse(z, part)
        for tag in _FORMULA_TAGS:
            texts.extend(el.text or "" for el in root.iter(tag))
    out = set()
    for text in texts:
        for lit in _LITERAL.findall(text):
            lit = lit.replace('""', '"')
            out.add(lit.strip().casefold())
            out.update(part.strip().casefold() for part in lit.split(","))
    # A table's header cells must keep the names its definition declares, or
    # Excel repairs the table away (and structured references with it).
    for name in z.namelist():
        if name.startswith("xl/tables/") and name.endswith(".xml"):
            out.update((col.get("name") or "").strip().casefold()
                       for col in _parse(z, name).iter(S + "tableColumn"))
    out.discard("")
    return out


def _key(rpr) -> str:
    return "" if rpr is None else etree.tostring(rpr, method="c14n").decode("utf-8")


def _pieces(holder) -> list[Piece]:
    """A `<si>` or `<is>` as pieces: its rich-text runs, or its one `<t>`."""
    runs = holder.findall(S + "r")
    if runs:
        return [Piece("text", r.findtext(S + "t") or "", _key(r.find(S + "rPr")), handle=r)
                for r in runs]
    t = holder.find(S + "t")
    return [Piece("text", t.text or "", "", handle=t)] if t is not None else []


def _plain(holder) -> str:
    return "".join(p.text for p in _pieces(holder))


def _set_text(t, text: str) -> None:
    t.text = text
    if text != text.strip() or "\n" in text:
        t.set(XML_SPACE, "preserve")
    else:
        t.attrib.pop(XML_SPACE, None)


def _rewrite(holder, seg, where: str, issues: list) -> bool:
    pieces = _pieces(holder)
    _, layout = encode(pieces)
    outs = decode(seg.target, layout)
    if outs is None:
        issues.append(reject_tags(seg, where))
        return False
    runs = holder.findall(S + "r")
    if not runs:
        _set_text(holder.find(S + "t"),
                  "".join(restore(o.text, seg.placeholders) if o.kind == "text" else "\n" for o in outs
                          if o.kind != "object"))
        return True
    at = list(holder).index(runs[0])
    for r in runs:
        holder.remove(r)
    new = []
    for o in outs:
        if o.kind != "text":
            continue  # no objects or breaks are ever extracted from a cell
        r = copy.deepcopy(layout.spans[o.span][0].handle)
        for child in list(r):
            if child.tag != S + "rPr":
                r.remove(child)
        t = etree.SubElement(r, S + "t")
        _set_text(t, restore(o.text, seg.placeholders))
        new.append(r)
    for i, r in enumerate(new):
        holder.insert(at + i, r)
    return True


class XlsxAdapter:
    def extract(self, src: str):
        with zipfile.ZipFile(src) as z:
            sheets, shared = _workbook(z)
            literals = formula_literals(z, [p for _, p in sheets])
            first_use: dict[int, int] = {}
            segs = []
            for n, (name, part) in enumerate(sheets, 1):
                root = _parse(z, part)
                for c in root.iter(S + "c"):
                    if c.get("t") == "s":
                        v = c.findtext(S + "v")
                        if v and v.strip().isdigit():
                            first_use.setdefault(int(v), n)
                # By sheet position, not name: a sheet name may hold characters
                # ("#", "%") that do not survive a URL path.
                for ref, c in _inline_cells(root):
                    segs.append(self._segment(f"xlsx:s{n}!{ref}", c.find(S + "is"), literals, n))
            if shared and shared in z.namelist():
                for i, si in enumerate(_parse(z, shared).iter(S + "si")):
                    segs.append(self._segment(f"xlsx:ss{i}", si, literals, first_use.get(i, 0)))
        # Shared strings first, then inline ones, as a reader meets them.
        segs.sort(key=lambda s: (not s.id.startswith("xlsx:ss"),))
        return segs

    @staticmethod
    def _segment(seg_id, holder, literals, page):
        if _plain(holder).strip().casefold() in literals:
            return blank_segment(seg_id, "", page)  # a formula depends on this spelling
        tagged, _ = encode(_pieces(holder))
        return blank_segment(seg_id, tagged, page)

    def rebuild(self, src, segments, out, lang):
        by_id = {s.id: s for s in segments}
        issues: list[Issue] = []
        replacements: dict[str, bytes] = {}
        with zipfile.ZipFile(src) as z:
            sheets, shared = _workbook(z)
            if shared and shared in z.namelist():
                root = _parse(z, shared)
                changed = False
                for i, si in enumerate(root.iter(S + "si")):
                    seg = by_id.get(f"xlsx:ss{i}")
                    if writable(seg):
                        changed |= _rewrite(si, seg, f"shared string {i}", issues)
                if changed:
                    replacements[shared] = part_bytes(root)
            for n, (name, part) in enumerate(sheets, 1):
                root = _parse(z, part)
                changed = False
                for ref, c in _inline_cells(root):
                    seg = by_id.get(f"xlsx:s{n}!{ref}")
                    if writable(seg):
                        changed |= _rewrite(c.find(S + "is"), seg, f"{name}!{ref}", issues)
                if changed:
                    replacements[part] = part_bytes(root)
        write_patched(src, out, replacements)
        return issues

    def validate(self, src, out):
        try:
            za, zb = zipfile.ZipFile(src), zipfile.ZipFile(out)
        except zipfile.BadZipFile as e:
            return [Issue("error", "unreadable", "output", f"output does not open: {e}")]
        with za, zb:
            if za.namelist() != zb.namelist():
                return [Issue("error", "structure", "workbook", "the package's parts changed")]
            sheets, shared = _workbook(za)
            if _workbook(zb) != (sheets, shared):
                return [Issue("error", "structure", "workbook", "sheets or their order changed")]
            text_parts = {p for _, p in sheets} | ({shared} if shared else set())
            issues = []
            for name in za.namelist():
                if name in text_parts:
                    continue
                if za.read(name) != zb.read(name):
                    issues.append(Issue("error", "structure", name, "a part that holds no text changed"))
            for sheet, part in sheets:
                try:
                    a, b = _parse(za, part), _parse(zb, part)
                except etree.XMLSyntaxError as e:
                    issues.append(Issue("error", "unreadable", sheet, str(e)))
                    continue
                if _formulas(a) != _formulas(b):
                    issues.append(Issue("error", "formula", sheet, "a formula changed"))
                if _cells(a) != _cells(b):
                    issues.append(Issue("error", "value", sheet, "a value or cell format changed"))
                elif _skeleton(a) != _skeleton(b):
                    issues.append(Issue("error", "structure", sheet, "sheet layout changed"))
                if "⟦" in etree.tostring(b, encoding="unicode"):
                    issues.append(Issue("error", "tokens", sheet, "a placeholder token reached the file"))
            if shared and shared in za.namelist():
                a, b = _parse(za, shared), _parse(zb, shared)
                if len(a.findall(S + "si")) != len(b.findall(S + "si")):
                    issues.append(Issue("error", "structure", "shared strings", "string count changed"))
                if "⟦" in etree.tostring(b, encoding="unicode"):
                    issues.append(Issue("error", "tokens", "shared strings",
                                        "a placeholder token reached the file"))
            return issues

    def units(self, src):
        with zipfile.ZipFile(src) as z:
            sheets, shared = _workbook(z)
            strings = len(_parse(z, shared).findall(S + "si")) if shared and shared in z.namelist() else 0
        return {"sheets": len(sheets), "strings": strings}


def _formulas(root) -> list:
    return [(c.get("r"), etree.tostring(f, method="c14n")) for c in root.iter(S + "c")
            for f in c.findall(S + "f")]


def _cells(root) -> list:
    """Every cell's address, type, style and value — except the text of an
    inline string, which is what translation writes."""
    return [(c.get("r"), c.get("t"), c.get("s"), c.findtext(S + "v")) for c in root.iter(S + "c")]


def _skeleton(root) -> bytes:
    clean = copy.deepcopy(root)
    for holder in clean.iter(S + "is"):
        for child in list(holder):
            holder.remove(child)
    return etree.tostring(clean, method="c14n")


ADAPTER = XlsxAdapter()
FORMAT = Format(".xlsx", "xlsx", "XLSX",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                100 * MB, "xl/workbook.xml", "pagebirdy.office.xlsx")
