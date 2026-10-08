"""Shared wiring for the image and website API tests.

Authentication is replaced by a fixed user, jobs run inline
(`PAGEBIRDY_SYNC_JOBS=1`) and storage is an in-memory dict, so nothing
reaches Supabase or a bucket. Tests that write a job row still need
`TEST_DATABASE_URL` (conftest skips them without it).
"""

import os

import pagebirdy.api as api
from pagebirdy import image_api, storage, web_api

USER = {"id": "u-test", "email": "a@b.c"}


class MemoryStorage:
    def __init__(self):
        self.files: dict[str, bytes] = {}

    def upload_file(self, local_path, key):
        with open(local_path, "rb") as f:
            self.files[key] = f.read()
        return key

    def read_bytes(self, key):
        return self.files.get(key)

    def download_to(self, key, local_path):
        data = self.files.get(key)
        if data is None:
            return False
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(data)
        return True


def wire(monkeypatch, tmp_path) -> MemoryStorage:
    mem = MemoryStorage()
    monkeypatch.setenv("PAGEBIRDY_SYNC_JOBS", "1")
    monkeypatch.setenv("BABEL_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("BABEL_OUT_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(api, "_REVIEW_DB", str(tmp_path / "review.db"))
    for name in ("upload_file", "read_bytes", "download_to"):
        monkeypatch.setattr(storage, name, getattr(mem, name))
    for mod in (api, image_api, web_api):
        if hasattr(mod, "require_trial_active"):
            monkeypatch.setattr(mod, "require_trial_active", lambda user: None)
    monkeypatch.setitem(api.app.dependency_overrides, api.require_user, lambda: USER)
    return mem
