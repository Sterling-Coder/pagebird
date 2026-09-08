"""Review store: persists a translation job's segments so the human-review UI
has something to load, edit, and approve.

This is what turns "MT output" into "high accuracy": every segment the pipeline
was unsure about (needs_human, disagreement, glossary miss) surfaces here for a
person to fix, and every approval writes back to the shared translation memory
so the correction is reused everywhere.

Schema (SQLite):
  jobs(id, source, output, created_at, meta_json)
  segments(job_id, seg_id, page, source, target, status, disagreement,
           has_math_font, placeholders_json, bbox_json, notes_json, approved)
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict
from pathlib import Path

from babel.models import Segment
from babel.tm.store import TranslationMemory
from babel.translate import integrity

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    job_type TEXT NOT NULL DEFAULT 'document',
    source_lang TEXT,
    target_lang TEXT,
    client TEXT,
    vendor TEXT,
    deadline REAL,
    status TEXT NOT NULL DEFAULT 'created',
    created_at REAL NOT NULL,
    created_by TEXT
);
CREATE TABLE IF NOT EXISTS folders (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    parent_folder_id TEXT,
    created_at REAL NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY, source TEXT, output TEXT,
    created_at REAL, meta_json TEXT
);
CREATE TABLE IF NOT EXISTS segments (
    job_id TEXT, seg_id TEXT, page INTEGER, source TEXT, target TEXT,
    status TEXT, disagreement INTEGER, has_math_font INTEGER,
    placeholders_json TEXT, bbox_json TEXT, notes_json TEXT, approved INTEGER,
    PRIMARY KEY (job_id, seg_id)
);
CREATE TABLE IF NOT EXISTS segment_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    seg_id TEXT NOT NULL,
    action TEXT NOT NULL,
    reviewer TEXT NOT NULL DEFAULT 'unknown',
    old_target TEXT,
    new_target TEXT,
    created_at REAL NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
CREATE INDEX IF NOT EXISTS idx_segment_events_job_seg ON segment_events(job_id, seg_id);
CREATE INDEX IF NOT EXISTS idx_segments_job_status ON segments(job_id, status);
"""

_JOB_COLUMNS = [
    ("original_filename", "TEXT"),
    ("file_hash", "TEXT"),
    ("file_size", "INTEGER"),
    ("duration_sec", "REAL"),
    ("status", "TEXT DEFAULT 'complete'"),
    ("error", "TEXT"),
    ("project_id", "TEXT"),
    ("job_type", "TEXT DEFAULT 'document'"),
    ("folder_id", "TEXT"),
    ("created_by", "TEXT"),
]


class ReviewStore:
    """Review store: persists a translation job's segments so the human-review
    UI has something to load, edit, and approve.

    `segments.job_id` is a logical (unenforced) reference to `jobs.id` — SQLite
    can't add a FK constraint to an already-populated table without a rebuild,
    which is out of scope here. `segment_events.job_id` is a new table and does
    enforce the FK.
    """

    def __init__(self, path: str = "babel_review.db", tm_path: str = "babel_tm.db"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = __import__("sqlite3").connect(path)
        self.conn.row_factory = __import__("sqlite3").Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(_SCHEMA)
        for name, coltype in _JOB_COLUMNS:
            self._ensure_column("jobs", name, coltype)
        self._ensure_column("folders", "parent_folder_id", "TEXT")
        self.conn.commit()
        self.tm_path = tm_path

    def _ensure_column(self, table: str, name: str, coltype: str) -> None:
        cols = {r[1] for r in self.conn.execute(f"PRAGMA table_info({table})")}
        if name not in cols:
            self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {coltype}")

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
        self.conn.execute(
            "INSERT INTO jobs (id, source, output, created_at, meta_json, "
            "original_filename, file_hash, file_size, duration_sec, status, error, "
            "project_id, job_type, folder_id, created_by) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (job_id, source, output, time.time(), json.dumps(meta, ensure_ascii=False),
             original_filename, file_hash, file_size, duration_sec, status, error,
             project_id, job_type, folder_id, created_by),
        )
        for s in segments:
            if not s.is_translatable:
                continue  # empty/whitespace-only segments aren't reviewable
            self.conn.execute(
                """INSERT INTO segments VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
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
        """Repoint a job's stored source/output paths (e.g. after INDD conversion
        or export swaps the intermediate .idml for the final .indd)."""
        if source is not None:
            self.conn.execute("UPDATE jobs SET source = ? WHERE id = ?", (source, job_id))
        if output is not None:
            self.conn.execute("UPDATE jobs SET output = ? WHERE id = ?", (output, job_id))
        self.conn.commit()

    def delete_job(self, job_id: str) -> None:
        """Remove a job and its segments (e.g. a translate succeeded but a later
        export step failed, leaving a job row that shouldn't be browsable/downloadable)."""
        self.conn.execute("DELETE FROM segment_events WHERE job_id = ?", (job_id,))
        self.conn.execute("DELETE FROM segments WHERE job_id = ?", (job_id,))
        self.conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        self.conn.commit()

    # ---- read ----------------------------------------------------------------

    def list_jobs(self, created_by: str | list[str] | None = None) -> list[dict]:
        if isinstance(created_by, str):
            created_by = [created_by]
        if created_by is not None:
            placeholders = ",".join("?" for _ in created_by)
            rows = self.conn.execute(
                "SELECT id, source, output, created_at, meta_json, original_filename, "
                "file_hash, file_size, duration_sec, status, error, project_id, job_type, "
                f"folder_id, created_by FROM jobs WHERE created_by IN ({placeholders}) "
                "ORDER BY created_at DESC",
                tuple(created_by),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT id, source, output, created_at, meta_json, original_filename, "
                "file_hash, file_size, duration_sec, status, error, project_id, job_type, "
                "folder_id, created_by FROM jobs ORDER BY created_at DESC"
            ).fetchall()
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
        self.conn.execute(
            "INSERT INTO folders (id, project_id, name, parent_folder_id, created_at) "
            "VALUES (?,?,?,?,?)",
            (folder_id, project_id, name, parent_folder_id, time.time()),
        )
        self.conn.commit()
        return folder_id

    def list_folders(self, project_id: str,
                      parent_folder_id: str | None = None) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, project_id, name, parent_folder_id, created_at FROM folders "
            "WHERE project_id = ? AND parent_folder_id IS ? ORDER BY created_at DESC",
            (project_id, parent_folder_id),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_folder(self, folder_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT id, project_id, name, parent_folder_id, created_at "
            "FROM folders WHERE id = ?",
            (folder_id,),
        ).fetchone()
        return dict(row) if row is not None else None

    def delete_folder(self, folder_id: str) -> None:
        """Remove a folder, every file (job) filed under it, and every
        subfolder (recursively) beneath it."""
        stack = [folder_id]
        all_folder_ids: list[str] = []
        while stack:
            fid = stack.pop()
            all_folder_ids.append(fid)
            children = self.conn.execute(
                "SELECT id FROM folders WHERE parent_folder_id = ?", (fid,)
            ).fetchall()
            stack.extend(c["id"] for c in children)

        for fid in all_folder_ids:
            job_rows = self.conn.execute(
                "SELECT id FROM jobs WHERE folder_id = ?", (fid,)
            ).fetchall()
            for jr in job_rows:
                self.conn.execute("DELETE FROM segment_events WHERE job_id = ?", (jr["id"],))
                self.conn.execute("DELETE FROM segments WHERE job_id = ?", (jr["id"],))
            self.conn.execute("DELETE FROM jobs WHERE folder_id = ?", (fid,))
            self.conn.execute("DELETE FROM folders WHERE id = ?", (fid,))
        self.conn.commit()

    # ---- projects ------------------------------------------------------------

    def create_project(
        self, name: str, job_type: str = "document", *,
        source_lang: str | None = None, target_lang: str | None = None,
        client: str | None = None, vendor: str | None = None,
        deadline: float | None = None, created_by: str | None = None,
    ) -> str:
        project_id = uuid.uuid4().hex[:12]
        self.conn.execute(
            "INSERT INTO projects (id, name, job_type, source_lang, target_lang, "
            "client, vendor, deadline, status, created_at, created_by) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (project_id, name, job_type, source_lang, target_lang, client, vendor,
             deadline, "created", time.time(), created_by),
        )
        self.conn.commit()
        return project_id

    def set_project_target_lang_if_unset(self, project_id: str, target_lang: str) -> None:
        """Backfill a project's target language from its first translated file,
        so projects created before a language was chosen still show a real
        Source/Target pair once work starts."""
        self.conn.execute(
            "UPDATE projects SET target_lang = ? WHERE id = ? AND target_lang IS NULL",
            (target_lang, project_id),
        )
        self.conn.commit()

    def delete_project(self, project_id: str) -> None:
        """Remove a project and every file (job) filed under it."""
        job_rows = self.conn.execute(
            "SELECT id FROM jobs WHERE project_id = ?", (project_id,)
        ).fetchall()
        for jr in job_rows:
            self.conn.execute("DELETE FROM segment_events WHERE job_id = ?", (jr["id"],))
            self.conn.execute("DELETE FROM segments WHERE job_id = ?", (jr["id"],))
        self.conn.execute("DELETE FROM jobs WHERE project_id = ?", (project_id,))
        self.conn.execute("DELETE FROM folders WHERE project_id = ?", (project_id,))
        self.conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self.conn.commit()

    def get_project(self, project_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if row is None:
            return None
        return self._project_row_to_dict(row)

    def list_projects(self, created_by: str | list[str] | None = None) -> list[dict]:
        if isinstance(created_by, str):
            created_by = [created_by]
        if created_by is not None:
            placeholders = ",".join("?" for _ in created_by)
            rows = self.conn.execute(
                f"SELECT * FROM projects WHERE created_by IN ({placeholders}) "
                "ORDER BY created_at DESC",
                tuple(created_by),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM projects ORDER BY created_at DESC"
            ).fetchall()
        return [self._project_row_to_dict(r) for r in rows]

    def _project_row_to_dict(self, row) -> dict:
        job_rows = self.conn.execute(
            "SELECT id FROM jobs WHERE project_id = ?", (row["id"],)
        ).fetchall()
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
        rows = self.conn.execute(
            "SELECT status, COUNT(*) c FROM segments WHERE job_id=? GROUP BY status",
            (job_id,),
        ).fetchall()
        return {r["status"]: r["c"] for r in rows}

    def get_segments(self, job_id: str, status: str | None = None) -> list[dict]:
        q = "SELECT * FROM segments WHERE job_id=?"
        args: list = [job_id]
        if status:
            q += " AND status=?"
            args.append(status)
        q += " ORDER BY page, seg_id"
        return [self._row_to_seg(r) for r in self.conn.execute(q, args).fetchall()]

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
        row = self.conn.execute(
            "SELECT * FROM segments WHERE job_id=? AND seg_id=?", (job_id, seg_id)
        ).fetchone()
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

        self.conn.execute(
            "UPDATE segments SET target=?, status=?, approved=?, notes_json=? "
            "WHERE job_id=? AND seg_id=?",
            (target, status, approved, json.dumps(notes, ensure_ascii=False), job_id, seg_id),
        )
        self.conn.execute(
            "INSERT INTO segment_events (job_id, seg_id, action, reviewer, old_target, "
            "new_target, created_at) VALUES (?,?,?,?,?,?,?)",
            (job_id, seg_id, action, reviewer, old_target, target, time.time()),
        )
        self.conn.commit()
        return self._row_to_seg(
            self.conn.execute(
                "SELECT * FROM segments WHERE job_id=? AND seg_id=?", (job_id, seg_id)
            ).fetchone()
        )

    def get_segment_history(self, job_id: str, seg_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT action, reviewer, old_target, new_target, created_at "
            "FROM segment_events WHERE job_id=? AND seg_id=? ORDER BY created_at DESC",
            (job_id, seg_id),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_job_history(self, job_id: str) -> list[dict]:
        """Every edit/approve/reject event across all of a document's segments,
        newest first — the per-document audit trail."""
        rows = self.conn.execute(
            "SELECT seg_id, action, reviewer, old_target, new_target, created_at "
            "FROM segment_events WHERE job_id=? ORDER BY created_at DESC",
            (job_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()


def _restore(text: str, placeholders: dict[str, str]) -> str:
    for token, literal in placeholders.items():
        text = text.replace(token, literal)
    return text


def _with_note(notes: list[str], note: str) -> list[str]:
    return notes + [note] if note not in notes else notes
