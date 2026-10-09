"""Which document formats the upload accepts, and how each is checked.

The single list behind `POST /api/translate`'s extension check and
`GET /api/formats`, which the UI reads. PDF/IDML are listed for the UI
but keep their extension-only acceptance and their own dispatch in `api.py`
(`.indd` is rejected there: production has no InDesign Server):
sniffing their content could reject a file that uploads today. An office
format appears here only once its adapter ships (`register`, called from
`pagebirdy/office/__init__.py`).
"""

from __future__ import annotations

import importlib
import os
import zipfile
from dataclasses import dataclass

MB = 1024 * 1024
# An upload is refused by what its archive *declares* before anything is
# inflated: a few-MB deflate bomb would otherwise stall the server and then
# exhaust memory when a part is parsed.
MAX_UNCOMPRESSED = 2048 * MB
# Above this many uncompressed bytes the archive must also compress no better
# than MAX_RATIO; real Office XML compresses ~5-20x, a bomb ~1000x.
MAX_RATIO_BYTES = 200 * MB
MAX_RATIO = 100


@dataclass(frozen=True)
class Format:
    ext: str
    key: str
    label: str
    mime: str
    max_bytes: int
    required_part: str | None     # a zip member that must exist; None = not a zip
    adapter_module: str           # module exposing ADAPTER


_EXISTING = (
    {"ext": ".pdf", "label": "PDF", "mime": "application/pdf"},
    {"ext": ".idml", "label": "IDML", "mime": "application/vnd.adobe.indesign-idml-package"},
)
EXISTING = tuple(d["ext"] for d in _EXISTING)
# Binary Office formats: not supported, but worth telling apart from "unknown".
LEGACY = {".doc": ".docx", ".ppt": ".pptx", ".xls": ".xlsx"}
OFFICE: dict[str, Format] = {}


class UnsupportedFile(Exception):
    """User-facing: the message is shown verbatim in both UIs."""


def register(fmt: Format) -> None:
    OFFICE[fmt.ext] = fmt


def _labels() -> list[str]:
    return [d["label"] for d in _EXISTING] + [f.label for f in OFFICE.values()]


def _ext(name: str) -> str:
    return os.path.splitext(name or "")[1].lower()


def lookup(name: str) -> Format | None:
    """The office format for a file name, or None (an existing format, or
    something unsupported)."""
    return OFFICE.get(_ext(name))


def check_extension(name: str) -> None:
    ext = _ext(name)
    if ext in EXISTING or ext in OFFICE:
        return
    if ext in LEGACY:
        raise UnsupportedFile(
            f"{ext} files aren't supported. Open the file in Office, save it as "
            f"{LEGACY[ext]} and upload that instead.")
    labels = _labels()
    raise UnsupportedFile("This file type isn't supported yet. Please upload "
                          + ", ".join(labels[:-1]) + " or " + labels[-1] + ".")


def check_content(fmt: Format, path: str) -> None:
    """The file is what its extension says: size, signature, readable parts."""
    size = os.path.getsize(path)
    if size == 0:
        raise UnsupportedFile("The file is empty.")
    if size > fmt.max_bytes:
        raise UnsupportedFile(f"The file is larger than {fmt.max_bytes // MB} MB, "
                              f"the limit for {fmt.label} files.")
    if fmt.required_part is None:
        adapter_for(fmt).sniff(path)
        return
    try:
        with zipfile.ZipFile(path) as z:
            infos = z.infolist()
            unpacked = sum(i.file_size for i in infos)
            packed = sum(i.compress_size for i in infos) or 1
            if unpacked > MAX_UNCOMPRESSED or (
                    unpacked > MAX_RATIO_BYTES and unpacked / packed > MAX_RATIO):
                raise UnsupportedFile(f"This {fmt.label} file is too large to process "
                                      f"once unpacked ({unpacked // MB} MB).")
            names = {i.filename for i in infos}
            bad = z.testzip()
    except (zipfile.BadZipFile, OSError, EOFError, ValueError):
        names, bad = set(), "unreadable"
    if fmt.required_part not in names or bad:
        raise UnsupportedFile(f"This file isn't a valid {fmt.label} document, or it is damaged. "
                              f"Open it in Office, save it as {fmt.ext} and try again.")


def adapter_for(fmt: Format):
    return importlib.import_module(fmt.adapter_module).ADAPTER


def listing() -> dict:
    docs = [dict(d) for d in _EXISTING] + [
        {"ext": f.ext, "label": f.label, "mime": f.mime} for f in OFFICE.values()]
    return {"documents": docs}
