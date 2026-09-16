"""Environment loading. Import this before reading any API-key env vars.

Loads a local `.env` (gitignored) if present so keys don't have to live in the
shell. No-op when python-dotenv isn't installed or no .env exists.
"""

from __future__ import annotations

import os
import tempfile

_loaded = False


def load_env() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    try:
        from dotenv import load_dotenv
    except ImportError:
        pass
    else:
        # Look for .env in the backend root (two levels up from this file).
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        load_dotenv(os.path.join(root, ".env"))

    _materialize_google_credentials()


def _materialize_google_credentials() -> None:
    """Railway (and most PaaS) have no file-upload for secrets — only env
    vars. Locally, GOOGLE_APPLICATION_CREDENTIALS is a path to the service
    account JSON on disk. In prod, set GOOGLE_CREDENTIALS_JSON to the raw
    contents of that JSON file instead; this writes it to a temp file once
    per process and points GOOGLE_APPLICATION_CREDENTIALS at it, so the rest
    of the code (which only ever reads GOOGLE_APPLICATION_CREDENTIALS as a
    path) doesn't need to know the difference."""
    raw = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not raw:
        return
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return  # explicit path already set — don't override it
    fd, path = tempfile.mkstemp(prefix="gcp-sa-", suffix=".json")
    with os.fdopen(fd, "w") as f:
        f.write(raw)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
