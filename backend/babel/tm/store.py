"""Translation memory: SQLite store keyed by a hash of the protected source.

This is the accuracy-compounding engine. Once a segment is translated (and,
later, human-approved), the same source text anywhere across thousands of docs
reuses the exact same target — so "ratio" is never "razón" on page 2 and
"proporción" on page 30.

Keying on the *protected* source (math already placeholdered) means numerically
different problems that share the same prose skeleton collapse to one TM entry,
maximizing reuse.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tm (
    key        TEXT PRIMARY KEY,   -- sha1(source_lang|target_lang|source)
    source     TEXT NOT NULL,
    target     TEXT NOT NULL,
    source_lang TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    engine     TEXT,
    approved   INTEGER NOT NULL DEFAULT 0,  -- 1 once a human confirms
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _key(source: str, src_lang: str, tgt_lang: str) -> str:
    h = hashlib.sha1(f"{src_lang}|{tgt_lang}|{source}".encode("utf-8"))
    return h.hexdigest()


class TranslationMemory:
    def __init__(self, path: str = "babel_tm.db", src_lang: str = "en", tgt_lang: str = "es"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute(_SCHEMA)
        self.conn.commit()
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang

    def lookup(self, source: str) -> Optional[tuple[str, bool]]:
        """Return (target, approved) if a TM entry exists, else None."""
        cur = self.conn.execute(
            "SELECT target, approved FROM tm WHERE key = ?",
            (_key(source, self.src_lang, self.tgt_lang),),
        )
        row = cur.fetchone()
        return (row[0], bool(row[1])) if row else None

    def store(self, source: str, target: str, engine: str | None = None, approved: bool = False) -> None:
        self.conn.execute(
            """INSERT INTO tm (key, source, target, source_lang, target_lang, engine, approved)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(key) DO UPDATE SET
                   target=excluded.target,
                   engine=excluded.engine,
                   approved=MAX(tm.approved, excluded.approved),
                   updated_at=datetime('now')""",
            (
                _key(source, self.src_lang, self.tgt_lang),
                source, target, self.src_lang, self.tgt_lang, engine, int(approved),
            ),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
