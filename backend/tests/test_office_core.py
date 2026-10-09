import hashlib

from pagebirdy import languages
from pagebirdy.models import Segment
from pagebirdy.review.store import ReviewStore
from pagebirdy.translate import engine, integrity


def test_gate_unchanged_for_existing_tokens():
    assert integrity.verify("Add ⟦=3⟧ and ⟦m0⟧", "Suma ⟦=3⟧ y ⟦m0⟧") == (True, "")
    assert not integrity.verify("Add ⟦m0⟧", "Suma")[0]


def test_system_prompt_byte_identical_without_extra_rules():
    lang = languages.get("es")
    assert engine._system_prompt("Ctx", lang) == engine._system_prompt("Ctx", lang, "")
    assert engine._system_prompt("Ctx", lang, "\nEXTRA").endswith("\nEXTRA")


# --- office.protect / office.classify ----------------------------------------
import pytest

from pagebirdy.office.classify import should_translate
from pagebirdy.office.protect import protect, restore, visible


@pytest.mark.parametrize("ph", ["{customer_name}", "{{customer_name}}", "${amount}",
                                "%VALUE%", "<NAME>", "[VARIABLE]", "%USER%"])
def test_template_placeholders_become_names(ph):
    out, m = protect(f"Hello {ph}, welcome.")
    assert f"⟦~{ph}⟧" in out
    assert restore(out, m) == f"Hello {ph}, welcome."


def test_urls_emails_paths_codes_protected():
    text = r"See https://x.com/a or mail a@b.co, file C:\data\in.csv, code SKU-4471."
    out, m = protect(text)
    for lit in ("https://x.com/a", "a@b.co", r"C:\data\in.csv", "SKU-4471"):
        assert f"⟦~{lit}⟧" in out, (lit, out)
    assert restore(out, m) == text


def test_protect_is_deterministic():
    assert protect("Order {id} costs 5") == protect("Order {id} costs 5")


def test_protect_leaves_run_tags_and_objects_alone():
    out, _ = protect("Click ⟦r1⟧Save 2⟦/r1⟧⟦x0⟧")
    assert "⟦r1⟧" in out and "⟦/r1⟧" in out and "⟦x0⟧" in out
    assert "⟦=2⟧" in out


def test_visible_strips_structure_tokens_only():
    assert visible("a ⟦r1⟧b⟦/r1⟧⟦x0⟧⟦br⟧c ⟦=5⟧") == "a bc ⟦=5⟧"


@pytest.mark.parametrize("text,ok", [
    ("Total Revenue", True), ("100000", False), ("2024-05-01", False),
    ("https://x.com", False), ("a@b.co", False), ("INV-2024-001", False),
    ("", False), ("   ", False), ("—", False), ("Q3", True), ("$19.99", False),
])
def test_should_translate(text, ok):
    assert should_translate(text) is ok


@pytest.mark.parametrize("text,url,after", [
    ("See https://acme.com/help.", "https://acme.com/help", "."),
    ("Visit https://acme.com/a, then call.", "https://acme.com/a", ", then call."),
    ("Go to www.acme.com!", "www.acme.com", "!"),
    ("Did you try https://acme.com/faq?", "https://acme.com/faq", "?"),
    ("Docs live at https://acme.com/docs", "https://acme.com/docs", ""),
    ("(see https://acme.com/x)", "https://acme.com/x", ")"),
])
def test_url_token_excludes_sentence_punctuation(text, url, after):
    out, m = protect(text)
    assert f"⟦~{url}⟧{after}" in out, out
    assert restore(out, m) == text


def test_url_keeps_inner_punctuation_and_query():
    text = "Open https://acme.com/a.b/c?x=1&y=2#top now."
    out, _ = protect(text)
    assert "⟦~https://acme.com/a.b/c?x=1&y=2#top⟧ now." in out
