"""Supabase Storage — where uploaded and translated files actually live.

Railway's container disk is ephemeral: it resets to empty on every
redeploy. Local paths (uploads/, out/) are now scratch space only, used
while a job is actively processing; the durable copy lives here, in a
private Supabase Storage bucket, keyed by job id.
"""

from __future__ import annotations

import mimetypes
import os

import requests

from pagebirdy.config import load_env

load_env()

_SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
_SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
_BUCKET = os.environ.get("BABEL_STORAGE_BUCKET", "documents")

_bucket_ready = False


def _headers(**extra: str) -> dict:
    return {
        "apikey": _SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {_SUPABASE_SERVICE_ROLE_KEY}",
        **extra,
    }


def ensure_bucket() -> None:
    """Creates the storage bucket if it doesn't exist yet. Idempotent —
    call at startup; a 400 "already exists" is not an error here."""
    global _bucket_ready
    if _bucket_ready:
        return
    if not _SUPABASE_URL or not _SUPABASE_SERVICE_ROLE_KEY:
        return
    requests.post(
        f"{_SUPABASE_URL}/storage/v1/bucket",
        json={"id": _BUCKET, "name": _BUCKET, "public": False},
        headers=_headers(),
        timeout=10,
    )
    _bucket_ready = True


def upload_file(local_path: str, key: str) -> str:
    """Uploads a local file to the bucket under `key`, overwriting any
    existing object there. Returns `key` (what gets stored in the DB)."""
    ensure_bucket()
    content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    with open(local_path, "rb") as f:
        resp = requests.post(
            f"{_SUPABASE_URL}/storage/v1/object/{_BUCKET}/{key}",
            data=f,
            headers=_headers(**{"Content-Type": content_type, "x-upsert": "true"}),
            timeout=120,
        )
    resp.raise_for_status()
    return key


def download_to(key: str, local_path: str) -> bool:
    """Downloads object `key` to `local_path`. Returns False (and writes
    nothing) if the object doesn't exist — callers treat that as 404."""
    resp = requests.get(
        f"{_SUPABASE_URL}/storage/v1/object/{_BUCKET}/{key}",
        headers=_headers(),
        timeout=120,
    )
    if resp.status_code in (400, 404):
        return False
    resp.raise_for_status()
    os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(resp.content)
    return True


def read_bytes(key: str) -> bytes | None:
    """Reads an object straight into memory — for streaming a download
    response without an intermediate temp file. None if it doesn't exist."""
    resp = requests.get(
        f"{_SUPABASE_URL}/storage/v1/object/{_BUCKET}/{key}",
        headers=_headers(),
        timeout=120,
    )
    if resp.status_code in (400, 404):
        return None
    resp.raise_for_status()
    return resp.content


def delete(key: str) -> None:
    requests.delete(
        f"{_SUPABASE_URL}/storage/v1/object/{_BUCKET}/{key}",
        headers=_headers(),
        timeout=30,
    )


def list_prefix(prefix: str) -> list[str]:
    """Lists object names (not full keys) directly under `prefix` — a
    single non-recursive listing, matching Supabase Storage's own semantics
    (see `delete_prefix` for the same list call used to build the delete
    payload)."""
    resp = requests.post(
        f"{_SUPABASE_URL}/storage/v1/object/list/{_BUCKET}",
        json={"prefix": prefix},
        headers=_headers(),
        timeout=30,
    )
    if resp.status_code != 200:
        return []
    return [item["name"] for item in resp.json() if item.get("name")]


def _list_recursive(prefix: str) -> list[str]:
    """Lists every real object key under `prefix`, walking into subfolders
    (Supabase Storage's list endpoint is non-recursive — a subfolder comes
    back as a pseudo-entry with `id: null`, not its files)."""
    resp = requests.post(
        f"{_SUPABASE_URL}/storage/v1/object/list/{_BUCKET}",
        json={"prefix": prefix},
        headers=_headers(),
        timeout=30,
    )
    if resp.status_code != 200:
        return []
    keys: list[str] = []
    for item in resp.json():
        name = item.get("name")
        if not name:
            continue
        full = f"{prefix}{name}"
        if item.get("id") is None:
            keys.extend(_list_recursive(f"{full}/"))
        else:
            keys.append(full)
    return keys


def delete_prefix(prefix: str) -> None:
    """Deletes every object under `prefix` (a job's whole folder, e.g. when
    the job itself is deleted), including nested subfolders such as a links
    job's `Links/` and `Links_<lang>/` — see `_list_recursive`. The old
    version only listed one level deep, so a links job's nested files were
    never actually deleted (left orphaned in storage) and listing kept
    growing slower over time."""
    names = _list_recursive(prefix)
    for i in range(0, len(names), 1000):
        chunk = names[i:i + 1000]
        requests.delete(
            f"{_SUPABASE_URL}/storage/v1/object/{_BUCKET}",
            json={"prefixes": chunk},
            headers=_headers(),
            timeout=60,
        )
