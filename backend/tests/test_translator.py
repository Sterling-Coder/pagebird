from babel.models import Segment
from babel.tm.store import TranslationMemory
from babel.translate.engine import Engine, IdentityEngine
from babel.translate.translator import Translator


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


def test_clean_translation_and_tm_writeback(tmp_path):
    tm = TranslationMemory(str(tmp_path / "tm.db"))
    eng = MapEngine({"Divide ⟦m0⟧ by ⟦m1⟧": "Divide ⟦m0⟧ entre ⟦m1⟧"})
    s = seg("a", "Divide ⟦m0⟧ by ⟦m1⟧", {"⟦m0⟧": "3", "⟦m1⟧": "2"})
    Translator(eng, None, tm).run([s])
    assert s.status == "translated"
    assert s.restored_target() == "Divide 3 entre 2"
    # Reused from TM on a second run without calling the engine.
    s2 = seg("b", "Divide ⟦m0⟧ by ⟦m1⟧", {"⟦m0⟧": "9", "⟦m1⟧": "4"})
    Translator(MapEngine({}), None, tm).run([s2])
    assert s2.status == "tm_hit"
    assert s2.restored_target() == "Divide 9 entre 4"  # placeholders re-bound per segment


def test_integrity_failure_routes_to_human():
    eng = MapEngine({"Add ⟦m0⟧": "Suma"})  # dropped the placeholder
    s = seg("a", "Add ⟦m0⟧", {"⟦m0⟧": "5"})
    Translator(eng, None, None).run([s])
    assert s.status == "needs_human" and s.target is None


def test_engine_disagreement_is_advisory_not_forced_review():
    # Two good-but-different MT outputs: flag it, but don't force human review.
    primary = MapEngine({"The ratio": "La razón"})
    secondary = MapEngine({"The ratio": "La proporción"})
    s = seg("a", "The ratio")
    Translator(primary, secondary, None).run([s])
    assert s.disagreement is True
    assert s.status == "translated"
    assert any("engine disagreement" in n for n in s.notes)


def test_value_visible_token_allows_noun_agreement():
    # Engine inflects the noun for the visible quantity; token stays intact.
    eng = MapEngine({"⟦=5⟧ apples": "⟦=5⟧ manzanas"})
    s = seg("a", "⟦=5⟧ apples", {"⟦=5⟧": "5"})
    Translator(eng, None, None).run([s])
    assert s.status == "translated"
    assert s.restored_target() == "5 manzanas"


def test_glossary_miss_is_flagged_but_still_ships():
    # Real engine leaves "ratio" untranslated -> glossary miss. Noted for review,
    # but the segment still ships: dropping it left the English on the page.
    eng = MapEngine({"The ratio is fixed": "The ratio is fixed"})
    s = seg("a", "The ratio is fixed")
    Translator(eng, None, None).run([s])
    assert s.status == "translated"
    assert any("glossary miss" in n for n in s.notes)
    assert any("flagged for review" in n for n in s.notes)


def test_glossary_miss_is_not_memorised():
    tm = TranslationMemory(":memory:")
    eng = MapEngine({"The ratio is fixed": "The ratio is fixed"})
    Translator(eng, None, tm).run([seg("a", "The ratio is fixed")])
    assert tm.lookup("The ratio is fixed") is None


def test_plural_target_is_not_a_glossary_miss():
    # "razones equivalentes" satisfies the "equivalent -> equivalente" entry.
    eng = MapEngine({"equivalent ratios": "razones equivalentes"})
    s = seg("a", "equivalent ratios")
    Translator(eng, None, None).run([s])
    assert s.status == "translated"
    assert not any("glossary miss" in n for n in s.notes)


def test_empty_segment_is_marked_empty():
    s = seg("a", "   ")
    Translator(IdentityEngine(), None, None).run([s])
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

    Translator(engine, None, None, target_lang="hi").run(labels + [word])

    for s in labels:
        assert s.target == s.source, f"{s.source} was sent to the engine"
        assert s.engine == "label"
        assert s.status == "translated"   # handled, so coverage still counts it
    # A real word is unaffected.
    assert word.target == "Refleja"


def test_primary_and_secondary_run_concurrently():
    import threading
    import time

    from babel.translate.engine import Engine

    events = {"primary_started": None, "secondary_started": None}

    class SlowPrimary(Engine):
        name = "slow-primary"

        def translate(self, texts):
            events["primary_started"] = time.time()
            time.sleep(0.15)
            return [f"{t}-p" for t in texts]

    class SlowSecondary(Engine):
        name = "slow-secondary"

        def translate(self, texts):
            events["secondary_started"] = time.time()
            time.sleep(0.15)
            return [f"{t}-s" for t in texts]

    s = seg("a", "hello")
    started = time.time()
    Translator(SlowPrimary(), SlowSecondary(), None).run([s])
    elapsed = time.time() - started

    assert elapsed < 0.25  # sequential would be >= 0.3s (2 * 0.15s)
    # Both started within a tight window of each other -> concurrent, not sequential.
    assert abs(events["primary_started"] - events["secondary_started"]) < 0.05


def test_secondary_failure_does_not_block_or_fail_primary():
    from babel.translate.engine import Engine

    class BrokenSecondary(Engine):
        name = "broken"

        def translate(self, texts):
            raise RuntimeError("secondary down")

    eng = MapEngine({"hello": "hola"})
    s = seg("a", "hello")
    Translator(eng, BrokenSecondary(), None).run([s])
    assert s.status == "translated"
    assert s.target == "hola"
    assert s.disagreement is False  # secondary failure -> no comparison, no crash


def test_stale_tm_entry_whose_target_is_its_source_is_rejected(tmp_path):
    """A failed run leaves English in the memory, and it never goes away.

    When the engine could not answer it returned the source unchanged, and that
    got memorised. Writeback now refuses to store passthrough, but entries from
    before that guard are still in the database -- and being keyed on the source
    text, one poisoned sentence puts English into every later document that
    shares it. Real case: a Spanish job where the only genuinely untranslated
    sentence on the page was a `tm_hit`.
    """
    tm = TranslationMemory(str(tmp_path / "tm.db"))
    english = "Your child will also use ten frames to model subtraction"
    tm.store(english, english, engine="broken")   # what a failed run left behind

    s = seg("a", english)
    Translator(MapEngine({english: "Su hijo usara cuadros de diez"}), None, tm,
              target_lang="es").run([s])
    tm.close()

    assert s.target == "Su hijo usara cuadros de diez"
    assert s.engine != "tm", "the poisoned entry was served instead of retranslating"


def test_a_good_tm_entry_is_still_reused(tmp_path):
    """The rejection must not defeat the memory it is protecting."""
    tm = TranslationMemory(str(tmp_path / "tm.db"))
    english = "Write the missing number in the box"
    tm.store(english, "Escribe el numero que falta en la casilla", engine="prior")

    s = seg("a", english)
    Translator(MapEngine({}), None, tm, target_lang="es").run([s])
    tm.close()

    assert s.engine == "tm"
    assert s.target == "Escribe el numero que falta en la casilla"
