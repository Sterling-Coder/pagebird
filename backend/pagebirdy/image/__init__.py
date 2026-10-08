"""Image translation — text burned into a raster image, translated in place.

A separate pipeline from the PDF/IDML document paths, sharing their core:

    validate ─► OCR (ingest/ocr.py's Vision client) ─► classify ─► translate
    (Translator + mathguard) ─► fit ─► reconstruct ─► quality check

Only the pixels inside a translated text region are ever rewritten; everything
else in the output is the source image's own pixels. Nothing here is imported
by `pipeline.py`, so the document paths are untouched by it.
"""
