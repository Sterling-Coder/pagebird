"""Office and plain-text document formats (.txt, .docx, .pptx, .xlsx).

Each format is an adapter that only extracts `Segment`s and writes text back;
protection, translation and the glossary are shared
(`office.pipeline.translate_document`).
"""

# The registry lists a format only once its adapter ships.
from pagebirdy.office import formats as _formats  # noqa: E402
from pagebirdy.office import txt as _txt  # noqa: E402

_formats.register(_txt.FORMAT)
from pagebirdy.office import docx as _docx  # noqa: E402

_formats.register(_docx.FORMAT)
from pagebirdy.office import pptx as _pptx  # noqa: E402

_formats.register(_pptx.FORMAT)
from pagebirdy.office import xlsx as _xlsx  # noqa: E402

_formats.register(_xlsx.FORMAT)
