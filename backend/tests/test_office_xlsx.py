import re
import zipfile

import pytest

from pagebirdy.office import formats
from pagebirdy.office.pipeline import prepare
from pagebirdy.office.xlsx import ADAPTER as XLSX
from tests.office_fixtures import LANG_AR, LANG_ES, make_xlsx, translate_all

RICH = "Net ⟦r1⟧profit⟦/r1⟧ margin"
ES = {"Total Revenue": "Ingresos totales", "Region": "Región", "Quarterly note": "Nota trimestral",
      RICH: "Margen de ⟦r1⟧beneficio⟦/r1⟧ neto"}


def _build(tmp_path, lang=LANG_ES, table=ES):
    src = str(tmp_path / "in.xlsx")
    make_xlsx(src)
    segs = XLSX.extract(src)
    todo, kept = prepare(segs)
    translate_all(todo, lambda s: table.get(s, s))
    out = str(tmp_path / "out.xlsx")
    issues = XLSX.rebuild(src, segs, out, lang) + XLSX.validate(src, out)
    return src, out, segs, kept, issues


def _part(path, name):
    return zipfile.ZipFile(path).read(name).decode("utf-8")


def _rewrite(src, dst, member, old, new):
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, "w") as zo:
        for item in zi.infolist():
            data = zi.read(item.filename)
            if item.filename == member:
                assert old in data
                data = data.replace(old, new)
            zo.writestr(item, data)


def test_only_prose_strings_are_sent(tmp_path):
    src = str(tmp_path / "in.xlsx")
    make_xlsx(src)
    todo, _ = prepare(XLSX.extract(src))
    # "Apple" is a VLOOKUP key, "Yes"/"No" a validation list, the rest an ID and a URL.
    assert sorted(s.source for s in todo) == sorted(["Total Revenue", "Region", "Quarterly note", RICH])
    ids = {s.source: s.id for s in todo}
    assert ids["Total Revenue"] == "xlsx:ss0" and ids["Quarterly note"] == "xlsx:s1!C3"
    assert {s.source: s.page for s in todo}["Region"] == 2  # first used on sheet 2


def test_text_translated_everything_else_byte_identical(tmp_path):
    src, out, _, _, issues = _build(tmp_path)
    assert [i for i in issues if i.level == "error"] == []
    ss = _part(out, "xl/sharedStrings.xml")
    assert "Ingresos totales" in ss and "Región" in ss and ">Apple<" in ss and ">Yes<" in ss
    assert re.search(r'<r><rPr><b/><sz val="11"/></rPr><t[^>]*>beneficio</t></r>', ss)
    assert "Nota trimestral" in _part(out, "xl/worksheets/sheet1.xml")
    za, zb = zipfile.ZipFile(src), zipfile.ZipFile(out)
    assert za.namelist() == zb.namelist()
    changed = {n for n in za.namelist() if za.read(n) != zb.read(n)}
    assert changed == {"xl/sharedStrings.xml", "xl/worksheets/sheet1.xml"}
    for formula in ("<f>SUM(B1:B1)</f>", '<f>VLOOKUP("Apple",Data!A1:B2,2,FALSE)</f>',
                    '<formula1>"Yes,No"</formula1>', '<mergeCell ref="A4:B4"/>', 'state="frozen"',
                    'hidden="1"', "<v>100000</v>", '<c r="C1" s="1"><v>45413</v></c>'):
        assert formula in _part(out, "xl/worksheets/sheet1.xml"), formula


def test_untouched_workbook_is_byte_identical(tmp_path):
    src = str(tmp_path / "in.xlsx")
    make_xlsx(src)
    segs = XLSX.extract(src)
    prepare(segs)  # nothing translated
    out = str(tmp_path / "out.xlsx")
    XLSX.rebuild(src, segs, out, LANG_ES)
    za, zb = zipfile.ZipFile(src), zipfile.ZipFile(out)
    assert all(za.read(n) == zb.read(n) for n in za.namelist())


def test_arabic_keeps_formulas_and_no_rtl_flip(tmp_path):
    table = {k: "نص عربي" for k in ES}
    table[RICH] = "⟦r1⟧صافي⟦/r1⟧ الربح"
    _, out, _, _, issues = _build(tmp_path, LANG_AR, table)
    assert [i for i in issues if i.level == "error"] == []
    s1 = _part(out, "xl/worksheets/sheet1.xml")
    assert "rightToLeft" not in s1
    assert "<f>SUM(B1:B1)</f>" in s1 and 'VLOOKUP("Apple",Data!A1:B2,2,FALSE)' in s1
    assert "نص عربي" in _part(out, "xl/sharedStrings.xml")


def test_validate_catches_a_changed_formula(tmp_path):
    src, out, _, _, _ = _build(tmp_path)
    bad = str(tmp_path / "bad.xlsx")
    _rewrite(out, bad, "xl/worksheets/sheet1.xml", b"SUM(B1:B1)", b"SUM(B1:B2)")
    assert any(i.level == "error" and i.code == "formula" for i in XLSX.validate(src, bad))


def test_validate_catches_a_changed_number(tmp_path):
    src, out, _, _, _ = _build(tmp_path)
    bad = str(tmp_path / "bad.xlsx")
    _rewrite(out, bad, "xl/worksheets/sheet2.xml", b"<v>200000</v>", b"<v>200001</v>")
    assert any(i.level == "error" for i in XLSX.validate(src, bad))


def test_validate_catches_a_changed_style_part(tmp_path):
    src, out, _, _, _ = _build(tmp_path)
    bad = str(tmp_path / "bad.xlsx")
    _rewrite(out, bad, "xl/styles.xml", b"yyyy-mm-dd", b"dd/mm/yyyy")
    assert any(i.level == "error" for i in XLSX.validate(src, bad))


def test_xlsx_content_check(tmp_path):
    fmt = formats.lookup("book.xlsx")
    assert fmt is not None
    good = tmp_path / "a.xlsx"
    make_xlsx(str(good))
    formats.check_content(fmt, str(good))
    fake = tmp_path / "b.xlsx"
    with zipfile.ZipFile(fake, "w") as z:
        z.writestr("word/document.xml", "<x/>")
    with pytest.raises(formats.UnsupportedFile):
        formats.check_content(fmt, str(fake))


def test_external_entities_in_a_part_are_not_resolved(tmp_path):
    """An upload's XML can declare an entity pointing at a local file; parsing
    must not read it."""
    import io
    import zipfile

    from pagebirdy.office import xlsx

    secret = tmp_path / "secret.txt"
    secret.write_text("TOP-SECRET-CONTENT")
    payload = (f'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "file://{secret}">]>'
               '<x>&e;</x>').encode()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/sharedStrings.xml", payload)
    with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as z:
        root = xlsx._parse(z, "xl/sharedStrings.xml")
    assert "TOP-SECRET-CONTENT" not in "".join(root.itertext())
