"""What a served copy of a stranger's page may not contain.

The translated page is served from this API's own origin, so anything that can
run in it could read the session and call the API. Everything executable goes:
scripts, event handlers, `javascript:`/`vbscript:`/`data:text/html` URLs,
frames, plugins, refresh/cookie/CSP `<meta http-equiv>`, preloads that are not
styles, fonts or images, and form targets. Styles, images and links stay, so
the page still looks like itself. This runs on top of the response's own
`Content-Security-Policy: sandbox` (`web_api.py`); neither is relied on alone.
"""

from __future__ import annotations

import re

from lxml import etree

_REMOVE = frozenset({"script", "iframe", "frame", "frameset", "object", "embed", "applet",
                     "portal", "fencedframe"})
_URL_ATTRS = frozenset({"href", "src", "action", "formaction", "data", "poster", "background",
                        "cite", "longdesc", "lowsrc", "dynsrc", "ping", "codebase", "manifest",
                        "xlink:href", "srcset", "imagesrcset"})
_DROP_ATTRS = frozenset({"srcdoc", "formaction", "action", "ping", "nonce", "integrity"})
_LINK_RELS = frozenset({"stylesheet", "icon", "shortcut", "apple-touch-icon",
                        "apple-touch-icon-precomposed", "mask-icon", "alternate"})
_PRELOAD_AS = frozenset({"style", "font", "image"})
_BAD_SCHEME = re.compile(r"^\s*(?:javascript|vbscript|data\s*:\s*text/html|data\s*:\s*image/svg)",
                         re.IGNORECASE)
_CTRL = re.compile(r"[\x00-\x20]+")

# For a copy saved to disk and opened outside the API: the same rules, inline.
META_CSP = ("default-src * data: blob: 'unsafe-inline'; script-src 'none'; object-src 'none'; "
            "frame-src 'none'; worker-src 'none'; form-action 'none'; connect-src 'none'")


def _local(name: str) -> str:
    return name.rsplit(":", 1)[-1].rsplit("}", 1)[-1].lower()


def _bad_url(value: str) -> bool:
    return bool(_BAD_SCHEME.match(_CTRL.sub("", value or "")))


def _keep_link(el) -> bool:
    rels = set((el.get("rel") or "").lower().split())
    if not rels:
        return False
    if rels == {"preload"}:
        return (el.get("as") or "").lower() in _PRELOAD_AS
    return rels <= _LINK_RELS and "import" not in rels


def sanitize(root) -> None:
    """Strip everything executable from the parsed document `root`, in place."""
    seen_base = False
    doomed = []
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue  # comments and processing instructions are inert
        tag = _local(el.tag)
        if tag in _REMOVE:
            doomed.append(el)
            continue
        if tag == "base":
            href = el.get("href") or ""
            if seen_base or not re.match(r"^https?://", href, re.IGNORECASE):
                doomed.append(el)
                continue
            seen_base = True
            for k in list(el.attrib):
                if k not in ("href",):
                    del el.attrib[k]
            continue
        if tag == "meta" and el.get("http-equiv") is not None:
            doomed.append(el)
            continue
        if tag == "link" and not _keep_link(el):
            doomed.append(el)
            continue
        for name in list(el.attrib):
            local = _local(name)
            if local.startswith("on") or local in _DROP_ATTRS or name.lower() in _DROP_ATTRS:
                del el.attrib[name]
            elif (local in _URL_ATTRS or name.lower() in _URL_ATTRS) and _bad_url(el.attrib[name]):
                del el.attrib[name]
            elif local == "style" and re.search(r"expression\s*\(|javascript:|-moz-binding",
                                               el.attrib[name], re.IGNORECASE):
                del el.attrib[name]
        if tag == "form":
            el.set("action", "about:blank")  # never submits anywhere
    for el in doomed:
        parent = el.getparent()
        if parent is None:
            continue
        # Keep the text that followed the removed element.
        if el.tail:
            prev = el.getprevious()
            if prev is not None:
                prev.tail = (prev.tail or "") + el.tail
            else:
                parent.text = (parent.text or "") + el.tail
        parent.remove(el)


def harden_head(root) -> None:
    """The meta tags every served copy carries: no referrer, inline CSP."""
    head = root.find("head")
    if head is None:
        head = etree.Element("head")
        root.insert(0, head)
    for name in ("referrer",):
        for old in head.findall(f"meta[@name='{name}']"):
            head.remove(old)
    ref = etree.Element("meta", name="referrer", content="no-referrer")
    csp = etree.Element("meta")
    csp.set("http-equiv", "Content-Security-Policy")
    csp.set("content", META_CSP)
    # After <meta charset> (which must come first), before anything else.
    at = 1 if len(head) and head[0].tag == "meta" and head[0].get("charset") else 0
    head.insert(at, csp)
    head.insert(at, ref)
