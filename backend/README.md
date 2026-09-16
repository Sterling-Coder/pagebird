# Pagebirdy backend

FastAPI service that does the actual translation. Package: `pagebirdy/`.

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn pagebirdy.api:app --reload --port 8000
```

## Layout

```
pagebirdy/
  api.py          FastAPI routes — jobs, projects, folders, upload, download, logs
  pipeline.py     translate_pdf / translate_idml / translate_links_folder — orchestrates a full job
  auth.py         Supabase-token auth, team/owner resolution
  storage.py      Supabase Storage read/write (durable output; local disk is scratch only)
  languages.py    supported target languages, per-language font/direction config

  ingest/         PDF text extraction, OCR (Vision/DocAI/rapidocr/http fallback)
  protect/        math expressions, placeholders — anything an LLM must not touch
  translate/      dual-engine LLM translation, integrity/verify gate
  idml/           IDML package read/write, linked-graphic translation, XML render preview
  reassemble/     rebuild a translated PDF from segments
  review/         Postgres-backed job/segment store (Supabase) — the human review layer
  eval/           quality scoring (COMET/MQM-style), scorecards
  glossary/       fixed per-language term lists used in translation prompts + QA
  fonts/          bundled font files for script coverage (Arabic, Hebrew, Devanagari, CJK, ...)
```

Each stage of a job: extract text → protect math/placeholders → dual-engine LLM translate → integrity/verify gate → reassemble → persist to Storage. Progress is reported incrementally via a `progress_cb` threaded through the pipeline so the UI can poll status.

## Environment

Not committed (`.env`, `.env.production`). Required/used, by area:

- **Postgres/Supabase**: connection string for `pagebirdy/review/store.py` (job/segment/project state), Supabase Storage credentials (`storage.py`), Supabase auth keys (`auth.py`).
- **Translation**: `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY`. `BABEL_LLM_PROVIDER` / `BABEL_LLM_MODEL` to pin a provider/model.
- **OCR** (optional): Google Vision or Document AI credentials (`GOOGLE_APPLICATION_CREDENTIALS`, `DOCAI_PROJECT_ID`, `DOCAI_LOCATION`, `DOCAI_PROCESSOR_ID`). Falls back to a local/HTTP OCR engine or skips OCR entirely, reporting why.
- **Equations** (optional): Mathpix keys for LaTeX detection in scanned math.
- **Misc**: `FRONTEND_ORIGIN` (CORS), `BABEL_UPLOAD_DIR` / `BABEL_OUT_DIR` (local scratch dirs, safe to clear), `BABEL_STORAGE_BUCKET`.

(Env var names still say `BABEL_*` — kept as-is deliberately since they're set in the real deployment environment, not just in code; see the root README's note on the package rename.)

Every optional integration degrades gracefully and logs why when unconfigured — nothing hard-fails at import time for a missing key.

## Database migrations

Alembic, against the same Postgres/Supabase database as the review store.

```bash
alembic upgrade head              # apply
alembic revision -m "description" # new migration
```

## Tests

```bash
pytest tests/
```

Some tests require a live Supabase/Postgres connection and real auth to pass (a handful fail in a bare local checkout with no `.env` — pre-existing, not a regression signal on their own).

## Notable design choices

- **No local durable storage.** Every job's source/output goes to Supabase Storage; `out/`/`uploads/` on disk are scratch space that can be deleted anytime (regenerate empty on next run).
- **`.idml` is the flagship path.** Font substitution, RTL mirroring, style inheritance, and linked-graphic OCR translation are all deepest here — PDF and links-batch share the same core engine but less of the layout-fidelity machinery applies.
- **Links batch jobs** (`translate_links_folder`) are independent from any document: upload a folder of `.ai`/`.eps`/`.pdf`/`.psd`, get back translated versions plus untouched originals for anything with no extractable text — nothing is silently dropped.
