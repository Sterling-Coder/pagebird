from pagebirdy.models import Segment
from pagebirdy.translate.engine import Engine, IdentityEngine
from pagebirdy.translate.translator import Translator


class MapEngine(Engine):
    """Deterministic fake engine driven by a source->target dict."""

    def __init__(self, mapping, name="fake"):
        self.mapping = mapping
        self.name = name

    def translate(self, texts):
        return [self.mapping.get(t, t) for t in texts]


def seg(id, source, placeholders=None):
    return Segment(id=id, page=0, bbox=(0, 0, 1, 1), font="f", size=11, color=0,
                   source=source, placeholders=placeholders or {})


def test_a_dropped_placeholder_still_ships_no_gate():
    # There is no integrity gate on the live pipeline any more: whatever the
    # engine returns ships, even a run that dropped a math placeholder.
    eng = MapEngine({"Add ⟦m0⟧": "Suma"})  # dropped the placeholder
    s = seg("a", "Add ⟦m0⟧", {"⟦m0⟧": "5"})
    Translator(eng, None).run([s])
    assert s.status == "translated"
    assert s.target == "Suma"


def test_a_configured_secondary_engine_is_never_called():
    # `secondary` (DeepL) is still accepted for `engine_secondary` reporting,
    # but its only use was the disagreement flag, which is gone.
    calls = []

    class Spy(Engine):
        name = "spy-secondary"

        def translate(self, texts):
            calls.append(texts)
            return texts

    primary = MapEngine({"The ratio": "La razón"})
    s = seg("a", "The ratio")
    Translator(primary, Spy()).run([s])
    assert calls == []
    assert s.status == "translated"
    assert s.disagreement is False


def test_value_visible_token_allows_noun_agreement():
    # Engine inflects the noun for the visible quantity; token stays intact.
    eng = MapEngine({"⟦=5⟧ apples": "⟦=5⟧ manzanas"})
    s = seg("a", "⟦=5⟧ apples", {"⟦=5⟧": "5"})
    Translator(eng, None).run([s])
    assert s.status == "translated"
    assert s.restored_target() == "5 manzanas"


def test_glossary_miss_is_flagged_but_still_ships():
    # Real engine leaves "ratio" untranslated -> glossary miss. Noted for review,
    # but the segment still ships: dropping it left the English on the page.
    eng = MapEngine({"The ratio is fixed": "The ratio is fixed"})
    s = seg("a", "The ratio is fixed")
    Translator(eng, None).run([s])
    assert s.status == "translated"
    assert any("glossary miss" in n for n in s.notes)


def test_plural_target_is_not_a_glossary_miss():
    # "razones equivalentes" satisfies the "equivalent -> equivalente" entry.
    eng = MapEngine({"equivalent ratios": "razones equivalentes"})
    s = seg("a", "equivalent ratios")
    Translator(eng, None).run([s])
    assert s.status == "translated"
    assert not any("glossary miss" in n for n in s.notes)


def test_empty_segment_is_marked_empty():
    s = seg("a", "   ")
    Translator(IdentityEngine(), None).run([s])
    assert s.status == "empty"


def test_diagram_labels_never_reach_the_engine():
    """A vertex label is not a word.

    On a Hindi geometry page the engine transliterated the triangle's labels --
    P became a Devanagari spelling of the letter -- while the drawn shape still
    said P, so the label no longer matched the figure. The prompt asks the model
    to leave single letters alone; this makes it structural instead.
    """
    engine = MapEngine({"P": "WRONG", "x": "WRONG", "Reflect": "Refleja"})
    labels = [seg("v1", "P"), seg("v2", "x"), seg("v3", "B1")]
    word = seg("w", "Reflect")

    Translator(engine, None, target_lang="hi").run(labels + [word])

    for s in labels:
        assert s.target == s.source, f"{s.source} was sent to the engine"
        assert s.engine == "label"
        assert s.status == "translated"   # handled, so coverage still counts it
    # A real word is unaffected.
    assert word.target == "Refleja"
