"""Supabase auth: verifies the bearer token on protected endpoints and checks
trial status. No JWT secret needed — we ask Supabase's own /auth/v1/user
endpoint to validate the token, which also means a revoked/expired token is
rejected immediately rather than trusting a locally-cached signing key.
"""

from __future__ import annotations

import os
import time

import requests
from fastapi import HTTPException, Request

from babel.config import load_env

load_env()

_SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
_SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
_SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Short-lived per-token cache so a page that fires several requests in a row
# doesn't round-trip to Supabase for every one of them.
_TOKEN_CACHE_TTL = 30.0
_token_cache: dict[str, tuple[float, dict]] = {}


def _extract_token(request: Request) -> str | None:
    # Header only — a session token in the query string would end up in
    # server access logs, browser history, and Referer headers.
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def require_user(request: Request) -> dict:
    """FastAPI dependency: returns {"id": ..., "email": ...} or raises 401."""
    if not _SUPABASE_URL or not _SUPABASE_ANON_KEY:
        raise HTTPException(status_code=500, detail="Supabase is not configured on the server")

    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    cached = _token_cache.get(token)
    if cached and cached[0] > time.monotonic():
        return cached[1]

    resp = requests.get(
        f"{_SUPABASE_URL}/auth/v1/user",
        headers={"Authorization": f"Bearer {token}", "apikey": _SUPABASE_ANON_KEY},
        timeout=10,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    body = resp.json()
    user = {"id": body["id"], "email": body.get("email")}
    _token_cache[token] = (time.monotonic() + _TOKEN_CACHE_TTL, user)
    return user


def _create_profile(user: dict) -> str:
    """Inserts a fresh 14-day-trial profile row for a user who doesn't have
    one yet, and returns its trial_ends_at. Uses upsert so a concurrent
    request creating the same row races safely instead of erroring."""
    from datetime import datetime, timedelta, timezone

    trial_ends_at = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    resp = requests.post(
        f"{_SUPABASE_URL}/rest/v1/profiles",
        params={"on_conflict": "id"},
        json={"id": user["id"], "email": user.get("email"), "trial_ends_at": trial_ends_at},
        headers={
            "apikey": _SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {_SUPABASE_SERVICE_ROLE_KEY}",
            "Prefer": "resolution=ignore-duplicates,return=representation",
        },
        timeout=10,
    )
    resp.raise_for_status()
    rows = resp.json()
    if rows:
        return rows[0]["trial_ends_at"]
    # Another request created it first (ignore-duplicates -> empty body) —
    # re-fetch to get the row that actually won the race.
    refetch = requests.get(
        f"{_SUPABASE_URL}/rest/v1/profiles",
        params={"id": f"eq.{user['id']}", "select": "trial_ends_at"},
        headers={
            "apikey": _SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {_SUPABASE_SERVICE_ROLE_KEY}",
        },
        timeout=10,
    )
    refetch.raise_for_status()
    refetched = refetch.json()
    if not refetched:
        raise HTTPException(status_code=500, detail="Failed to initialize trial")
    return refetched[0]["trial_ends_at"]


def require_trial_active(user: dict) -> None:
    """Raises 402 once the user's 14-day trial has passed. Call this from
    endpoints that spend LLM/API budget (translate, rebuild) — not from
    plain reads."""
    if not _SUPABASE_URL or not _SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=500, detail="Supabase is not configured on the server")

    resp = requests.get(
        f"{_SUPABASE_URL}/rest/v1/profiles",
        params={"id": f"eq.{user['id']}", "select": "trial_ends_at"},
        headers={
            "apikey": _SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {_SUPABASE_SERVICE_ROLE_KEY}",
        },
        timeout=10,
    )
    resp.raise_for_status()
    rows = resp.json()
    if not rows or not rows[0].get("trial_ends_at"):
        # No profile row yet — either the signup trigger hasn't run yet (a
        # brand-new account, split-second race) or it was never installed.
        # Fail closed either way, but self-heal: create a normal 14-day
        # trial server-side rather than either blocking forever or (the
        # bug this replaces) granting unmetered access forever.
        trial_ends_at = _create_profile(user)
    else:
        trial_ends_at = rows[0]["trial_ends_at"]
    # Postgres returns e.g. "2026-09-22T10:00:00+00:00"
    from datetime import datetime

    ends = datetime.fromisoformat(trial_ends_at.replace("Z", "+00:00"))
    if ends.timestamp() < time.time():
        raise HTTPException(
            status_code=402,
            detail="Your 14-day trial has ended. Contact us to keep translating.",
        )
