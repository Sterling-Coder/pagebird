"""The website adapter: what is translated, what is never touched, and that the
rebuilt page keeps its structure and loses everything executable."""

import re
import sys
from pathlib import Path

import lxml.html
import pytest

from pagebirdy import languages
from pagebirdy.office.pipeline import prepare, translate_document
from pagebirdy.web import html
from pagebirdy.web.fetch import FetchError

sys.path.insert(0, str(Path(__file__).parent))
from web_fixtures import PseudoEngine, page, pseudo  # noqa: E402


@pytest.fixture
def snap(tmp_path):
    path = tmp_path / "shop.example.com.html"
    path.write_bytes(html.snapshot(page()))
    return str(path)


def _sources(path):
    return {s.id: s.source for s in html.ADAPTER.extract(path)}


def _translate(path, out, lang="es"):
    segs = html.ADAPTER.extract(path)
    todo, _ = prepare(segs)
    for s in todo:
        s.target, s.status = pseudo(s.source), "translated"
    issues = html.ADAPTER.rebuild(path, segs, out, languages.get(lang))
    return segs, issues, lxml.html.fromstring(Path(out).read_bytes())


def test_sentences_reach_the_engine_whole_with_inline_markup_as_tags(snap):
    src = set(_sources(snap).values())
    assert "Welcome to ⟦r1⟧our⟦/r1⟧ store" in src
    assert any(s.startswith("Prices from $19.99 for 3 items. Email ⟦r1⟧") for s in src)
    assert "Run ⟦x0⟧ now. ⟦x1⟧" in src          # <code> and <img> are opaque objects
    assert "Loose text ⟦x0⟧ here" in src         # an empty icon <span> too
    assert {"Inner block", "Tail words", "Buy now", "Shop & Save"} <= src


def test_attributes_a_reader_sees_are_translated_and_no_others(snap):
    src = _sources(snap)
    attrs = {k.split("@")[1]: v for k, v in src.items() if "@" in k}
    assert attrs == {"content": "Best deals online", "title": "Help page",
                     "alt": "A red car", "value": "Send message"}


def test_never_translated(snap):
    text = " ".join(_sources(snap).values())
    for kept in ("greeting", "color: red", "pip install", "keep", "Brand Name", "Do not touch",
                 "/help", "mailto:", "site.css", "car.png"):
        assert kept not in text, kept


def test_protected_values_after_prepare(snap):
    segs = html.ADAPTER.extract(snap)
    todo, kept = prepare(segs)
    by_text = {s.id: s for s in todo}
    prices = next(s for s in todo if s.source.startswith("Prices"))
    assert "⟦~sales@example.com⟧" in prices.source
    assert "19.99" in "".join(prices.placeholders.values())
    assert {s.status for s in kept} == {"protected"}
    kept_text = {s.source for s in kept}
    assert "2024-01-15" in kept_text and "https://example.com/docs" in kept_text
    assert by_text  # something left to translate


def test_rebuild_keeps_structure_links_and_attributes(snap, tmp_path):
    _, issues, out = _translate(snap, str(tmp_path / "out.html"))
    assert issues == []
    h1 = out.find(".//h1")
    assert h1.get("class") == "hero" and h1.text_content() == pseudo("Welcome to our store")
    assert h1.find("b").text == pseudo("our")
    links = {a.get("href"): a for a in out.iter("a") if a.get("href")}
    assert links["/help"].get("class") == "lnk"
    assert links["/help"].get("title") == pseudo("Help page")
    assert links["/help"].text == pseudo("our help center")
    assert links["mailto:sales@example.com"].text == "sales@example.com"
    assert out.find(".//code").text == "pip install babel"
    img = out.find(".//img")
    assert img.get("src") == "/img/car.png" and img.get("alt") == pseudo("A red car")
    assert out.find(".//pre").text == "keep   this   code"
    assert out.find(".//p[@class='notranslate']").text == "Brand Name Ltd"
    assert out.find(".//span[@class='icon']") is not None
    body = out.find(".//body").text_content()
    assert "$19.99" in body and "3 ïtëms" in body


def test_output_is_stripped_of_everything_executable(snap, tmp_path):
    _, _, out = _translate(snap, str(tmp_path / "out.html"))
    assert out.findall(".//script") == [] and out.findall(".//iframe") == []
    for el in out.iter():
        if isinstance(el.tag, str):
            assert not any(k.lower().startswith("on") for k in el.attrib), el.tag
            assert not (el.get("href") or "").lower().startswith("javascript:")
    assert out.find(".//form").get("action") == "about:blank"
    metas = [m.get("http-equiv") for m in out.iter("meta") if m.get("http-equiv")]
    assert metas == ["Content-Security-Policy"]   # ours; the page's refresh is gone
    assert [l.get("rel") for l in out.iter("link")] == ["stylesheet"]
    assert out.find(".//base").get("href") == "https://shop.example.com/a/index.html"
    assert out.find(".//style") is not None       # styles are kept


def test_rtl_target_sets_direction(snap, tmp_path):
    _, _, out = _translate(snap, str(tmp_path / "out.html"), lang="ar")
    assert out.get("lang") == "ar" and out.get("dir") == "rtl"
    _, _, out = _translate(snap, str(tmp_path / "out2.html"), lang="es")
    assert out.get("lang") == "es" and out.get("dir") is None


def test_misordered_tags_keep_the_source_and_go_to_a_human(snap, tmp_path):
    segs = html.ADAPTER.extract(snap)
    todo, _ = prepare(segs)
    for s in todo:
        s.target, s.status = pseudo(s.source), "translated"
    h1 = next(s for s in todo if s.source.startswith("Welcome"))
    h1.target = "Bienvenue ⟦/r1⟧notre⟦r1⟧ magasin"
    issues = html.ADAPTER.rebuild(snap, segs, str(tmp_path / "o.html"), languages.get("fr"))
    assert [i.code for i in issues] == ["tags"] and h1.status == "needs_human"
    out = lxml.html.fromstring((tmp_path / "o.html").read_bytes())
    assert out.find(".//h1").text_content() == "Welcome to our store"


def test_an_emptied_tag_pair_keeps_the_link_and_goes_to_a_human(snap, tmp_path):
    """Seen live: the engine kept ⟦r4⟧⟦/r4⟧ but moved the linked words outside
    it — the gate's count passes, and the <a> would silently disappear."""
    segs = html.ADAPTER.extract(snap)
    todo, _ = prepare(segs)
    for s in todo:
        s.target, s.status = pseudo(s.source), "translated"
    prices = next(s for s in todo if s.source.startswith("Prices"))
    prices.target = re.sub(r"⟦r2⟧(.*?)⟦/r2⟧", r"\1 ⟦r2⟧⟦/r2⟧", prices.target)
    issues = html.ADAPTER.rebuild(snap, segs, str(tmp_path / "o.html"), languages.get("es"))
    assert [i.code for i in issues] == ["tags"] and prices.status == "needs_human"
    out = lxml.html.fromstring((tmp_path / "o.html").read_bytes())
    assert out.find(".//a[@href='/help']").text == "our help center"


def test_whitespace_between_runs_never_becomes_a_tag(tmp_path):
    """Seen live on a real page: the newline after a link reached the engine as
    an empty pair, "What's out there?⟦r1⟧ ⟦/r1⟧"."""
    body = (b'<html lang="en"><body><dl><dt><a href="/top">What is out there?</a>\n</dt></dl>'
            b'<p>Read <b>this</b> <i>now</i> please</p></body></html>')
    path = tmp_path / "ws.html"
    path.write_bytes(html.snapshot(page(body)))
    src = set(_sources(str(path)).values())
    assert "What is out there?" in src
    assert "Read ⟦r1⟧this ⟦/r1⟧⟦r2⟧now⟦/r2⟧ please" in src
    out_path = str(tmp_path / "o.html")
    _, issues, out = _translate(str(path), out_path)
    assert issues == []
    assert out.find(".//a").text == pseudo("What is out there?")
    assert out.find(".//p").text_content() == pseudo("Read this now please")


def test_page_base_href_is_resolved_against_the_fetched_url(tmp_path):
    body = b'<html lang="en"><head><base href="/assets/"></head><body><p>Hello there</p></body></html>'
    snap = html.snapshot(page(body, url="https://x.example.com/blog/post"))
    root = lxml.html.fromstring(snap)
    assert [b.get("href") for b in root.iter("base")] == ["https://x.example.com/assets/"]


@pytest.mark.parametrize("lang", ["fr", "de-DE", "zh-Hans", "ar"])
def test_non_english_page_is_unsupported(lang):
    body = f'<html lang="{lang}"><body><p>Bonjour tout le monde</p></body></html>'.encode()
    with pytest.raises(FetchError) as e:
        html.snapshot(page(body))
    assert e.value.code == "unsupported" and "English" in str(e.value)


@pytest.mark.parametrize("lang", ["en", "en-GB", "EN-us", None])
def test_english_or_undeclared_pages_are_accepted(lang):
    attr = f' lang="{lang}"' if lang else ""
    html.snapshot(page(f"<html{attr}><body><p>Hello</p></body></html>".encode()))


def test_script_only_page_has_nothing_to_translate(tmp_path):
    body = b'<html lang="en"><body><div id="root"></div><script>render()</script></body></html>'
    path = tmp_path / "spa.html"
    path.write_bytes(html.snapshot(page(body)))
    with pytest.raises(FetchError) as e:
        html.ADAPTER.extract(str(path))
    assert e.value.code == "unsupported" and "JavaScript" in str(e.value)


def test_too_much_text_is_unsupported(tmp_path, monkeypatch):
    monkeypatch.setattr(html, "MAX_SEGMENTS", 5)
    path = tmp_path / "big.html"
    body = "<html><body>" + "".join(f"<p>Paragraph number {i}</p>" for i in range(20)) + "</body></html>"
    path.write_bytes(html.snapshot(page(body.encode())))
    with pytest.raises(FetchError) as e:
        html.ADAPTER.extract(str(path))
    assert e.value.code == "unsupported"


def test_page_size_limits_come_from_the_environment(tmp_path, monkeypatch):
    path = tmp_path / "big.html"
    body = "<html><body>" + "".join(f"<p>Paragraph number {i}</p>" for i in range(20)) + "</body></html>"
    path.write_bytes(html.snapshot(page(body.encode())))
    monkeypatch.setenv("BABEL_WEB_MAX_SEGMENTS", "5")
    with pytest.raises(FetchError) as e:
        html.ADAPTER.extract(str(path))
    assert "limit 5 blocks" in str(e.value)
    monkeypatch.setenv("BABEL_WEB_MAX_SEGMENTS", "50")
    assert len(html.ADAPTER.extract(str(path))) == 20


def test_legacy_charset_is_decoded(tmp_path):
    body = '<html><head><meta charset="windows-1252"></head><body><p>Café menu</p></body></html>'
    snap = html.snapshot(page(body.encode("cp1252")).__class__(
        url="https://x.example.com/", body=body.encode("cp1252"), charset=None, content_type="text/html"))
    path = tmp_path / "c.html"
    path.write_bytes(snap)
    assert "Café menu" in _sources(str(path)).values()


def test_runs_through_the_shared_driver(snap, tmp_path):
    engine = PseudoEngine()
    report = translate_document(snap, str(tmp_path / "out"), target_lang="es",
                                engines=(engine, None), fmt=html.FORMAT, adapter=html.ADAPTER)
    assert report["format"] == "website" and report["errors"] == []
    assert report["output"].endswith(".es.html")
    assert not any("greeting" in t or "pip install" in t for t in engine.seen)
    body = Path(report["output"]).read_text(encoding="utf-8")
    assert re.search(r"Wëlcömë tö <b>öür</b> störë", body)


def test_an_emptied_styling_pair_is_written_unstyled_not_left_in_english(snap, tmp_path):
    """Only a link keeps the English for an emptied pair. A pair that only
    styled its words (<b>, a coloured <span>) loses the styling instead: the
    translation is whole, and English on a translated page is the worse result."""
    segs = html.ADAPTER.extract(snap)
    todo, _ = prepare(segs)
    for s in todo:
        s.target, s.status = pseudo(s.source), "translated"
    h1 = next(s for s in todo if s.source.startswith("Welcome"))
    h1.target = "Bienvenue dans notre magasin⟦r1⟧⟦/r1⟧"
    issues = html.ADAPTER.rebuild(snap, segs, str(tmp_path / "o.html"), languages.get("fr"))
    assert [(i.code, i.where) for i in issues] == [("tags", h1.id)]
    assert "styling" in issues[0].detail and h1.status == "translated"
    out = lxml.html.fromstring((tmp_path / "o.html").read_bytes())
    assert out.find(".//h1").text_content() == "Bienvenue dans notre magasin"
    assert out.find(".//h1/b") is None


def test_an_emptied_pair_inside_a_heading_link_is_unstyled_not_english(tmp_path):
    """The whole heading is the link; only the coloured <span> inside it lost
    its words. The link wraps the translation as before and the colour goes."""
    body = (b'<!doctype html><html lang="en"><body><h3><a href="/po">'
            b'<span class="red">PO &amp; SO </span>Automation</a></h3></body></html>')
    path = tmp_path / "p.html"
    path.write_bytes(html.snapshot(page(body=body)))
    segs = html.ADAPTER.extract(str(path))
    todo, _ = prepare(segs)
    h3 = next(s for s in todo if "Automation" in s.source)
    h3.target, h3.status = "Automatización de OC y OV⟦r1⟧⟦/r1⟧", "translated"
    issues = html.ADAPTER.rebuild(str(path), segs, str(tmp_path / "o.html"), languages.get("es"))
    assert h3.status == "translated" and "styling" in issues[0].detail
    out = lxml.html.fromstring((tmp_path / "o.html").read_bytes())
    assert out.find(".//h3/a").get("href") == "/po"
    assert out.find(".//h3/a").text_content() == "Automatización de OC y OV"
