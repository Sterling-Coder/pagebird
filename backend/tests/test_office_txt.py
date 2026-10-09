from pagebirdy.office import formats
from pagebirdy.office.txt import ADAPTER as TXT
from tests.office_fixtures import LANG_ES, translate_all

import pytest


def _roundtrip(tmp_path, raw: bytes, fn=lambda s: s.upper()):
    src = tmp_path / "in.txt"
    src.write_bytes(raw)
    segs = TXT.extract(str(src))
    translate_all(segs, fn)
    out = tmp_path / "out.txt"
    issues = TXT.rebuild(str(src), segs, str(out), LANG_ES)
    return segs, out.read_bytes(), issues + TXT.validate(str(src), str(out))


def test_structure_survives_byte_for_byte(tmp_path):
    raw = b"Hello {customer_name},\r\n\r\n    Your order {order_id} shipped.  \r\nBye"
    segs, out, issues = _roundtrip(tmp_path, raw)
    assert out == b"HELLO {CUSTOMER_NAME},\r\n\r\n    YOUR ORDER {ORDER_ID} SHIPPED.  \r\nBYE"
    assert [s.id for s in segs] == ["txt:L0", "txt:L2", "txt:L3"]
    assert issues == []


def test_bom_and_lf_and_final_newline_kept(tmp_path):
    _, out, _ = _roundtrip(tmp_path, "﻿a\nb\n".encode("utf-8"))
    assert out == "﻿A\nB\n".encode("utf-8")


def test_mixed_line_endings_kept_per_line(tmp_path):
    _, out, _ = _roundtrip(tmp_path, b"a\r\nb\nc\rd")
    assert out == b"A\r\nB\nC\rD"


def test_cp1252_input_written_as_utf8(tmp_path):
    _, out, _ = _roundtrip(tmp_path, "café menu".encode("cp1252"), fn=lambda s: s)
    assert out.decode("utf-8") == "café menu"


def test_utf16_with_bom(tmp_path):
    _, out, _ = _roundtrip(tmp_path, "hi\r\n".encode("utf-16"), fn=lambda s: s)
    assert out == "﻿hi\r\n".encode("utf-8")


def test_untranslated_segments_keep_source(tmp_path):
    src = tmp_path / "in.txt"
    src.write_text("one\ntwo\n", encoding="utf-8", newline="")
    segs = TXT.extract(str(src))
    segs[0].target, segs[0].status = "uno", "translated"
    segs[1].target, segs[1].status = "dos", "needs_human"
    TXT.rebuild(str(src), segs, str(tmp_path / "o.txt"), LANG_ES)
    assert (tmp_path / "o.txt").read_bytes() == b"uno\ntwo\n"


def test_validate_catches_lost_line(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"a\n\nb\n")
    (tmp_path / "b.txt").write_bytes(b"a\nb\n")
    assert any(i.level == "error" for i in TXT.validate(str(tmp_path / "a.txt"), str(tmp_path / "b.txt")))


def test_txt_registered_and_sniffed(tmp_path):
    fmt = formats.lookup("notes.TXT")
    assert fmt is not None and fmt.label == "TXT"
    good = tmp_path / "a.txt"; good.write_text("hello", encoding="utf-8")
    formats.check_content(fmt, str(good))
    binary = tmp_path / "b.txt"; binary.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")
    with pytest.raises(formats.UnsupportedFile):
        formats.check_content(fmt, str(binary))
    empty = tmp_path / "c.txt"; empty.write_bytes(b"")
    with pytest.raises(formats.UnsupportedFile):
        formats.check_content(fmt, str(empty))
    assert ".txt" in [d["ext"] for d in formats.listing()["documents"]]
