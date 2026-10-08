"""The website endpoints through FastAPI: submit, serve the result safely,
failures and rate limits.

The fetch is replaced by a canned page except in the last test, which runs
the real fetcher against a server on 127.0.0.1 (admitted by address and port
only). The engine is a deterministic pseudo-translator. Auth, storage and the
job executor are stubbed by `api_support.wire`; tests that write a job row need
`TEST_DATABASE_URL` (conftest skips them without it).
"""

import http.server
import sys
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import pagebirdy.api as api
from pagebirdy import web_api
from pagebirdy.office import pipeline as office_pipeline
from pagebirdy.web import fetch as web_fetch
from pagebirdy.web import pipeline as web_pipeline
from pagebirdy.web.fetch import FetchError

sys.path.insert(0, str(Path(__file__).parent))
from api_support import wire  # noqa: E402
from web_fixtures import PAGE, PseudoEngine, page, pseudo  # noqa: E402


@pytest.fixture
def client(monkeypatch, tmp_path):
    wire(monkeypatch, tmp_path)
    monkeypatch.setattr(office_pipeline, "build_engines",
                        lambda doc_context="", target_lang=None, extra_rules="":
                        (PseudoEngine(), None))
    monkeypatch.setattr(web_pipeline, "fetch", lambda url: page(url=url))
    web_api.reset_limits()
    yield TestClient(api.app)
    web_api.reset_limits()


def _submit(client, url="https://shop.example.com/", lang="es", **extra):
    return client.post("/api/translate/website",
                       json={"url": url, "target_lang": lang, **extra})


def test_translates_and_serves_a_sandboxed_page(client):
    r = _submit(client)
    assert r.status_code == 200, r.text
    jid = r.json()["job_id"]
    job = client.get(f"/api/jobs/{jid}").json()
    assert job["status"] == "complete" and job["meta"]["format"] == "website"
    assert job["meta"]["source_url"] == "https://shop.example.com/"
    assert job["original_filename"] == "https://shop.example.com/"

    r = client.get(f"/api/translate/website/{jid}/result")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
    csp = r.headers["content-security-policy"]
    assert csp.startswith("sandbox;") and "script-src 'none'" in csp
    assert "allow-scripts" not in csp and "allow-same-origin" not in csp
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["content-disposition"].startswith("inline")
    assert pseudo("Welcome to") in r.text and "<script" not in r.text.lower()

    d = client.get(f"/api/translate/website/{jid}/result?download=1")
    assert d.headers["content-disposition"].startswith("attachment") and d.content == r.content

    src = client.get(f"/api/translate/website/{jid}/source")
    assert src.status_code == 200 and "Welcome to" in src.text and "<script" not in src.text.lower()
    assert src.headers["content-security-policy"].startswith("sandbox;")


def test_segments_are_reviewable_and_edits_reach_the_page(client):
    jid = _submit(client).json()["job_id"]
    segs = client.get(f"/api/jobs/{jid}/segments").json()
    h1 = next(s for s in segs if s["source"].startswith("Welcome"))
    r = client.patch(f"/api/segments/{jid}/{h1['seg_id']}",
                     json={"target": "Bienvenidos a ⟦r1⟧nuestra⟦/r1⟧ tienda", "approve": True})
    assert r.status_code == 200 and r.json()["status"] == "approved", r.text
    assert client.post(f"/api/jobs/{jid}/rebuild").status_code == 200
    page_html = client.get(f"/api/translate/website/{jid}/result").text
    assert "Bienvenidos a <b>nuestra</b> tienda" in page_html


@pytest.mark.parametrize("url,code", [
    ("", "invalid_url"), ("not a url", "invalid_url"), ("ftp://example.com", "invalid_url"),
    ("javascript:alert(1)", "invalid_url"), ("http://localhost/", "blocked"),
    ("http://127.0.0.1/", "blocked"), ("http://169.254.169.254/latest/meta-data", "blocked"),
    ("http://10.1.2.3/", "blocked"), ("http://[::1]/", "blocked"),
    ("https://example.com:8443/", "blocked"), ("http://intranet/", "blocked"),
])
def test_bad_urls_are_refused_without_a_job(client, url, code):
    r = _submit(client, url=url)
    assert r.status_code == 400 and r.json()["code"] == code, r.text
    assert "detail" in r.json()


def test_language_is_required_and_must_exist(client):
    assert _submit(client, lang="").json()["code"] == "invalid_language"
    assert _submit(client, lang="xx").json()["code"] == "invalid_language"


@pytest.mark.parametrize("code", ["unreachable", "timeout", "blocked", "not_html", "too_large"])
def test_fetch_failures_become_a_failed_row_with_a_friendly_message(client, monkeypatch, code):
    def refuse(url):
        raise FetchError(code)
    monkeypatch.setattr(web_pipeline, "fetch", refuse)
    r = _submit(client)
    assert r.status_code == 500 and r.json()["detail"] == web_fetch.MESSAGES[code]
    job = next(j for j in client.get("/api/jobs").json() if j["meta"]["format"] == "website")
    assert (job["status"], job["error"]) == ("failed", web_fetch.MESSAGES[code])


def test_non_english_page_is_unsupported(client, monkeypatch):
    monkeypatch.setattr(web_pipeline, "fetch", lambda url: page(
        b'<html lang="fr"><body><p>Bonjour</p></body></html>', url=url))
    r = _submit(client)
    assert r.status_code == 500 and "English" in r.json()["detail"]


def test_script_only_page_is_unsupported_and_the_row_says_why(client, monkeypatch):
    monkeypatch.setattr(web_pipeline, "fetch", lambda url: page(
        b'<html lang="en"><body><div id="app"></div><script>x()</script></body></html>', url=url))
    r = _submit(client)
    assert r.status_code == 500 and "JavaScript" in r.json()["detail"]


def test_unexpected_errors_never_leak(client, monkeypatch):
    def boom(url):
        raise RuntimeError("connect to 10.0.0.5 failed: Traceback ...")
    monkeypatch.setattr(web_pipeline, "fetch", boom)
    r = _submit(client)
    assert r.status_code == 500 and r.json()["detail"] == web_api.GENERIC_FAILURE
    assert "10.0.0.5" not in str(client.get("/api/jobs").json())


def test_pipeline_errors_store_a_friendly_message(client, monkeypatch):
    from pagebirdy.web import html

    def boom(*a, **k):
        raise RuntimeError("lxml internal detail")
    monkeypatch.setattr(html.HtmlAdapter, "rebuild", boom)
    r = _submit(client)
    assert r.status_code == 500 and r.json()["detail"] == web_api.GENERIC_FAILURE


def test_rate_limit_per_user(client, monkeypatch):
    monkeypatch.setenv("BABEL_WEB_RATE_LIMIT", "2")
    assert _submit(client).status_code == 200
    assert _submit(client).status_code == 200
    r = _submit(client)
    assert r.status_code == 429 and r.json()["code"] == "rate_limited"


def test_concurrency_cap(client, monkeypatch):
    monkeypatch.setenv("BABEL_WEB_MAX_RUNNING", "1")
    web_api._take_slot("someone-else")       # one job already running
    r = _submit(client)
    assert r.status_code == 429 and r.json()["code"] == "busy"


def test_result_for_unknown_job_is_404(client):
    assert client.get("/api/translate/website/nope/result").status_code == 404


def test_end_to_end_through_the_real_fetcher(client, monkeypatch):
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            if self.path == "/old":
                self.send_response(301)
                self.send_header("Location", "/")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(PAGE)))
            self.end_headers()
            self.wfile.write(PAGE)

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        real = web_fetch.ip_allowed
        monkeypatch.setattr(web_fetch, "ip_allowed", lambda ip: ip == "127.0.0.1" or real(ip))
        monkeypatch.setattr(web_fetch, "ALLOWED_PORTS", frozenset({80, 443, port}))
        monkeypatch.setattr(web_pipeline, "fetch", web_fetch.fetch)
        r = _submit(client, url=f"http://127.0.0.1:{port}/old")
        assert r.status_code == 200, r.text
        jid = r.json()["job_id"]
        assert r.json()["final_url"] == f"http://127.0.0.1:{port}/"
        out = client.get(f"/api/translate/website/{jid}/result").text
        assert pseudo("Welcome to") in out and f'<base href="http://127.0.0.1:{port}/">' in out
    finally:
        srv.shutdown()
