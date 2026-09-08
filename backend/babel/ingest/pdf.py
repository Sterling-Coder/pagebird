"""PDF ingest: PyMuPDF spans -> Line objects with bbox/font/size.

We read the structured `dict` layout and keep every span's geometry and style
so the reassembly stage can place translated text in the same place.
"""

from __future__ import annotations

import fitz  # PyMuPDF

from babel.models import Line, Span


def extract_lines(pdf_path: str, pages: list[int] | None = None) -> list[Line]:
    """Return all text lines in the document (optionally a page subset, 0-based)."""
    doc = fitz.open(pdf_path)
    try:
        lines: list[Line] = []
        for pno in range(doc.page_count):
            if pages is not None and pno not in pages:
                continue
            page = doc.load_page(pno)
            # sort=True gives natural top-to-bottom, column-aware reading order.
            data = page.get_text("dict", sort=True)
            for bno, block in enumerate(data.get("blocks", [])):
                if block.get("type") != 0:  # 0 = text block; 1 = image
                    continue
                for line in block.get("lines", []):
                    spans = [_to_span(s) for s in line.get("spans", []) if s.get("text")]
                    if not spans:
                        continue
                    lines.append(
                        Line(page=pno, bbox=tuple(line["bbox"]), spans=spans, block=bno,
                             direction=tuple(line.get("dir", (1.0, 0.0))))
                    )
        return lines
    finally:
        doc.close()


def _to_span(s: dict) -> Span:
    return Span(
        text=s["text"],
        font=s.get("font", ""),
        size=float(s.get("size", 0.0)),
        color=int(s.get("color", 0)),
        bbox=tuple(s["bbox"]),
        flags=int(s.get("flags", 0)),
        origin=float(s.get("origin", (0.0, 0.0))[1]),
    )
