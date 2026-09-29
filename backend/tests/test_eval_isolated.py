import pytest

from pagebirdy.eval import isolated

_FNS = "tests._eval_child_fns:"


def test_returns_the_childs_result():
    assert isolated.run(_FNS + "ok", "j1", extra=2) == {"job_id": "j1", "score": 1, "extra": 2}


def test_key_error_is_preserved_for_a_404():
    with pytest.raises(KeyError, match="job j1 not found"):
        isolated.run(_FNS + "missing", "j1")


def test_other_errors_become_runtime_errors():
    with pytest.raises(RuntimeError, match="ValueError: bad layout"):
        isolated.run(_FNS + "broken", "j1")


def test_a_killed_child_does_not_take_the_caller_down():
    with pytest.raises(RuntimeError, match="killed by SIGKILL"):
        isolated.run(_FNS + "crash", "j1")


def test_a_hung_child_times_out_and_is_reaped():
    with pytest.raises(TimeoutError, match="longer than 1s"):
        isolated.run(_FNS + "hang", "j1", timeout=1)
