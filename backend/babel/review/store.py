"""Review store: persists a translation job's segments so the human-review UI
has something to load, edit, and approve.

This is what turns "MT output" into "high accuracy": every segment the pipeline
was unsure about (needs_human, disagreement, glossary miss) surfaces here for a
person to fix, and every approval writes back to the shared translation memory
so the correction is reused everywhere.

Backed by Supabase Postgres (via SUPABASE_DB_URL) — not local SQLite. A local
SQLite file lived on Railway's container disk, which resets to empty on every
redeploy; every project/job was silently wiped each deploy. Table names are
prefixed review_ (review_projects, review_jobs, ...) to stay out of the way of
Supabase's own auth/profiles/team_members tables in the same database.

Schema: see migrations/versions/*_review_store_tables_*.py.
"""

from __future__ import annotations

import json
import os
import time
import uuid

import psycopg
from psycopg.rows import dict_row

from babel.config import load_env
from babel.models import Segment
from babel.tm.store import TranslationMemory
from babel.translate import integrity

load_env()


def _db_url() -> str:
    url = os.environ.get("SUPABASE_DB_URL", "")
    if not url:
        raise RuntimeError("SUPABASE_DB_URL is not set — required to reach the review store")
    # Alembic and psycopg2-style tooling use a bare postgresql:// scheme;
    # psycopg (v3) needs it spelled out to pick the right driver.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    # psycopg.connect() doesn't understand the SQLAlchemy-style "+psycopg"
    # scheme — strip it back off for the raw driver, keep it only when
    # something else (SQLAlchemy) reads this via a different path.
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


class ReviewStore:
    def __init__(self, path: str = "", tm_path: str = "babel_tm.db"):
        # `path` (an old SQLite filename) is accepted for call-site
        # compatibility but unused now — everything reads from SUPABASE_DB_URL.
        self.conn = psycopg.connect(_db_url(), row_factory=dict_row, autocommit=False)
        self.tm_path = tm_path

    # ---- write ---------------------------------------------------------------

    def save_job(
        self, source: str, output: str, segments: list[Segment], meta: dict, *,
        original_filename: str | None = None,
        file_hash: str | None = None,
        file_size: int | None = None,
        duration_sec: float | None = None,
        status: str = "complete",
        error: str | None = None,
        project_id: str | None = None,
        job_type: str = "document",
        folder_id: str | None = None,
        created_by: str | None = None,
    ) -> str:
        job_id = uuid.uuid4().hex[:12]
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO review_jobs (id, source, output, created_at, meta_json, "
                "original_filename, file_hash, file_size, duration_sec, status, error, "
                "project_id, job_type, folder_id, created_by) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (job_id, source, output, time.time(), json.dumps(meta, ensure_ascii=False),
                 original_filename, file_hash, file_size, duration_sec, status, error,
                 project_id, job_type, folder_id, created_by),
            )
            for s in segments:
                if not s.is_translatable:
                    continue  # empty/whitespace-only segments aren't reviewable
                cur.execute(
                    "INSERT INTO review_segments (job_id, seg_id, page, source, target, "
                    "status, disagreement, has_math_font, placeholders_json, bbox_json, "
                    "notes_json, approved) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        job_id, s.id, s.page, s.source, s.target, s.status,
                        int(s.disagreement), int(s.has_math_font),
                        json.dumps(s.placeholders, ensure_ascii=False),
                        json.dumps(s.bbox), json.dumps(s.notes, ensure_ascii=False), 0,
                    ),
                )
        self.conn.commit()
        return job_id

    def update_job_paths(self, job_id: str, source: str | None = None,
                          output: str | None = None) -> None:
        """Repoint a job's stored source/output — a storage key, not a local
        path, once the pipeline's local scratch copy has been uploaded."""
        with self.conn.cursor() as cur:
            if source is not None:
                cur.execute("UPDATE review_jobs SET source = %s WHERE id = %s", (source, job_id))
            if output is not None:
                cur.execute("UPDATE review_jobs SET output = %s WHERE id = %s", (output, job_id))
        self.conn.commit()

    def delete_job(self, job_id: str) -> None:
        """Remove a job and its segments (e.g. a translate succeeded but a later
        export step failed, leaving a job row that shouldn't be browsable/downloadable)."""
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM review_segment_events WHERE job_id = %s", (job_id,))
            cur.execute("DELETE FROM review_segments WHERE job_id = %s", (job_id,))
            cur.execute("DELETE FROM review_jobs WHERE id = %s", (job_id,))
        self.conn.commit()

    # ---- read ----------------------------------------------------------------

    def list_jobs(self, created_by: str | list[str] | None = None) -> list[dict]:
        if isinstance(created_by, str):
            created_by = [created_by]
        with self.conn.cursor() as cur:
            if created_by is not None:
                cur.execute(
                    "SELECT id, source, output, created_at, meta_json, original_filename, "
                    "file_hash, file_size, duration_sec, status, error, project_id, job_type, "
                    "folder_id, created_by FROM review_jobs WHERE created_by = ANY(%s) "
                    "ORDER BY created_at DESC",
                    (list(created_by),),
                )
            else:
                cur.execute(
                    "SELECT id, source, output, created_at, meta_json, original_filename, "
                    "file_hash, file_size, duration_sec, status, error, project_id, job_type, "
                    "folder_id, created_by FROM review_jobs ORDER BY created_at DESC"
                )
            rows = cur.fetchall()
        out = []
        for r in rows:
            counts = self._status_counts(r["id"])
            out.append({
                "id": r["id"], "source": r["source"], "output": r["output"],
                "created_at": r["created_at"], "meta": json.loads(r["meta_json"]),
                "status_counts": counts,
                "original_filename": r["original_filename"], "file_hash": r["file_hash"],
                "file_size": r["file_size"], "duration_sec": r["duration_sec"],
                "status": r["status"], "error": r["error"],
                "project_id": r["project_id"], "job_type": r["job_type"],
                "folder_id": r["folder_id"], "created_by": r["created_by"],
            })
        return out

    # ---- folders -----------------------------------------------------------

    def create_folder(self, project_id: str, name: str,
                       parent_folder_id: str | None = None) -> str:
        folder_id = uuid.uuid4().hex[:12]
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO review_folders (id, project_id, name, parent_folder_id, created_at) "
                "VALUES (%s,%s,%s,%s,%s)",
                (folder_id, project_id, name, parent_folder_id, time.time()),
            )
        self.conn.commit()
        return folder_id

    def list_folders(self, project_id: str,
                      parent_folder_id: str | None = None) -> list[dict]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, project_id, name, parent_folder_id, created_at FROM review_folders "
                "WHERE project_id = %s AND parent_folder_id IS NOT DISTINCT FROM %s "
                "ORDER BY created_at DESC",
                (project_id, parent_folder_id),
            )
            return cur.fetchall()

    def get_folder(self, folder_id: str) -> dict | None:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, project_id, name, parent_folder_id, created_at "
                "FROM review_folders WHERE id = %s",
                (folder_id,),
            )
            return cur.fetchone()

    def delete_folder(self, folder_id: str) -> None:
        """Remove a folder, every file (job) filed under it, and every
        subfolder (recursively) beneath it."""
        with self.conn.cursor() as cur:
            stack = [folder_id]
            all_folder_ids: list[str] = []
            while stack:
                fid = stack.pop()
                all_folder_ids.append(fid)
                cur.execute(
                    "SELECT id FROM review_folders WHERE parent_folder_id = %s", (fid,)
                )
                stack.extend(c["id"] for c in cur.fetchall())

            for fid in all_folder_ids:
                cur.execute("SELECT id FROM review_jobs WHERE folder_id = %s", (fid,))
                job_rows = cur.fetchall()
                for jr in job_rows:
                    cur.execute(
                        "DELETE FROM review_segment_events WHERE job_id = %s", (jr["id"],)
                    )
                    cur.execute("DELETE FROM review_segments WHERE job_id = %s", (jr["id"],))
                cur.execute("DELETE FROM review_jobs WHERE folder_id = %s", (fid,))
                cur.execute("DELETE FROM review_folders WHERE id = %s", (fid,))
        self.conn.commit()

    # ---- projects ------------------------------------------------------------

    def create_project(
        self, name: str, job_type: str = "document", *,
        source_lang: str | None = None, target_lang: str | None = None,
        client: str | None = None, vendor: str | None = None,
        deadline: float | None = None, created_by: str | None = None,
    ) -> str:
        project_id = uuid.uuid4().hex[:12]
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO review_projects (id, name, job_type, source_lang, target_lang, "
                "client, vendor, deadline, status, created_at, created_by) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (project_id, name, job_type, source_lang, target_lang, client, vendor,
                 deadline, "created", time.time(), created_by),
            )
        self.conn.commit()
        return project_id

    def set_project_target_lang_if_unset(self, project_id: str, target_lang: str) -> None:
        """Backfill a project's target language from its first translated file,
        so projects created before a language was chosen still show a real
        Source/Target pair once work starts."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE review_projects SET target_lang = %s "
                "WHERE id = %s AND target_lang IS NULL",
                (target_lang, project_id),
            )
        self.conn.commit()

    def delete_project(self, project_id: str) -> None:
        """Remove a project and every file (job) filed under it."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM review_jobs WHERE project_id = %s", (project_id,))
            job_rows = cur.fetchall()
            for jr in job_rows:
                cur.execute(
                    "DELETE FROM review_segment_events WHERE job_id = %s", (jr["id"],)
                )
                cur.execute("DELETE FROM review_segments WHERE job_id = %s", (jr["id"],))
            cur.execute("DELETE FROM review_jobs WHERE project_id = %s", (project_id,))
            cur.execute("DELETE FROM review_folders WHERE project_id = %s", (project_id,))
            cur.execute("DELETE FROM review_projects WHERE id = %s", (project_id,))
        self.conn.commit()

    def get_project(self, project_id: str) -> dict | None:
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM review_projects WHERE id = %s", (project_id,))
            row = cur.fetchone()
        if row is None:
            return None
        return self._project_row_to_dict(row)

    def list_projects(self, created_by: str | list[str] | None = None) -> list[dict]:
        if isinstance(created_by, str):
            created_by = [created_by]
        with self.conn.cursor() as cur:
            if created_by is not None:
                cur.execute(
                    "SELECT * FROM review_projects WHERE created_by = ANY(%s) "
                    "ORDER BY created_at DESC",
                    (list(created_by),),
                )
            else:
                cur.execute("SELECT * FROM review_projects ORDER BY created_at DESC")
            rows = cur.fetchall()
        return [self._project_row_to_dict(r) for r in rows]

    def _project_row_to_dict(self, row) -> dict:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM review_jobs WHERE project_id = %s", (row["id"],))
            job_rows = cur.fetchall()
        counts: dict[str, int] = {}
        for jr in job_rows:
            for status, c in self._status_counts(jr["id"]).items():
                counts[status] = counts.get(status, 0) + c
        return {
            "id": row["id"], "name": row["name"], "job_type": row["job_type"],
            "source_lang": row["source_lang"], "target_lang": row["target_lang"],
            "client": row["client"], "vendor": row["vendor"],
            "deadline": row["deadline"], "status": row["status"],
            "created_at": row["created_at"], "created_by": row["created_by"],
            "file_count": len(job_rows), "status_counts": counts,
        }

    def _status_counts(self, job_id: str) -> dict:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT status, COUNT(*) c FROM review_segments WHERE job_id=%s GROUP BY status",
                (job_id,),
            )
            return {r["status"]: r["c"] for r in cur.fetchall()}

    def get_segments(self, job_id: str, status: str | None = None) -> list[dict]:
        q = "SELECT * FROM review_segments WHERE job_id=%s"
        args: list = [job_id]
        if status:
            q += " AND status=%s"
            args.append(status)
        q += " ORDER BY page, seg_id"
        with self.conn.cursor() as cur:
            cur.execute(q, args)
            return [self._row_to_seg(r) for r in cur.fetchall()]

    def _row_to_seg(self, r) -> dict:
        placeholders = json.loads(r["placeholders_json"])
        target = r["target"]
        restored = _restore(target, placeholders) if target is not None else None
        return {
            "job_id": r["job_id"], "seg_id": r["seg_id"], "page": r["page"],
            "source": r["source"], "source_restored": _restore(r["source"], placeholders),
            "target": target, "target_restored": restored,
            "status": r["status"], "disagreement": bool(r["disagreement"]),
            "has_math_font": bool(r["has_math_font"]), "placeholders": placeholders,
            "notes": json.loads(r["notes_json"]), "approved": bool(r["approved"]),
            "bbox": json.loads(r["bbox_json"]),
        }

    # ---- update / approve ----------------------------------------------------

    def update_segment(self, job_id: str, seg_id: str, target: str, approve: bool, *,
                        reviewer: str = "unknown") -> dict:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM review_segments WHERE job_id=%s AND seg_id=%s", (job_id, seg_id)
            )
            row = cur.fetchone()
            if row is None:
                raise KeyError(f"segment {seg_id} not found in job {job_id}")

            old_target = row["target"]
            notes = json.loads(row["notes_json"])
            ok, detail = integrity.verify(row["source"], target)
            if not ok:
                # A human edit that drops/adds a math token is rejected, same gate as MT.
                status, approved = "needs_human", 0
                notes = _with_note(notes, f"edit rejected: placeholder mismatch ({detail})")
                approve = False
                action = "reject"
            elif approve:
                status, approved = "approved", 1
                action = "approve"
                tm = TranslationMemory(self.tm_path)
                try:
                    tm.store(row["source"], target, engine="human", approved=True)
                finally:
                    tm.close()
            else:
                status, approved = "edited", 0
                action = "edit"

            cur.execute(
                "UPDATE review_segments SET target=%s, status=%s, approved=%s, notes_json=%s "
                "WHERE job_id=%s AND seg_id=%s",
                (target, status, approved, json.dumps(notes, ensure_ascii=False), job_id, seg_id),
            )
            cur.execute(
                "INSERT INTO review_segment_events (job_id, seg_id, action, reviewer, "
                "old_target, new_target, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (job_id, seg_id, action, reviewer, old_target, target, time.time()),
            )
            self.conn.commit()

            cur.execute(
                "SELECT * FROM review_segments WHERE job_id=%s AND seg_id=%s", (job_id, seg_id)
            )
            return self._row_to_seg(cur.fetchone())

    def get_segment_history(self, job_id: str, seg_id: str) -> list[dict]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT action, reviewer, old_target, new_target, created_at "
                "FROM review_segment_events WHERE job_id=%s AND seg_id=%s ORDER BY created_at DESC",
                (job_id, seg_id),
            )
            return cur.fetchall()

    def get_job_history(self, job_id: str) -> list[dict]:
        """Every edit/approve/reject event across all of a document's segments,
        newest first — the per-document audit trail."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT seg_id, action, reviewer, old_target, new_target, created_at "
                "FROM review_segment_events WHERE job_id=%s ORDER BY created_at DESC",
                (job_id,),
            )
            return cur.fetchall()

    def close(self) -> None:
        self.conn.close()


def _restore(text: str, placeholders: dict[str, str]) -> str:
    for token, literal in placeholders.items():
        text = text.replace(token, literal)
    return text


def _with_note(notes: list[str], note: str) -> list[str]:
    return notes + [note] if note not in notes else notes
