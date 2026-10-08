"""Shared stand-ins for the website tests: a pseudo-translating engine and a
sample page. Nothing touches the network."""

import re

from pagebirdy.translate.engine import Engine
from pagebirdy.web.fetch import Page

_TOKEN = re.compile(r"(⟦[^⟧]*⟧)")
_VOWELS = str.maketrans("aeiouAEIOU", "äëïöüÄËÏÖÜ")


def pseudo(text: str) -> str:
    """'Hello ⟦r1⟧world⟦/r1⟧' -> 'Hëllö ⟦r1⟧wörld⟦/r1⟧': changed words, every token intact."""
    return "".join(p if i % 2 else p.translate(_VOWELS) for i, p in enumerate(_TOKEN.split(text)))


class PseudoEngine(Engine):
    name = "pseudo"

    def __init__(self):
        self.seen: list[str] = []

    def translate(self, texts):
        self.seen.extend(texts)
        return [pseudo(t) for t in texts]


PAGE = b"""<!doctype html>
<html lang="en-US"><head>
<title>Shop &amp; Save</title>
<meta name="description" content="Best deals online">
<meta http-equiv="refresh" content="0;url=https://evil.example/">
<link rel="stylesheet" href="/css/site.css">
<link rel="modulepreload" href="/app.js">
<script>var greeting = "Hello world";</script>
<style>p { color: red }</style>
</head>
<body onload="steal()">
<h1 class="hero">Welcome to <b>our</b> store</h1>
<p>Prices from $19.99 for 3 items. Email <a href="mailto:sales@example.com">sales@example.com</a>
or visit <a href="/help" title="Help page" class="lnk">our help center</a>.</p>
<p>Run <code>pip install babel</code> now. <img src="/img/car.png" alt="A red car" onerror="x()"></p>
<div>Loose text <span class="icon"></span> here<div>Inner block</div>Tail words</div>
<p class="notranslate">Brand Name Ltd</p>
<p translate="no">Do not touch</p>
<pre>keep   this   code</pre>
<ul><li>First item</li><li>Second <a href="javascript:alert(1)">item</a></li></ul>
<p>Formula: E = mc2 and x = 2y + 3</p>
<iframe src="https://ads.example/"></iframe>
<form action="https://collect.example/"><input type="submit" value="Send message"></form>
<button>Buy now</button>
<p>2024-01-15</p>
<p>https://example.com/docs</p>
</body></html>"""


def page(body: bytes = PAGE, url: str = "https://shop.example.com/a/index.html") -> Page:
    return Page(url=url, body=body, charset="utf-8", content_type="text/html")
