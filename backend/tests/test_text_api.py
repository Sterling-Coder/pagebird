"""POST /api/translate/text: the browser extension's short-text endpoint.
Auth is faked and the engine is a deterministic upper-caser."""

import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import pagebirdy.api as api
from pagebirdy import text_api

sys.path.insert(0, str(Path(__file__).parent))
from api_support import wire  # noqa: E402
from image_fixtures import DictEngine  # noqa: E402


class Upper(DictEngine):
    def __init__(self):
        super().__init__({})

    def translate(self, texts):
        self.seen.extend(texts)
        return ["".join(p if p.startswith("⟦") else p.upper() for p in re.split(r"(⟦[^⟧]*⟧)", t))
                for t in texts]


@pytest.fixture
def client(monkeypatch, tmp_path):
    wire(monkeypatch, tmp_path)
    monkeypatch.setattr(text_api, "require_trial_active", lambda user: None)
    monkeypatch.setattr(text_api, "build_engines", lambda **kw: (Upper(), None))
    text_api.reset_limits()
    yield TestClient(api.app)
    text_api.reset_limits()


def _post(client, **body):
    body.setdefault("target_lang", "es")
    return client.post("/api/translate/text", json=body)


def test_translates_in_order_and_keeps_blanks(client):
    r = _post(client, texts=["Hello world", "  ", "Good morning"])
    assert r.status_code == 200, r.text
    assert r.json()["translations"] == ["HELLO WORLD", "  ", "GOOD MORNING"]
    assert r.json()["target_lang"] == "es" and r.json()["direction"] == "ltr"


def test_numbers_and_urls_survive(client):
    r = _post(client, texts=["Pay 49.99 at https://x.example.com/pay now"])
    assert r.json()["translations"] == ["PAY 49.99 AT https://x.example.com/pay NOW"]


def test_rtl_direction_is_reported(client):
    assert _post(client, texts=["Hi"], target_lang="ar").json()["direction"] == "rtl"


@pytest.mark.parametrize("body,needle", [
    ({"texts": []}, "Nothing"),
    ({"texts": ["a"], "target_lang": ""}, "target language"),
    ({"texts": ["a"], "target_lang": "xx"}, "Unsupported"),
    ({"texts": ["a"] * 101}, "At most"),
    ({"texts": ["a" * 5001]}, "at most"),
])
def test_bad_requests(client, body, needle):
    r = client.post("/api/translate/text", json={"target_lang": "es", **body})
    assert r.status_code == 400 and needle in r.json()["detail"]


def test_rate_limit_per_user(client, monkeypatch):
    monkeypatch.setenv("PAGEBIRDY_TEXT_RATE_LIMIT", "2")
    assert _post(client, texts=["a"]).status_code == 200
    assert _post(client, texts=["a"]).status_code == 200
    assert _post(client, texts=["a"]).status_code == 429


def test_engine_failure_is_a_generic_502(client, monkeypatch):
    class Boom(Upper):
        failures = ["secret sk-123"]

    monkeypatch.setattr(text_api, "build_engines", lambda **kw: (Boom(), None))
    r = _post(client, texts=["Hello"])
    assert r.status_code == 502 and "sk-123" not in r.text


def test_requires_login():
    api.app.dependency_overrides.pop(api.require_user, None)
    assert TestClient(api.app).post("/api/translate/text", json={"texts": ["a"]}).status_code in (401, 500)
