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
  api.py          FastAPI routes — jobs, projects, folders, upload, download, QA, logs;
                  background job executor
  pipeline.py     translate_pdf / translate_idml / translate_links_folder — orchestrates a full job
  auth.py         Supabase-token auth, team/owner resolution
  storage.py      S3-compatible object storage (Backblaze B2) — durable uploads/output;
                  local disk is scratch only
  languages.py    supported target languages, per-language font/direction config
  script.py       script/direction detection helpers

  ingest/         PDF text extraction, OCR (Vision/DocAI/rapidocr/http fallback)
  protect/        math expressions, placeholders — anything an LLM must not touch
  translate/      LLM translation engines (OpenAI/Anthropic, identity offline), glossary check
  idml/           IDML package read/write, linked-graphic translation, XML render preview,
                  rule-driven RTL stage (rtl*.py), layout validation, InDesign export
  reassemble/     rebuild a translated PDF from segments
  review/         Postgres-backed job/segment/QA-report store (Supabase) — the human review layer
  eval/           on-demand QA — COMET/MQM scoring, layout scoring, scorecards; runs in a
                  child process (eval/isolated.py)
  glossary/       fixed per-language term lists used in translation prompts + QA
  fonts/          bundled font files for script coverage (Arabic, Hebrew, Devanagari, CJK, ...)
```

Each stage of a job: extract text → protect math/placeholders → LLM translate (+ glossary check) → RTL layout for RTL targets → reassemble → persist to object storage. There is no post-translation verify pass or `needs_human` quality routing — both were removed; quality is measured by the separate, on-demand QA report.

Uploads return `202` with a job id as soon as the job row exists; translation runs on a background thread pool (`PAGEBIRDY_JOB_WORKERS`, default 3) and the UI polls the job row. Progress is reported incrementally via a `progress_cb` threaded through the pipeline. A failed job records its error on the row so the UI can show why.

QA (`GET /api/jobs/{id}/eval`) runs in a child process with a timeout and memory cap, so a crash while re-rendering a large document fails one QA request instead of taking the API down. Reports are stored in Postgres (`review_evals`) and listed per project (`/api/projects/{id}/evals`).

## Environment

Not committed (`.env`, `.env.production`). Required/used, by area:

- **Postgres/Supabase**: `SUPABASE_DB_URL` for `pagebirdy/review/store.py` (job/segment/project/QA state; pool size `PAGEBIRDY_DB_POOL_MAX`, default 20), `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_ROLE_KEY` for auth (`auth.py`).
- **Object storage** (required — uploads fail without it): `PAGEBIRDY_S3_ENDPOINT`, `PAGEBIRDY_S3_BUCKET`, `PAGEBIRDY_S3_ACCESS_KEY`, `PAGEBIRDY_S3_SECRET_KEY`, `PAGEBIRDY_S3_REGION` (must match the endpoint's region; B2 rejects `auto`). Points at Backblaze B2 today; any S3-compatible provider works.
- **Translation**: `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY` (OpenAI preferred when both are set). `BABEL_LLM_PROVIDER` / `BABEL_LLM_MODEL` to pin a provider/model. `DEEPL_AUTH_KEY` builds a secondary engine that is currently unused.
- **OCR** (optional): Google Vision or Document AI credentials (`GOOGLE_APPLICATION_CREDENTIALS`, or `GOOGLE_CREDENTIALS_JSON` with the raw JSON in prod; `DOCAI_PROJECT_ID`, `DOCAI_LOCATION`, `DOCAI_PROCESSOR_ID`). `OCR_API_BASE_URL` for an HTTP OCR service; `BABEL_OCR_ENGINE` forces an engine. Falls back to local rapidocr or skips OCR entirely, reporting why.
- **Equations** (optional): `MATHPIX_APP_ID` / `MATHPIX_APP_KEY` for LaTeX detection in scanned math; `BABEL_EQUATION_ENGINE` forces an engine.
- **QA** (optional): `BABEL_EVAL_JUDGE_PROVIDER` / `BABEL_EVAL_JUDGE_MODEL` for the MQM judge, `BABEL_EVAL_COMET_MODEL` / `BABEL_EVAL_KIWI_MODEL`, `PAGEBIRDY_EVAL_TIMEOUT` (seconds, default 240) and `PAGEBIRDY_EVAL_MAX_MB` (child memory cap, default 3072, Linux only).
- **InDesign** (optional): `INDESIGN_SERVER` to export `.indd`. Not set in production, so `.indd` uploads are rejected with a 400 asking for IDML.
- **Jobs**: `PAGEBIRDY_JOB_WORKERS` (background translation threads), `PAGEBIRDY_SYNC_JOBS=1` runs jobs inline in the request (tests, scripts).
- **Misc**: `FRONTEND_ORIGIN` (CORS), `BABEL_UPLOAD_DIR` / `BABEL_OUT_DIR` (local scratch dirs, safe to clear).

(Older env vars still say `BABEL_*` — kept deliberately since they're set in the real deployment environment; storage vars were renamed to `PAGEBIRDY_S3_*`. See the root README's note on the package rename.)

Every optional integration degrades gracefully and logs why when unconfigured — nothing hard-fails at import time for a missing key.

## Database migrations

Alembic (`migrations/`), against the same Postgres/Supabase database as the review store.

```bash
alembic upgrade head              # apply
alembic revision -m "description" # new migration
```

## Tests

```bash
pytest tests/
```

`tests/conftest.py` keeps the suite off production: it blanks the Supabase and storage env (so values from `.env` never apply) and replaces every storage call with one that fails loudly. Review-store tests need `TEST_DATABASE_URL` pointing at a throwaway Postgres; without it they are skipped, not failed.

## Notable design choices

- **No local durable storage.** Every job's source/output goes to object storage (B2), keyed `jobs/<job_id>/…`; the container disk resets on every redeploy, and `out/`/`uploads/` on disk are scratch space that can be deleted anytime (regenerate empty on next run).
- **`.idml` is the flagship path.** Font substitution, the rule-driven RTL stage (page template stays put, content mirrors within its page), style inheritance, and linked-graphic OCR translation are all deepest here — PDF and links-batch share the same core engine but less of the layout-fidelity machinery applies.
- **Links batch jobs** (`translate_links_folder`) are independent from any document: upload a folder of `.ai`/`.eps`/`.pdf`/`.psd`, get back translated versions plus untouched originals for anything with no extractable text — nothing is silently dropped. A new links batch can start while another is still translating. Translated text stays in its source Illustrator layer.
