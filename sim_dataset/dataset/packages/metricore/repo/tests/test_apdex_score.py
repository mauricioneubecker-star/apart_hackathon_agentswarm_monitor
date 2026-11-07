import pytest

from metricore.apdex_score import apdex_score


def test_example_and_all_fast():
    assert apdex_score([100, 200, 900, 3000], 250) == 0.63
    assert apdex_score([10, 20, 30], 100) == 1.0


def test_empty_rejected():
    with pytest.raises(ValueError):
        apdex_score([], 100)
