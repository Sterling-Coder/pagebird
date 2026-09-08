from babel.models import Segment
from babel.translate.verify import _parse, run_verification


class FakeVerifier:
    name = "verify:fake"

    def __init__(self, verdicts):
        self.verdicts = verdicts
        self.seen = None

    def verify(self, pairs):
        self.seen = pairs
        return self.verdicts


def _seg(sid, source, target, status="translated", placeholders=None):
    return Segment(id=sid, page=0, bbox=(0, 0, 1, 1), font="f", size=11, color=0,
                   source=source, target=target, status=status,
                   placeholders=placeholders or {})


def test_flags_bad_translation_for_review_but_still_ships_it():
    good = _seg("a", "The ratio", "La razón")
    bad = _seg("b", "Add the numbers", "Resta los números")  # wrong: resta = subtract
    v = FakeVerifier(["", "wrong verb: subtract vs add"])
    flagged = run_verification([good, bad], v)
    assert flagged == 1
    assert good.status == "translated"
    # Noted for the reviewer, but not demoted: demoting made reassembly skip the
    # segment and leave the English on the page.
    assert bad.status == "translated"
    assert any("verify:" in n for n in bad.notes)


def test_only_checks_fresh_translations():
    approved = _seg("a", "x", "y", status="tm_hit")
    needs = _seg("b", "x", None, status="needs_human")
    v = FakeVerifier([])  # should not be asked about these
    flagged = run_verification([approved, needs], v)
    assert flagged == 0
    assert v.seen is None


def test_uses_restored_human_readable_pairs():
    s = _seg("a", "Divide ⟦=3⟧ by ⟦=4⟧", "Divide ⟦=3⟧ entre ⟦=4⟧",
             placeholders={"⟦=3⟧": "3", "⟦=4⟧": "4"})
    v = FakeVerifier([""])
    run_verification([s], v)
    assert v.seen == [("Divide 3 by 4", "Divide 3 entre 4")]


def test_none_verifier_is_noop():
    s = _seg("a", "x", "y")
    assert run_verification([s], None) == 0
    assert s.status == "translated"


def test_parse_bad_reply_yields_no_false_flags():
    assert _parse("not json", 3) == ["", "", ""]
    assert _parse('{"v":["ok"]}', 2) == ["", ""]  # wrong length -> no flags
