"""Fetch one public web page, and nothing else.

The URL is a stranger's input that makes this server open a connection, so
every way it could reach something that is not a public web server is closed:

  * scheme http/https only, port 80/443 only, no credentials in the URL;
  * a host name that only means something inside a network (single label,
    `.local`, `.internal`, a cloud metadata name) is refused before lookup;
  * every address the name resolves to must be globally routable — loopback,
    private, link-local (the 169.254.169.254 metadata service), CGNAT,
    multicast, reserved, and IPv6 forms wrapping an IPv4 one are refused (a
    NAT64 address is judged by the IPv4 address it wraps);
  * the address actually connected to is checked again on the open socket,
    so a name that resolves to a public address for the check and a private
    one for the connection (DNS rebinding) still cannot get through;
  * redirects are followed by hand, at most `MAX_REDIRECTS`, each one checked
    from the top;
  * no environment proxy, no .netrc, no cookies (urllib3 reads none of them);
  * connect/read/overall timeouts and a size cap counted while streaming,
    after decompression, so neither a slow nor a large page holds a worker.

A failure raises `FetchError` whose message is safe to show a user: it never
names an internal address or carries a stack trace.
"""

from __future__ import annotations

import concurrent.futures
import ipaddress
import socket
import time
import zlib
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit

import urllib3
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool

MAX_BYTES = 5 * 1024 * 1024
CONNECT_TIMEOUT = 5.0
READ_TIMEOUT = 10.0
TOTAL_TIMEOUT = 20.0
DNS_TIMEOUT = 5.0
# Pauses between lookups of a name the resolver failed to answer for.
DNS_RETRY_DELAYS = (0.5, 1.0)
MAX_REDIRECTS = 5
ALLOWED_PORTS = frozenset({80, 443})
_CHUNK = 64 * 1024
_HTML_TYPES = ("text/html", "application/xhtml+xml")
USER_AGENT = "BabelWebsiteTranslator/1.0 (+static snapshot; no scripts executed)"

# Names that resolve only inside a network, or to a cloud metadata service.
_BLOCKED_NAMES = frozenset({
    "localhost", "metadata", "metadata.google.internal", "metadata.goog",
    "instance-data", "instance-data.ec2.internal", "kubernetes.default",
})
_BLOCKED_SUFFIXES = (".localhost", ".local", ".internal", ".intranet", ".lan", ".home",
                     ".home.arpa", ".corp", ".localdomain", ".svc", ".cluster.local")
# Globally-flagged ranges that still lead somewhere internal or nowhere useful.
_EXTRA_BLOCKED = tuple(ipaddress.ip_network(n) for n in (
    "100.64.0.0/10",      # carrier-grade NAT
    "192.0.0.0/24",       # IETF protocol assignments
    "198.18.0.0/15",      # benchmarking
    "64:ff9b:1::/48",     # local-use NAT64
    "2002::/16",          # 6to4 (wraps an IPv4 address)
    "2001::/32",          # Teredo
    "fd00:ec2::254/128",  # AWS IMDS over IPv6
))

_NAT64 = ipaddress.ip_network("64:ff9b::/96")

MESSAGES = {
    "invalid_url": "Please enter a valid website URL.",
    "blocked": "This address can't be translated. Only public websites are supported.",
    "unreachable": "We couldn't access this website. Please check the URL and try again.",
    "timeout": "The website took too long to process. Please try again.",
    "too_large": "This page is too large to translate (the limit is 5 MB).",
    "not_html": "This address doesn't point to a web page.",
    "unsupported": "This website cannot currently be translated.",
}


class FetchError(Exception):
    """User-facing: `code` is stable for the UI, `str(e)` is safe to show."""

    def __init__(self, code: str, message: str | None = None):
        super().__init__(message or MESSAGES[code])
        self.code = code


class _BlockedPeer(Exception):
    """Raised from inside the connection; deliberately not an OSError, so
    urllib3 does not wrap or retry it."""


@dataclass
class Page:
    url: str            # final URL, after redirects
    body: bytes
    charset: str | None
    content_type: str


def normalize_url(raw: str) -> str:
    """`raw` as an absolute http(s) URL, or FetchError("invalid_url").

    A bare `example.com` gets https://. Fragments are dropped (the server never
    sees them anyway)."""
    text = (raw or "").strip()
    if not text or any(c.isspace() for c in text) or len(text) > 2048:
        raise FetchError("invalid_url")
    if "://" not in text:
        text = "https://" + text
    parts = urlsplit(text)
    if parts.scheme.lower() not in ("http", "https"):
        raise FetchError("invalid_url", "Only http:// and https:// addresses can be translated.")
    if parts.username is not None or parts.password is not None:
        raise FetchError("invalid_url", "Website addresses with a username or password "
                                        "can't be translated.")
    host = parts.hostname
    if not host:
        raise FetchError("invalid_url")
    try:
        port = parts.port
    except ValueError:
        raise FetchError("invalid_url")
    netloc = host if ":" not in host else f"[{host}]"
    if port is not None:
        netloc += f":{port}"
    return urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, ""))


def ip_allowed(ip: str) -> bool:
    """Is `ip` a public unicast address this server may connect to?"""
    try:
        addr = ipaddress.ip_address(ip.split("%", 1)[0])
    except ValueError:
        return False
    if isinstance(addr, ipaddress.IPv6Address):
        if addr in _NAT64:
            # A DNS64 network hands out 64:ff9b::<IPv4> for every IPv4-only
            # site: it is exactly as public as the address it wraps.
            return ip_allowed(str(ipaddress.IPv4Address(int(addr) & 0xFFFFFFFF)))
        embedded = addr.ipv4_mapped or addr.sixtofour or (addr.teredo or (None, None))[1]
        if embedded is not None and not ip_allowed(str(embedded)):
            return False
    if any(addr in net for net in _EXTRA_BLOCKED if net.version == addr.version):
        return False
    return addr.is_global and not (addr.is_multicast or addr.is_private or addr.is_loopback
                                   or addr.is_link_local or addr.is_reserved
                                   or addr.is_unspecified)


def _ascii_host(host: str) -> str:
    try:
        return host.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError:
        raise FetchError("invalid_url")


def check_host(host: str) -> None:
    """Refuse a host by its name alone (before any lookup)."""
    name = _ascii_host(host)
    try:
        ipaddress.ip_address(name)
        return  # a literal address is judged by `ip_allowed`
    except ValueError:
        pass
    if name in _BLOCKED_NAMES or name.endswith(_BLOCKED_SUFFIXES) or "." not in name:
        raise FetchError("blocked")


def resolve(host: str, port: int) -> list[str]:
    """Every address `host` resolves to — refused if any of them is not public.

    All of them, not just the first: the connection may use any."""
    name = _ascii_host(host)
    # A resolver that drops one query reads as "host not found" (seen on a
    # Windows host: getaddrinfo 11001 for a domain nslookup resolved a moment
    # later), so a failed lookup is retried before the site is called
    # unreachable. A name that really does not exist costs DNS_RETRY_DELAYS.
    for delay in (*DNS_RETRY_DELAYS, None):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(socket.getaddrinfo, name, port, 0, socket.SOCK_STREAM)
            try:
                infos = future.result(timeout=DNS_TIMEOUT)
                break
            except concurrent.futures.TimeoutError:
                raise FetchError("timeout")
            except socket.gaierror:
                if delay is None:
                    raise FetchError("unreachable")
            except (UnicodeError, OSError):
                raise FetchError("unreachable")
        time.sleep(delay)
    addrs = sorted({info[4][0] for info in infos})
    if not addrs:
        raise FetchError("unreachable")
    if not all(ip_allowed(a) for a in addrs):
        raise FetchError("blocked")
    return addrs


class _PeerCheck:
    """Mixed into urllib3's connections: the socket that actually connected
    must lead to a public address, whatever the earlier lookup said."""

    def _new_conn(self):  # type: ignore[override]
        sock = super()._new_conn()  # type: ignore[misc]
        try:
            peer = sock.getpeername()[0]
        except OSError:
            peer = ""
        if not ip_allowed(peer):
            sock.close()
            raise _BlockedPeer()
        return sock


class _GuardedHTTPConnection(_PeerCheck, HTTPConnection):
    pass


class _GuardedHTTPSConnection(_PeerCheck, HTTPSConnection):
    pass


class _HTTPPool(HTTPConnectionPool):
    ConnectionCls = _GuardedHTTPConnection


class _HTTPSPool(HTTPSConnectionPool):
    ConnectionCls = _GuardedHTTPSConnection


def _ca_certs() -> str | None:
    try:
        import certifi
        return certifi.where()
    except ImportError:
        return None


def _pool(scheme: str, host: str, port: int, read_timeout: float):
    timeout = urllib3.Timeout(connect=CONNECT_TIMEOUT, read=read_timeout)
    if scheme == "https":
        return _HTTPSPool(host, port, timeout=timeout, retries=False, maxsize=1,
                          cert_reqs="CERT_REQUIRED", ca_certs=_ca_certs())
    return _HTTPPool(host, port, timeout=timeout, retries=False, maxsize=1)


def _content_type(headers) -> tuple[str, str | None]:
    raw = headers.get("Content-Type", "") or ""
    mime, _, params = raw.partition(";")
    charset = None
    for p in params.split(";"):
        k, _, v = p.strip().partition("=")
        if k.lower() == "charset" and v:
            charset = v.strip().strip('"\'') or None
    return mime.strip().lower(), charset


def _decoder(encoding: str):
    enc = (encoding or "identity").strip().lower()
    if enc in ("", "identity"):
        return None
    if enc in ("gzip", "x-gzip"):
        return zlib.decompressobj(16 + zlib.MAX_WBITS)
    if enc == "deflate":
        return zlib.decompressobj()
    raise FetchError("unsupported")


def _read_body(resp, deadline: float) -> bytes:
    """The body, decompressed, never more than MAX_BYTES; a response that
    is still arriving at the deadline is a timeout."""
    decoder = _decoder(resp.headers.get("Content-Encoding", ""))
    declared = resp.headers.get("Content-Length")
    if declared and declared.isdigit() and decoder is None and int(declared) > MAX_BYTES:
        raise FetchError("too_large")
    out = bytearray()
    while True:
        if time.monotonic() > deadline:
            raise FetchError("timeout")
        chunk = resp.read1(_CHUNK) if hasattr(resp, "read1") else resp.read(_CHUNK)
        if not chunk:
            break
        if decoder is not None:
            # Never inflate more than the room left (+1 to notice the overflow).
            room = MAX_BYTES - len(out) + 1
            data = decoder.decompress(chunk, room)
            if decoder.unconsumed_tail:
                raise FetchError("too_large")
            chunk = data
        out += chunk
        if len(out) > MAX_BYTES:
            raise FetchError("too_large")
    if decoder is not None:
        out += decoder.flush()
        if len(out) > MAX_BYTES:
            raise FetchError("too_large")
    return bytes(out)


def _get(url: str, deadline: float):
    """One request, no redirects followed. Returns the open response."""
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        raise FetchError("blocked")
    host = parts.hostname or ""
    try:
        port = parts.port or (443 if scheme == "https" else 80)
    except ValueError:
        raise FetchError("invalid_url")
    if port not in ALLOWED_PORTS:
        raise FetchError("blocked", "Only websites on the standard ports (80 and 443) "
                                    "can be translated.")
    if parts.username is not None or parts.password is not None:
        raise FetchError("blocked")
    check_host(host)
    resolve(host, port)

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise FetchError("timeout")
    pool = _pool(scheme, _ascii_host(host), port, min(READ_TIMEOUT, remaining))
    path = urlunsplit(("", "", parts.path or "/", parts.query, ""))
    try:
        resp = pool.urlopen("GET", path, redirect=False, preload_content=False,
                            decode_content=False, assert_same_host=False, headers={
                                "User-Agent": USER_AGENT,
                                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
                                "Accept-Encoding": "gzip, deflate",
                                "Accept-Language": "en",
                            })
    except _BlockedPeer:
        raise FetchError("blocked")
    except (urllib3.exceptions.ConnectTimeoutError, urllib3.exceptions.ReadTimeoutError):
        raise FetchError("timeout")
    except urllib3.exceptions.HTTPError as e:
        if isinstance(getattr(e, "reason", None), _BlockedPeer):
            raise FetchError("blocked")
        raise FetchError("unreachable")
    except OSError:
        raise FetchError("unreachable")
    return resp, pool


def fetch(raw_url: str) -> Page:
    """The page at `raw_url`, after every check above, or FetchError."""
    url = normalize_url(raw_url)
    deadline = time.monotonic() + TOTAL_TIMEOUT
    for _ in range(MAX_REDIRECTS + 1):
        resp, pool = _get(url, deadline)
        try:
            if resp.status in (301, 302, 303, 307, 308):
                location = resp.headers.get("Location")
                if not location:
                    raise FetchError("unreachable")
                try:
                    url = normalize_url(urljoin(url, location.strip()))
                except FetchError:
                    raise FetchError("blocked")  # e.g. a redirect to file:// or gopher://
                continue
            if resp.status >= 400:
                raise FetchError("unreachable", "We couldn't access this website "
                                                f"(it answered {resp.status}). "
                                                "Please check the URL and try again.")
            if resp.status != 200:
                raise FetchError("unreachable")
            mime, charset = _content_type(resp.headers)
            if mime not in _HTML_TYPES:
                raise FetchError("not_html")
            try:
                body = _read_body(resp, deadline)
            except (urllib3.exceptions.ReadTimeoutError, socket.timeout):
                raise FetchError("timeout")
            except (urllib3.exceptions.HTTPError, OSError, zlib.error):
                raise FetchError("unreachable")
            if not body.strip():
                raise FetchError("unsupported", "This page is empty.")
            return Page(url=url, body=body, charset=charset, content_type=mime)
        finally:
            resp.release_conn()
            pool.close()
    raise FetchError("unreachable", "This website redirects too many times.")
