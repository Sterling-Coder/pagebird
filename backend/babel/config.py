"""Environment loading. Import this before reading any API-key env vars.

Loads a local `.env` (gitignored) if present so keys don't have to live in the
shell. No-op when python-dotenv isn't installed or no .env exists.
"""

from __future__ import annotations

import os

_loaded = False


def load_env() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    # Look for .env in the backend root (two levels up from this file).
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(root, ".env"))
