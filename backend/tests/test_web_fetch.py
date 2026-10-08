"""The website fetcher's SSRF guard and limits.

Addresses are judged by the real `ip_allowed`; the HTTP behaviour (redirects,
size, timeouts, content type) runs against a real server on 127.0.0.1, which
the tests admit by allowing exactly that address and its port — nothing else
about the guard is relaxed.
"""

import gzip
import http.server
import socket
import threading
import time

import pytest

from pagebirdy.web import fetch
from pagebirdy.web.fetch import FetchError

# --- addresses -------------------------------------------------------------

BLOCKED_IPS = [
    "127.0.0.1", "127.1.2.3", "0.0.0.0", "10.0.0.1", "172.16.5.4", "192.168.1.1",
    "169.254.169.254", "100.64.0.1", "224.0.0.1", "255.255.255.255", "240.0.0.1",
    "198.18.0.1", "::1", "::", "fe80::1", "fc00::1", "fd12:3456::1", "fd00:ec2::254",
    "::ffff:127.0.0.1", "::ffff:10.0.0.1", "::ffff:169.254.169.254", "64:ff9b::a00:1",
    "64:ff9b::7f00:1", "64:ff9b::a9fe:a9fe", "64:ff9b:1::808:808",
    "2002:7f00:1::", "ff02::1", "fe80::1%eth0", "not-an-ip",
]
ALLOWED_IPS = ["93.184.216.34", "8.8.8.8", "1.1.1.1", "2606:4700:4700::1111",
               "64:ff9b::808:808"]  # NAT64 of 8.8.8.8: what a DNS64 network returns


@pytest.mark.parametrize("ip", BLOCKED_IPS)
def test_internal_addresses_are_refused(ip):
    assert fetch.ip_allowed(ip) is False


@pytest.mark.parametrize("ip", ALLOWED_IPS)
def test_public_addresses_are_allowed(ip):
    assert fetch.ip_allowed(ip) is True


@pytest.mark.parametrize("host", [
    "localhost", "LOCALHOST", "foo.localhost", "printer.local", "db.internal",
    "metadata.google.internal", "metadata", "intranet", "router.lan", "x.home.arpa",
])
def test_internal_names_are_refused_before_lookup(host, monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: pytest.fail("looked up"))
    with pytest.raises(FetchError) as e:
        fetch.fetch(f"http://{host}/")
    assert e.value.code == "blocked"


def _resolves_to(monkeypatch, *ips):
    def fake(host, port, *a, **k):
        return [(socket.AF_INET6 if ":" in ip else socket.AF_INET, socket.SOCK_STREAM, 6, "",
                 (ip, port)) for ip in ips]
    monkeypatch.setattr(socket, "getaddrinfo", fake)


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/", "http://[::1]/", "http://169.254.169.254/latest/meta-data/",
    "http://2130706433/", "http://0x7f.1/", "http://[::ffff:127.0.0.1]/",
])
def test_literal_and_encoded_internal_addresses_are_refused(url):
    with pytest.raises(FetchError) as e:
        fetch.fetch(url)
    assert e.value.code in ("blocked", "unreachable")
    assert e.value.code == "blocked" or "127" not in str(e.value)


def test_a_dropped_dns_answer_is_retried(monkeypatch):
    calls = []

    def flaky(host, port, *a, **k):
        calls.append(host)
        if len(calls) == 1:
            raise socket.gaierror(11001, "getaddrinfo failed")
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr(socket, "getaddrinfo", flaky)
    monkeypatch.setattr(fetch, "DNS_RETRY_DELAYS", (0, 0))
    assert fetch.resolve("example.com", 443) == ["93.184.216.34"]
    assert len(calls) == 2


def test_a_name_that_never_resolves_is_unreachable(monkeypatch):
    calls = []

    def missing(*a, **k):
        calls.append(1)
        raise socket.gaierror(11001, "getaddrinfo failed")

    monkeypatch.setattr(socket, "getaddrinfo", missing)
    monkeypatch.setattr(fetch, "DNS_RETRY_DELAYS", (0, 0))
    with pytest.raises(FetchError) as e:
        fetch.resolve("no-such-host.example", 443)
    assert e.value.code == "unreachable" and len(calls) == 3


def test_a_name_resolving_to_any_private_address_is_refused(monkeypatch):
    _resolves_to(monkeypatch, "93.184.216.34", "10.0.0.7")
    with pytest.raises(FetchError) as e:
        fetch.fetch("https://example.com/")
    assert e.value.code == "blocked"
    assert "10.0.0.7" not in str(e.value)


@pytest.mark.parametrize("url,code", [
    ("", "invalid_url"), ("   ", "invalid_url"), ("not a url", "invalid_url"),
    ("ftp://example.com/", "invalid_url"), ("javascript:alert(1)", "invalid_url"),
    ("file:///etc/passwd", "invalid_url"), ("https://user:pw@example.com/", "invalid_url"),
    ("https://example.com:8080/", "blocked"), ("http://example.com:22/", "blocked"),
    ("https://", "invalid_url"),
])
def test_bad_urls(url, code, monkeypatch):
    _resolves_to(monkeypatch, "93.184.216.34")
    with pytest.raises(FetchError) as e:
        fetch.fetch(url)
    assert e.value.code == code


def test_normalize_adds_https_and_drops_fragment():
    assert fetch.normalize_url("example.com") == "https://example.com/"
    assert fetch.normalize_url(" HTTP://Example.com/a?b=1#top ") == "http://example.com/a?b=1"
    assert fetch.normalize_url("http://example.com/path") == "http://example.com/path"


# --- a real server on loopback ----------------------------------------------

class _Handler(http.server.BaseHTTPRequestHandler):
    routes: dict = {}

    def do_GET(self):  # noqa: N802
        self.server.seen.append(dict(self.headers))
        route = self.routes.get(self.path.split("?")[0])
        if route is None:
            self.send_response(404)
            self.end_headers()
            return
        route(self)

    def log_message(self, *a):
        pass


@pytest.fixture
def server(monkeypatch):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    srv.daemon_threads = True
    srv.seen = []
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    # Admit exactly this server: its address and its port. Every other check
    # is the real one.
    real = fetch.ip_allowed
    monkeypatch.setattr(fetch, "ip_allowed", lambda ip: ip == "127.0.0.1" or real(ip))
    monkeypatch.setattr(fetch, "ALLOWED_PORTS", frozenset({80, 443, port}))
    _Handler.routes = {}
    yield f"http://127.0.0.1:{port}", _Handler.routes, srv
    srv.shutdown()


def _html(body=b"<html><body><p>Hello</p></body></html>", ctype="text/html; charset=utf-8",
          status=200, headers=()):
    def route(h):
        h.send_response(status)
        h.send_header("Content-Type", ctype)
        for k, v in headers:
            h.send_header(k, v)
        h.send_header("Content-Length", str(len(body)))
        h.end_headers()
        h.wfile.write(body)
    return route


def _redirect(location, status=302):
    def route(h):
        h.send_response(status)
        h.send_header("Location", location)
        h.end_headers()
    return route


def test_fetches_a_page(server):
    base, routes, srv = server
    routes["/"] = _html()
    page = fetch.fetch(base + "/")
    assert page.body.startswith(b"<html>") and page.charset == "utf-8"
    sent = srv.seen[0]
    assert "Cookie" not in sent and "Authorization" not in sent


def test_follows_a_public_redirect(server):
    base, routes, _ = server
    routes["/a"] = _redirect("/b")
    routes["/b"] = _html()
    assert fetch.fetch(base + "/a").url == base + "/b"


@pytest.mark.parametrize("target", [
    "http://10.0.0.1/", "http://localhost/", "http://169.254.169.254/latest/",
    "http://[::1]/", "file:///etc/passwd", "gopher://example.com/", "http://example.com:8080/",
])
def test_every_redirect_hop_is_checked(server, target):
    base, routes, _ = server
    routes["/"] = _redirect(target)
    with pytest.raises(FetchError) as e:
        fetch.fetch(base + "/")
    assert e.value.code == "blocked"


def test_redirect_loop_stops(server):
    base, routes, _ = server
    routes["/"] = _redirect("/")
    with pytest.raises(FetchError) as e:
        fetch.fetch(base + "/")
    assert e.value.code == "unreachable" and "redirects" in str(e.value)


def test_dns_rebinding_is_caught_on_the_connected_socket(monkeypatch):
    """The lookup says public, the connection lands on loopback: refused."""
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    _Handler.routes = {"/": _html()}
    srv.seen = []
    try:
        monkeypatch.setattr(fetch, "ALLOWED_PORTS", frozenset({80, 443, port}))
        monkeypatch.setattr(fetch, "resolve", lambda host, port: ["93.184.216.34"])
        monkeypatch.setattr(fetch, "check_host", lambda host: None)
        with pytest.raises(FetchError) as e:
            fetch.fetch(f"http://127.0.0.1:{port}/")
        assert e.value.code == "blocked"
        assert srv.seen == []  # not a single request reached it
    finally:
        srv.shutdown()


def test_size_limit_by_declared_length(server, monkeypatch):
    base, routes, _ = server
    monkeypatch.setattr(fetch, "MAX_BYTES", 1000)
    routes["/"] = _html(b"x" * 2000)
    with pytest.raises(FetchError) as e:
        fetch.fetch(base + "/")
    assert e.value.code == "too_large"


def test_size_limit_while_streaming(server, monkeypatch):
    base, routes, _ = server
    monkeypatch.setattr(fetch, "MAX_BYTES", 1000)

    def route(h):
        h.send_response(200)
        h.send_header("Content-Type", "text/html")
        h.end_headers()  # no length: read until close
        h.wfile.write(b"y" * 5000)
        h.close_connection = True
    routes["/"] = route
    with pytest.raises(FetchError) as e:
        fetch.fetch(base + "/")
    assert e.value.code == "too_large"


def test_size_limit_counts_decompressed_bytes(server, monkeypatch):
    base, routes, _ = server
    monkeypatch.setattr(fetch, "MAX_BYTES", 10_000)
    routes["/"] = _html(gzip.compress(b"<p>" + b"a" * 1_000_000), headers=[("Content-Encoding", "gzip")])
    with pytest.raises(FetchError) as e:
        fetch.fetch(base + "/")
    assert e.value.code == "too_large"


def test_gzip_page_is_decoded(server):
    base, routes, _ = server
    routes["/"] = _html(gzip.compress(b"<html><body>Hi</body></html>"),
                        headers=[("Content-Encoding", "gzip")])
    assert fetch.fetch(base + "/").body == b"<html><body>Hi</body></html>"


def test_read_timeout(server, monkeypatch):
    base, routes, _ = server
    monkeypatch.setattr(fetch, "READ_TIMEOUT", 0.3)

    def slow(h):
        time.sleep(1.0)
        _html()(h)
    routes["/"] = slow
    with pytest.raises(FetchError) as e:
        fetch.fetch(base + "/")
    assert e.value.code == "timeout"


def test_overall_timeout_on_a_trickling_body(server, monkeypatch):
    base, routes, _ = server
    monkeypatch.setattr(fetch, "TOTAL_TIMEOUT", 0.5)

    def trickle(h):
        h.send_response(200)
        h.send_header("Content-Type", "text/html")
        h.end_headers()
        for _ in range(20):
            h.wfile.write(b"<p>x</p>")
            h.wfile.flush()
            time.sleep(0.1)
    routes["/"] = trickle
    with pytest.raises(FetchError) as e:
        fetch.fetch(base + "/")
    assert e.value.code == "timeout"


@pytest.mark.parametrize("ctype", ["application/json", "image/png", "application/pdf", ""])
def test_non_html_is_refused(server, ctype):
    base, routes, _ = server
    routes["/"] = _html(b"{}", ctype=ctype)
    with pytest.raises(FetchError) as e:
        fetch.fetch(base + "/")
    assert e.value.code == "not_html"


def test_http_error_status(server):
    base, _, _ = server
    with pytest.raises(FetchError) as e:
        fetch.fetch(base + "/missing")
    assert e.value.code == "unreachable" and "404" in str(e.value)


def test_connection_refused_is_unreachable_and_names_no_address(monkeypatch):
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()  # nothing listens here now
    real = fetch.ip_allowed
    monkeypatch.setattr(fetch, "ip_allowed", lambda ip: ip == "127.0.0.1" or real(ip))
    monkeypatch.setattr(fetch, "ALLOWED_PORTS", frozenset({80, 443, port}))
    with pytest.raises(FetchError) as e:
        fetch.fetch(f"http://127.0.0.1:{port}/")
    # Windows answers a closed loopback port by timing out, not refusing.
    assert e.value.code in ("unreachable", "timeout")
    assert "127.0.0.1" not in str(e.value) and str(port) not in str(e.value)


def test_environment_proxy_is_ignored(server, monkeypatch):
    base, routes, _ = server
    routes["/"] = _html()
    monkeypatch.setenv("HTTP_PROXY", "http://10.9.9.9:3128")
    monkeypatch.setenv("http_proxy", "http://10.9.9.9:3128")
    assert fetch.fetch(base + "/").body
