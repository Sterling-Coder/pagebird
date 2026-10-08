import zipfile

import pytest

from pagebirdy.office import formats


def _zip(path, names):
    with zipfile.ZipFile(path, "w") as z:
        for n in names:
            z.writestr(n, "<x/>")


def test_unknown_extension_lists_supported_formats():
    with pytest.raises(formats.UnsupportedFile) as e:
        formats.check_extension("a.rtf")
    msg = str(e.value)
    assert msg.startswith("This file type isn't supported yet. Please upload ")
    assert "PDF" in msg and "IDML" in msg


def test_no_extension_is_unsupported():
    with pytest.raises(formats.UnsupportedFile):
        formats.check_extension("README")


@pytest.mark.parametrize("old,new", [("a.doc", ".docx"), ("a.ppt", ".pptx"), ("a.XLS", ".xlsx")])
def test_legacy_formats_get_a_save_as_hint(old, new):
    with pytest.raises(formats.UnsupportedFile) as e:
        formats.check_extension(old)
    assert new in str(e.value)


def test_existing_formats_pass_extension_check_unchanged():
    for name in ("a.pdf", "a.IDML"):
        formats.check_extension(name)          # no raise
        assert formats.lookup(name) is None    # still dispatched by api.py


def test_listing_shape():
    data = formats.listing()
    exts = [d["ext"] for d in data["documents"]]
    assert exts[:2] == [".pdf", ".idml"]
    assert ".indd" not in exts   # rejected by api.py: production has no InDesign Server
    assert all({"ext", "label", "mime"} <= set(d) for d in data["documents"])
    assert len(exts) == len(set(exts))
