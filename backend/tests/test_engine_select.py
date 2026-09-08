import pytest

from babel.translate.engine import IdentityEngine, _parse_batch, build_engines


def test_defaults_to_identity_offline(monkeypatch):
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPL_AUTH_KEY", "BABEL_LLM_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    primary, secondary = build_engines()
    assert isinstance(primary, IdentityEngine)
    assert secondary is None


def test_openai_preferred_when_both_keys_present(monkeypatch):
    # Force the branch without the SDK installed: construction fails -> identity,
    # but we still prove the selection *targets* openai, not anthropic.
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "y")
    monkeypatch.delenv("BABEL_LLM_PROVIDER", raising=False)
    # A developer .env is loaded into os.environ by config.load_env() as soon as
    # anything imports babel.cli, so this assertion about the *default* model
    # only holds if the override is cleared first.
    monkeypatch.delenv("BABEL_LLM_MODEL", raising=False)
    import babel.translate.engine as eng

    called = {}

    class Fake(eng.Engine):
        name = "openai:test"

        def __init__(self, model, doc_context="", lang=None):
            called["model"] = model
            called["lang"] = lang

        def translate(self, texts):
            return list(texts)

    monkeypatch.setattr(eng, "OpenAIEngine", Fake)
    primary, _ = eng.build_engines()
    assert primary.name == "openai:test"
    assert called["model"] == "gpt-5.2"

    # The chosen target language reaches the engine that builds the prompt.
    eng.build_engines(target_lang="fr")
    assert called["lang"].code == "fr"


def test_bad_engine_reply_raises_for_caller_to_mark_needs_human():
    with pytest.raises(ValueError):
        _parse_batch("not json", ["a", "b"])
    with pytest.raises(ValueError):
        _parse_batch('{"t": ["x"]}', ["a", "b"])  # wrong length
    assert _parse_batch('{"t": ["x","y"]}', ["a", "b"]) == ["x", "y"]
