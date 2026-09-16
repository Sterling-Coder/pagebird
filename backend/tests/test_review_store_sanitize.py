"""`_pg_safe` — Postgres text columns cannot store a NUL (0x00) byte at all;
psycopg raises before the query even reaches the server. Malformed OCR or a
garbled PDF/IDML content stream occasionally produces one in extracted text,
so every write path strips it at the DB boundary. Pure function, no DB
needed — the Postgres-backed ReviewStore itself can't be exercised without a
live SUPABASE_DB_URL."""

from pagebirdy.review.store import _pg_safe


def test_strips_nul_from_string():
    assert _pg_safe("Add\x003") == "Add3"


def test_leaves_clean_string_alone():
    assert _pg_safe("Solve for x") == "Solve for x"


def test_strips_nul_recursively_from_dict():
    cleaned = _pg_safe({"stage": "translat\x00ing", "progress": 42})
    assert cleaned == {"stage": "translating", "progress": 42}


def test_strips_nul_recursively_from_list():
    assert _pg_safe(["a\x00b", "c"]) == ["ab", "c"]


def test_non_string_scalars_pass_through_unchanged():
    assert _pg_safe(42) == 42
    assert _pg_safe(None) is None
    assert _pg_safe(3.5) == 3.5
