"""/api/me (name, picture) and /api/team/invite.

Auth is faked and every Supabase call goes to an in-test fake that records
requests, so nothing reaches the real project or bucket."""

import io

import pytest
import requests
from fastapi.testclient import TestClient

import pagebirdy.api as api
from pagebirdy import auth

BASE = "https://fake-project.supabase.test"
USER = {"id": "11111111-1111-4111-8111-111111111111", "email": "owner@example.com"}
OTHER_ID = "22222222-2222-4222-8222-222222222222"
STRANGER_ID = "33333333-3333-4333-8333-333333333333"

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


class FakeResponse:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self._body = body if body is not None else []
        self.text = str(self._body)

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")


class FakeSupabase:
    """Routes (method, path) to a handler; records every call."""

    def __init__(self):
        self.calls: list[tuple[str, str, dict]] = []
        self.profile = {"email": USER["email"], "created_at": "2026-09-01T00:00:00+00:00",
                        "trial_ends_at": "2099-01-01T00:00:00+00:00", "first_name": "Old",
                        "last_name": "Name", "full_name": "Old Name", "avatar_url": None}
        self.routes: dict[tuple[str, str], object] = {}

    def on(self, method, path, handler):
        self.routes[(method, path)] = handler

    def __call__(self, method, url, **kwargs):
        method = method.upper()
        path = url[len(BASE):].split("?")[0]
        self.calls.append((method, path, kwargs))
        handler = self.routes.get((method, path))
        if handler is None:
            for (m, p), h in self.routes.items():
                if m == method and p.endswith("*") and path.startswith(p[:-1]):
                    handler = h
                    break
        if handler is None:
            if (method, path) == ("GET", "/rest/v1/profiles"):
                return FakeResponse(200, [dict(self.profile)])
            if (method, path) == ("PATCH", "/rest/v1/profiles"):
                self.profile.update(kwargs.get("json") or {})
                return FakeResponse(200, [dict(self.profile)])
            return FakeResponse(200, [])
        return handler(method, url, **kwargs) if callable(handler) else handler

    def find(self, method, path):
        return [c for c in self.calls if c[0] == method and c[1] == path]


@pytest.fixture
def sb(monkeypatch):
    fake = FakeSupabase()
    monkeypatch.setenv("SUPABASE_URL", BASE)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fake-service-key")
    monkeypatch.delenv("PAGEBIRDY_AVATAR_BUCKET", raising=False)
    monkeypatch.setattr(auth, "_SUPABASE_URL", BASE)
    monkeypatch.setattr(auth, "_SUPABASE_SERVICE_ROLE_KEY", "fake-service-key")
    monkeypatch.setattr(requests, "request", fake)
    for verb in ("get", "post", "patch", "put", "delete"):
        monkeypatch.setattr(requests, verb, lambda url, _v=verb, **kw: fake(_v, url, **kw))
    monkeypatch.setitem(api.app.dependency_overrides, api.require_user, lambda: dict(USER))
    return fake


@pytest.fixture
def client(sb):
    return TestClient(api.app)


# --- /api/me --------------------------------------------------------------

def test_get_me_includes_avatar_url(client, sb):
    sb.profile["avatar_url"] = f"{BASE}/storage/v1/object/public/avatars/{USER['id']}/a.png"
    r = client.get("/api/me")
    assert r.status_code == 200, r.text
    assert r.json()["avatar_url"] == sb.profile["avatar_url"]
    assert r.json()["full_name"] == "Old Name"


def test_get_me_works_before_avatar_migration(client, sb):
    """Without profiles.avatar_url PostgREST rejects the select; /api/me must
    still load (minus the photo) rather than fail every page."""
    def profiles(method, url, **kw):
        if "avatar_url" in kw["params"]["select"]:
            return FakeResponse(400, {"code": "42703", "message": "column profiles.avatar_url does not exist"})
        row = {k: v for k, v in sb.profile.items() if k != "avatar_url"}
        return FakeResponse(200, [row])
    sb.on("GET", "/rest/v1/profiles", profiles)
    r = client.get("/api/me")
    assert r.status_code == 200, r.text
    assert r.json()["full_name"] == "Old Name"
    assert r.json()["avatar_url"] is None


def test_patch_me_writes_profile_and_metadata(client, sb):
    r = client.patch("/api/me", json={"first_name": "  Ada ", "last_name": "Lovelace"})
    assert r.status_code == 200, r.text
    assert r.json()["full_name"] == "Ada Lovelace"
    patch = sb.find("PATCH", "/rest/v1/profiles")[-1]
    assert patch[2]["json"] == {"first_name": "Ada", "last_name": "Lovelace", "full_name": "Ada Lovelace"}
    assert patch[2]["params"] == {"id": f"eq.{USER['id']}"}
    meta = sb.find("PUT", f"/auth/v1/admin/users/{USER['id']}")
    assert meta and meta[0][2]["json"]["user_metadata"]["full_name"] == "Ada Lovelace"


def test_patch_me_empty_names_become_null(client, sb):
    r = client.patch("/api/me", json={"first_name": "   ", "last_name": None})
    assert r.status_code == 200, r.text
    assert sb.find("PATCH", "/rest/v1/profiles")[-1][2]["json"] == {
        "first_name": None, "last_name": None, "full_name": None}


def test_patch_me_rejects_long_name(client, sb):
    r = client.patch("/api/me", json={"first_name": "x" * 81, "last_name": "y"})
    assert r.status_code == 422
    assert not sb.find("PATCH", "/rest/v1/profiles")


def test_patch_me_survives_metadata_failure(client, sb):
    sb.on("PUT", f"/auth/v1/admin/users/{USER['id']}", FakeResponse(500, {"msg": "boom"}))
    r = client.patch("/api/me", json={"first_name": "Ada", "last_name": "L"})
    assert r.status_code == 200, r.text
    assert r.json()["full_name"] == "Ada L"


# --- avatar ---------------------------------------------------------------

def _upload(client, data, name="me.png", ctype="image/png"):
    return client.post("/api/me/avatar", files={"file": (name, io.BytesIO(data), ctype)})


def test_avatar_upload_stores_and_saves_url(client, sb):
    old = f"{BASE}/storage/v1/object/public/avatars/{USER['id']}/old.png"
    sb.profile["avatar_url"] = old
    r = _upload(client, PNG)
    assert r.status_code == 200, r.text
    url = r.json()["avatar_url"]
    assert url.startswith(f"{BASE}/storage/v1/object/public/avatars/{USER['id']}/") and url.endswith(".png")
    up = [c for c in sb.calls if c[0] == "POST" and c[1].startswith("/storage/v1/object/avatars/")]
    assert len(up) == 1
    assert up[0][2]["headers"]["Content-Type"] == "image/png"
    assert up[0][2]["headers"]["x-upsert"] == "true"
    assert up[0][2]["data"] == PNG
    assert sb.profile["avatar_url"] == url
    assert sb.find("DELETE", f"/storage/v1/object/avatars/{USER['id']}/old.png")


def test_avatar_never_deletes_foreign_object(client, sb):
    sb.profile["avatar_url"] = f"{BASE}/storage/v1/object/public/avatars/{OTHER_ID}/theirs.png"
    assert _upload(client, PNG).status_code == 200
    assert not [c for c in sb.calls if c[0] == "DELETE" and c[1].startswith("/storage/")]


def test_avatar_too_big(client, sb):
    r = _upload(client, PNG + b"\x00" * (2 * 1024 * 1024))
    assert r.status_code == 413
    assert not [c for c in sb.calls if c[1].startswith("/storage/")]


def test_avatar_wrong_magic_bytes(client, sb):
    r = _upload(client, b"<svg xmlns='http://www.w3.org/2000/svg'/>", name="x.png", ctype="image/png")
    assert r.status_code == 415
    assert not [c for c in sb.calls if c[1].startswith("/storage/")]


@pytest.mark.parametrize("data", [
    b"\xff\xd8\xff\xe0" + b"\x00" * 20,
    b"GIF89a" + b"\x00" * 20,
    b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 20,
])
def test_avatar_accepts_other_formats(client, sb, data):
    assert _upload(client, data, name="f", ctype="application/octet-stream").status_code == 200


def test_avatar_storage_failure_is_502_with_reason(client, sb):
    sb.on("POST", "/storage/v1/object/avatars/*",
          FakeResponse(404, {"statusCode": "404", "error": "Bucket not found", "message": "Bucket not found"}))
    r = _upload(client, PNG)
    assert r.status_code == 502
    assert "Bucket not found" in r.json()["detail"]
    assert sb.profile["avatar_url"] is None


def test_avatar_delete(client, sb):
    sb.profile["avatar_url"] = f"{BASE}/storage/v1/object/public/avatars/{USER['id']}/cur.png"
    r = client.delete("/api/me/avatar")
    assert r.status_code == 200 and r.json() == {"avatar_url": None}
    assert sb.profile["avatar_url"] is None
    assert sb.find("DELETE", f"/storage/v1/object/avatars/{USER['id']}/cur.png")


# --- team invite ----------------------------------------------------------

def _profiles_lookup(rows_by_email):
    def handler(method, url, **kw):
        if "email" in (kw.get("params") or {}):
            email = kw["params"]["email"].removeprefix("eq.")
            return FakeResponse(200, rows_by_email.get(email, []))
        return FakeResponse(200, [])
    return handler


def _saved_invites(sb):
    return [c[2]["json"] for c in sb.find("POST", "/rest/v1/team_members")]


def test_invite_existing_user_uses_matching_profile(client, sb):
    sb.on("GET", "/rest/v1/profiles", _profiles_lookup({"friend@example.com": [{"id": OTHER_ID}]}))
    # If the old admin-list lookup were used, this unrelated first user would win.
    sb.on("GET", "/auth/v1/admin/users", FakeResponse(200, {"users": [{"id": STRANGER_ID, "email": "x@y.z"}]}))
    r = client.post("/api/team/invite", json={"email": "  Friend@Example.com "})
    assert r.status_code == 200, r.text
    assert _saved_invites(sb) == [{"owner_id": USER["id"], "member_id": OTHER_ID,
                                  "email": "friend@example.com", "status": "pending"}]
    assert not sb.find("POST", "/auth/v1/invite")


def test_invite_falls_back_to_exact_admin_match(client, sb):
    sb.on("GET", "/rest/v1/profiles", _profiles_lookup({}))
    sb.on("POST", "/auth/v1/invite", FakeResponse(422, {"msg": "A user with this email address has already been registered"}))
    sb.on("GET", "/auth/v1/admin/users", FakeResponse(200, {"users": [
        {"id": STRANGER_ID, "email": "someone@else.com"},
        {"id": OTHER_ID, "email": "Friend@Example.com"},
    ]}))
    r = client.post("/api/team/invite", json={"email": "friend@example.com"})
    assert r.status_code == 200, r.text
    assert _saved_invites(sb)[0]["member_id"] == OTHER_ID


def test_invite_never_picks_unmatched_user(client, sb):
    sb.on("GET", "/rest/v1/profiles", _profiles_lookup({}))
    sb.on("POST", "/auth/v1/invite", FakeResponse(422, {"msg": "Email rate limit exceeded"}))
    sb.on("GET", "/auth/v1/admin/users", FakeResponse(200, {"users": [{"id": STRANGER_ID, "email": "x@y.z"}]}))
    r = client.post("/api/team/invite", json={"email": "friend@example.com"})
    assert r.status_code == 400
    assert "rate limit" in r.json()["detail"]
    assert not _saved_invites(sb)


def test_invite_new_user_sends_supabase_invite(client, sb):
    sb.on("GET", "/rest/v1/profiles", _profiles_lookup({}))
    sb.on("POST", "/auth/v1/invite", FakeResponse(200, {"id": OTHER_ID}))
    sb.on("GET", "/auth/v1/admin/users", FakeResponse(200, {"users": []}))
    r = client.post("/api/team/invite", json={"email": "new@example.com"})
    assert r.status_code == 200, r.text
    sent = sb.find("POST", "/auth/v1/invite")[0][2]["json"]
    assert sent["email"] == "new@example.com"
    assert _saved_invites(sb)[0]["member_id"] == OTHER_ID


def test_invite_self_is_rejected(client, sb):
    r = client.post("/api/team/invite", json={"email": "OWNER@example.com"})
    assert r.status_code == 400 and r.json()["detail"] == "You can't invite yourself."
    assert not sb.calls


def test_invite_self_by_id_is_rejected(client, sb):
    sb.on("GET", "/rest/v1/profiles", _profiles_lookup({"alias@example.com": [{"id": USER["id"]}]}))
    r = client.post("/api/team/invite", json={"email": "alias@example.com"})
    assert r.status_code == 400
    assert not _saved_invites(sb)


def test_invite_already_accepted_is_not_downgraded(client, sb):
    sb.on("GET", "/rest/v1/profiles", _profiles_lookup({"friend@example.com": [{"id": OTHER_ID}]}))
    sb.on("GET", "/rest/v1/team_members", FakeResponse(200, [{"status": "accepted"}]))
    r = client.post("/api/team/invite", json={"email": "friend@example.com"})
    assert r.status_code == 400
    assert r.json()["detail"] == "friend@example.com is already on your team."
    assert not _saved_invites(sb)


@pytest.mark.parametrize("email", ["not-an-email", "a@b", "two@@x.com", ""])
def test_invite_rejects_bad_email(client, sb, email):
    assert client.post("/api/team/invite", json={"email": email}).status_code == 422
    assert not sb.calls


def test_team_upstream_failure_is_readable(client, sb):
    sb.on("GET", "/rest/v1/team_members", FakeResponse(503, {"message": "upstream down"}))
    r = client.get("/api/team")
    assert r.status_code == 502
    assert "Could not load your team" in r.json()["detail"] and "upstream down" in r.json()["detail"]


def test_list_team_passes_rows_through(client, sb):
    row = {"member_id": OTHER_ID, "email": "f@e.com", "status": "pending",
           "created_at": "2026-10-01T12:00:00+00:00"}
    sb.on("GET", "/rest/v1/team_members",
          lambda m, u, **kw: FakeResponse(200, [row] if "owner_id" in kw["params"] else []))
    r = client.get("/api/team")
    assert r.status_code == 200
    assert r.json()["members"] == [row]


def test_invite_link_lands_on_set_password(client, sb, monkeypatch):
    monkeypatch.setattr(api, "_frontend_origins", ["https://app.example.test"])
    sb.on("GET", "/rest/v1/profiles", _profiles_lookup({}))
    sb.on("GET", "/auth/v1/admin/users", FakeResponse(200, {"users": []}))
    sb.on("POST", "/auth/v1/invite", FakeResponse(200, {"id": OTHER_ID}))
    assert client.post("/api/team/invite", json={"email": "new@example.com"}).status_code == 200
    sent = sb.find("POST", "/auth/v1/invite")[0][2]["json"]
    assert sent["redirect_to"] == "https://app.example.test/auth/set-password?invited=1"
