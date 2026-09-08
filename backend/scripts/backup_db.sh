#!/usr/bin/env bash
# Online, atomic backup of the babel SQLite databases via VACUUM INTO.
# Safe to run against a live server (WAL mode allows concurrent readers/writers).
#
# Usage: ./backup_db.sh [backup_dir]
# Env:   BABEL_REVIEW_DB, BABEL_TM_DB (default: babel_review.db, babel_tm.db in cwd)

set -euo pipefail

BACKUP_DIR="${1:-backups}"
REVIEW_DB="${BABEL_REVIEW_DB:-babel_review.db}"
TM_DB="${BABEL_TM_DB:-babel_tm.db}"
TIMESTAMP="$(date +%Y%m%d%H%M%S)"

mkdir -p "$BACKUP_DIR"

if [ -f "$REVIEW_DB" ]; then
    sqlite3 "$REVIEW_DB" "VACUUM INTO '${BACKUP_DIR}/babel_review-${TIMESTAMP}.db'"
    echo "backed up $REVIEW_DB -> ${BACKUP_DIR}/babel_review-${TIMESTAMP}.db"
else
    echo "skip: $REVIEW_DB not found"
fi

if [ -f "$TM_DB" ]; then
    sqlite3 "$TM_DB" "VACUUM INTO '${BACKUP_DIR}/babel_tm-${TIMESTAMP}.db'"
    echo "backed up $TM_DB -> ${BACKUP_DIR}/babel_tm-${TIMESTAMP}.db"
else
    echo "skip: $TM_DB not found"
fi

# Prune backups older than 30 days.
find "$BACKUP_DIR" -name 'babel_*.db' -mtime +30 -delete
