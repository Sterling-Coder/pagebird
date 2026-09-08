from babel.translate import integrity


def test_preserved_ok():
    ok, detail = integrity.verify("Divide ⟦m0⟧ by ⟦m1⟧", "Divide ⟦m0⟧ entre ⟦m1⟧")
    assert ok and detail == ""


def test_dropped_placeholder_fails():
    ok, detail = integrity.verify("Divide ⟦m0⟧ by ⟦m1⟧", "Divide entre ⟦m1⟧")
    assert not ok and "⟦m0⟧" in detail


def test_hallucinated_placeholder_fails():
    ok, detail = integrity.verify("Divide ⟦m0⟧", "Divide ⟦m0⟧ y ⟦m1⟧")
    assert not ok and "extra" in detail


def test_count_matters():
    ok, _ = integrity.verify("⟦m0⟧ ⟦m0⟧", "⟦m0⟧")
    assert not ok
