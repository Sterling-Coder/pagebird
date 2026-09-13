import time

from babel.translate.engine import _ChunkedEngine, _CHUNK


def test_translate_preserves_order_regardless_of_completion_order():
    # Chunk 0 is slow, chunk 1 is fast — chunk 1 finishes first, but output
    # order must still match input order.
    class Engine(_ChunkedEngine):
        def _translate_chunk(self, chunk):
            # Reverse-alphabetical chunk content encodes which chunk this is.
            if chunk[0] == "a":
                time.sleep(0.1)
            return [f"{t}-done" for t in chunk]

    texts = ["a"] * _CHUNK + ["b"] * _CHUNK  # two chunks: all "a", all "b"
    result = Engine().translate(texts)
    assert result == ["a-done"] * _CHUNK + ["b-done"] * _CHUNK


def test_translate_runs_chunks_concurrently():
    # Each chunk sleeps; if sequential, total time >= chunks * delay.
    # If concurrent (5 workers), 6 chunks of 0.1s each finish in ~0.2s (2 waves).
    class Engine(_ChunkedEngine):
        def _translate_chunk(self, chunk):
            time.sleep(0.1)
            return list(chunk)

    texts = ["x"] * (_CHUNK * 6)  # 6 chunks
    started = time.time()
    Engine().translate(texts)
    elapsed = time.time() - started
    assert elapsed < 0.1 * 6  # would be >= 0.6s if fully sequential
    assert elapsed < 0.35     # 2 waves of 5-worker pool: ~0.2s + scheduling overhead


def test_translate_falls_back_to_source_on_chunk_failure_and_records_it(monkeypatch):
    import babel.translate.engine as engine_mod
    monkeypatch.setattr(engine_mod, "_CHUNK_RETRY_DELAY", 0)

    class Engine(_ChunkedEngine):
        def _translate_chunk(self, chunk):
            if chunk[0] == "bad":
                raise RuntimeError("boom")
            return [f"{t}-done" for t in chunk]

    texts = ["bad"] * _CHUNK + ["good"] * _CHUNK
    eng = Engine()
    result = eng.translate(texts)
    assert result == ["bad"] * _CHUNK + ["good-done"] * _CHUNK  # failed chunk falls back to source
    assert eng.failed_sources == {"bad"}
    # A chunk that always fails halves down to single items (see
    # test_translate_chunk_splits_on_persistent_miscount for the case this
    # exists for), so every "bad" item bottoms out as its own leaf failure.
    assert len(eng.failures) == _CHUNK
    assert all("RuntimeError" in f and "boom" in f for f in eng.failures)
    # Only the top-level call gets the full retry-with-backoff budget; every
    # split node below it (all leaf failures here) gets one fast attempt —
    # retrying-with-delay at every tree level turned one bad chunk into
    # minutes of dead waiting in production.
    assert all("gave up after 1 attempt" in f for f in eng.failures)


def test_split_retry_does_not_pay_backoff_at_every_tree_level():
    # Regression: an earlier version of the split-on-miscount fix retried
    # with the FULL backoff budget (3 attempts, 1.5s/3s delays) at every
    # level of the split tree, not just the top — a chunk with several
    # persistently-failing items took minutes to give up instead of
    # seconds, which read as the whole pipeline hanging. Split nodes must
    # get exactly one fast attempt; only the top-level call retries.
    class Engine(_ChunkedEngine):
        def _translate_chunk(self, chunk):
            raise RuntimeError("boom")  # every item is unresolvable, worst case

    texts = ["bad"] * _CHUNK
    eng = Engine()
    started = time.time()
    eng.translate(texts)
    elapsed = time.time() - started
    # Real _CHUNK_RETRY_DELAY (1.5s/3s) applies only once, at the top level.
    # No split-tree multiplication: this must stay well under a second of
    # sleep despite _CHUNK worth of leaf failures.
    assert elapsed < 4.5 + 2.0  # top-level backoff (1.5+3=4.5s) + generous slack
    assert len(eng.failed_sources) == 1  # {"bad"} — all items identical


def test_translate_chunk_splits_on_persistent_miscount(monkeypatch):
    # Observed in production: the model deterministically returns N-1 items
    # for a specific 40-item chunk (it conflates two similar source strings
    # into one output line) — every retry of the SAME chunk fails identically
    # since it isn't a transient network/rate-limit blip. Splitting the chunk
    # isolates the one colliding pair instead of losing the whole batch.
    import babel.translate.engine as engine_mod
    monkeypatch.setattr(engine_mod, "_CHUNK_RETRY_DELAY", 0)

    # "dup-a" and "dup-b" are the pair the fake model always conflates,
    # however they're split — everything else always translates cleanly.
    def fake_model(chunk):
        if "dup-a" in chunk and "dup-b" in chunk:
            out = [f"{t}-done" for t in chunk if t != "dup-b"]  # drop one -> miscount
            return out
        return [f"{t}-done" for t in chunk]

    class Engine(_ChunkedEngine):
        def _translate_chunk(self, chunk):
            result = fake_model(chunk)
            if len(result) != len(chunk):
                raise ValueError(f"got {len(result)} for {len(chunk)}-item chunk")
            return result

    texts = ["x"] * 10 + ["dup-a", "dup-b"] + ["y"] * 10
    eng = Engine()
    result = eng.translate(texts)
    assert result == ["x-done"] * 10 + ["dup-a-done", "dup-b-done"] + ["y-done"] * 10
    assert not eng.failed_sources  # nothing permanently lost to needs_human
    assert not eng.failures


def test_translate_chunk_retries_and_succeeds_on_second_attempt(monkeypatch):
    # A single bad sample (malformed JSON, wrong item count) shouldn't
    # permanently sink a chunk — retrying the same chunk often succeeds
    # since LLM sampling is non-deterministic.
    import babel.translate.engine as engine_mod
    monkeypatch.setattr(engine_mod, "_CHUNK_RETRY_DELAY", 0)

    calls = {"n": 0}

    class Engine(_ChunkedEngine):
        def _translate_chunk(self, chunk):
            calls["n"] += 1
            if calls["n"] < 2:
                raise RuntimeError("transient")
            return [f"{t}-done" for t in chunk]

    texts = ["x"] * _CHUNK
    eng = Engine()
    result = eng.translate(texts)
    assert result == ["x-done"] * _CHUNK
    assert not eng.failures
    assert not eng.failed_sources


def test_translate_empty_input_returns_empty():
    class Engine(_ChunkedEngine):
        def _translate_chunk(self, chunk):
            return list(chunk)

    assert Engine().translate([]) == []


def test_deepl_engine_chunks_large_input(monkeypatch):
    import deepl

    from babel.translate.engine import DeepLEngine, _CHUNK
    from babel import languages

    calls = []

    class FakeResult:
        def __init__(self, text):
            self.text = text

    class FakeTranslator:
        def __init__(self, key):
            pass

        def translate_text(self, chunk, **kwargs):
            calls.append(list(chunk))
            return [FakeResult(f"{t}-fr") for t in chunk]

        def create_glossary(self, *a, **k):
            raise RuntimeError("no glossary needed in this test")

    monkeypatch.setattr(deepl, "Translator", FakeTranslator)
    monkeypatch.setenv("DEEPL_AUTH_KEY", "fake-key")

    # French has no glossary file configured (languages.py), so
    # _ensure_glossary's load_terms call returns nothing and create_glossary
    # is never invoked — keeps this test focused on chunking, not glossary setup.
    eng = DeepLEngine(lang=languages.get("fr"))
    texts = [f"text{i}" for i in range(_CHUNK + 5)]  # 45 texts -> 2 chunks (40 + 5)

    result = eng.translate(texts)

    assert len(calls) == 2
    assert {len(c) for c in calls} == {_CHUNK, 5}
    assert result == [f"text{i}-fr" for i in range(_CHUNK + 5)]
