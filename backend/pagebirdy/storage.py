"""Backblaze B2 (S3-compatible) — where uploaded and translated files actually
live. Postgres (`review_jobs`/`review_segments`, see `review/store.py`) never
holds file bytes, only the key this module returns from `upload_file`.

Railway's container disk is ephemeral: it resets to empty on every
redeploy. Local paths (uploads/, out/) are scratch space only, used while a
job is actively processing; the durable copy of every job's original upload
and its translated output lives here, keyed by job id (`jobs/<job_id>/…`).

The client is plain boto3 against B2's S3-compatible endpoint, so any other
S3-compatible provider (Railway's own bucket, R2, MinIO, ...) works too —
only the env below needs to point elsewhere; nothing here is B2-specific.

Env (from the B2 bucket's "S3 Compatible" tab — Application Key ID / Key are
the access/secret key pair, scoped to just this bucket):
  PAGEBIRDY_S3_ENDPOINT     e.g. https://s3.us-west-004.backblazeb2.com
  PAGEBIRDY_S3_BUCKET       bucket name
  PAGEBIRDY_S3_ACCESS_KEY   B2 Application Key ID
  PAGEBIRDY_S3_SECRET_KEY   B2 Application Key
  PAGEBIRDY_S3_REGION       e.g. "us-west-004" — must match the endpoint's
                         region; B2 rejects "auto"

Unlike an optional engine, storage is not best-effort: a job whose files were
never persisted is not downloadable once the container restarts. So an
upload with no bucket configured, or one the bucket refuses, raises — the
caller (`api._upload_with_retry`) retries and then marks the job failed.
"""

from __future__ import annotations

import logging
import mimetypes
import os
import threading

from pagebirdy.config import load_env

load_env()

logger = logging.getLogger("pagebirdy.storage")

_client = None
_client_lock = threading.Lock()


def _region_from_endpoint(endpoint: str) -> str:
    """B2's own endpoint names its region: `s3.us-west-004.backblazeb2.com`
    -> `us-west-004`. A fallback for a bucket wired up with only the
    endpoint set — unlike AWS, B2 has no "auto"; a wrong or missing region
    is a signature failure on every request, not a slow one, so this is
    worth deriving rather than leaving the caller to hit that blind."""
    host = endpoint.split("//", 1)[-1].split("/", 1)[0]
    parts = host.split(".")
    return parts[1] if len(parts) >= 4 and parts[0] == "s3" else ""


def _cfg() -> dict:
    endpoint = os.environ.get("PAGEBIRDY_S3_ENDPOINT", "")
    return {
        "endpoint": endpoint,
        "bucket": os.environ.get("PAGEBIRDY_S3_BUCKET", ""),
        "access_key": os.environ.get("PAGEBIRDY_S3_ACCESS_KEY", ""),
        "secret_key": os.environ.get("PAGEBIRDY_S3_SECRET_KEY", ""),
        "region": os.environ.get("PAGEBIRDY_S3_REGION", "") or _region_from_endpoint(endpoint),
    }


def enabled() -> bool:
    c = _cfg()
    return bool(c["endpoint"] and c["bucket"] and c["access_key"] and c["secret_key"])


def _bucket() -> str:
    return _cfg()["bucket"]


def _get_client():
    """Lazily built, cached boto3 client. Only a successful build is cached,
    so one transient failure does not disable storage for the process."""
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is not None:
            return _client
        if not enabled():
            raise RuntimeError(
                "storage is not configured: set PAGEBIRDY_S3_ENDPOINT, PAGEBIRDY_S3_BUCKET, "
                "PAGEBIRDY_S3_ACCESS_KEY and PAGEBIRDY_S3_SECRET_KEY")
        c = _cfg()
        if not c["region"]:
            raise RuntimeError(
                "storage: could not determine a region — set PAGEBIRDY_S3_REGION "
                f"(endpoint {c['endpoint']!r} doesn't match B2's s3.<region>.backblazeb2.com)")
        import boto3
        from botocore.config import Config

        _client = boto3.client(
            "s3",
            endpoint_url=c["endpoint"],
            aws_access_key_id=c["access_key"],
            aws_secret_access_key=c["secret_key"],
            region_name=c["region"],
            config=Config(signature_version="s3v4",
                          retries={"max_attempts": 3, "mode": "standard"}),
        )
    return _client


def _missing(error) -> bool:
    """Is this botocore error a plain "no such object"?"""
    code = str(getattr(error, "response", {}).get("Error", {}).get("Code", ""))
    return code in ("404", "NoSuchKey", "NotFound")


def ensure_bucket() -> None:
    """Kept for callers of the old Supabase module. A Railway bucket is
    created on the platform, never by the app, so there is nothing to do."""


def upload_file(local_path: str, key: str) -> str:
    """Uploads a local file to the bucket under `key`, overwriting any
    existing object there. Returns `key` (what gets stored in the DB).
    Raises when the upload does not happen."""
    content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    _get_client().upload_file(local_path, _bucket(), key,
                              ExtraArgs={"ContentType": content_type})
    return key


def download_to(key: str, local_path: str) -> bool:
    """Downloads object `key` to `local_path`. Returns False (and writes
    nothing) if the object doesn't exist — callers treat that as 404."""
    from botocore.exceptions import ClientError

    os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
    partial = local_path + ".part"
    try:
        _get_client().download_file(_bucket(), key, partial)
    except ClientError as e:
        if os.path.exists(partial):
            os.remove(partial)
        if _missing(e):
            return False
        raise
    os.replace(partial, local_path)
    return True


def read_bytes(key: str) -> bytes | None:
    """Reads an object straight into memory — for streaming a download
    response without an intermediate temp file. None if it doesn't exist."""
    from botocore.exceptions import ClientError

    try:
        obj = _get_client().get_object(Bucket=_bucket(), Key=key)
    except ClientError as e:
        if _missing(e):
            return None
        raise
    return obj["Body"].read()


def delete(key: str) -> None:
    _get_client().delete_object(Bucket=_bucket(), Key=key)


def list_prefix(prefix: str) -> list[str]:
    """Names (not full keys) directly under `prefix` — files, plus the names
    of any subfolders — the same one-level listing the old Supabase module
    returned."""
    names: list[str] = []
    paginator = _get_client().get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=_bucket(), Prefix=prefix, Delimiter="/"):
        for obj in page.get("Contents", []):
            name = obj["Key"][len(prefix):]
            if name:
                names.append(name)
        for sub in page.get("CommonPrefixes", []):
            name = sub["Prefix"][len(prefix):].rstrip("/")
            if name:
                names.append(name)
    return names


def _list_recursive(prefix: str) -> list[str]:
    """Every object key under `prefix`, subfolders included."""
    keys: list[str] = []
    paginator = _get_client().get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=_bucket(), Prefix=prefix):
        keys.extend(obj["Key"] for obj in page.get("Contents", []))
    return keys


def delete_prefix(prefix: str) -> None:
    """Deletes every object under `prefix` (a job's whole folder, e.g. when
    the job itself is deleted), including nested subfolders such as a links
    job's `Links/` and `Links_<lang>/`.

    A prefix is only trusted when it names one folder inside a top-level one
    (`jobs/<id>/`): anything shorter, or with an empty segment (`jobs//`,
    from an empty id), would match every job in the bucket."""
    parts = prefix.split("/")
    if (not prefix.endswith("/") or len(parts) < 3
            or any(part == "" for part in parts[:-1])):
        raise ValueError(f"refusing to delete unscoped prefix {prefix!r}")
    keys = _list_recursive(prefix)
    client = _get_client()
    for i in range(0, len(keys), 1000):
        chunk = keys[i:i + 1000]
        resp = client.delete_objects(
            Bucket=_bucket(),
            Delete={"Objects": [{"Key": k} for k in chunk], "Quiet": True})
        for err in resp.get("Errors", []):
            logger.error("storage: delete failed for %s: %s", err.get("Key"), err.get("Message"))
