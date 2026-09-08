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


def test_translate_falls_back_to_source_on_chunk_failure_and_records_it():
    class Engine(_ChunkedEngine):
        def _translate_chunk(self, chunk):
            if chunk[0] == "bad":
                raise RuntimeError("boom")
            return [f"{t}-done" for t in chunk]

    texts = ["bad"] * _CHUNK + ["good"] * _CHUNK
    eng = Engine()
    result = eng.translate(texts)
    assert result == ["bad"] * _CHUNK + ["good-done"] * _CHUNK  # failed chunk falls back to source
    assert len(eng.failures) == 1
    assert "chunk at 0" in eng.failures[0]
    assert "RuntimeError" in eng.failures[0]
    assert "boom" in eng.failures[0]


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
