import pytest

from stockflow.first_fit_decreasing import first_fit_decreasing


def test_example():
    assert first_fit_decreasing([("a", 4), ("b", 7), ("c", 3)], 10) == [[("b", 7), ("c", 3)], [("a", 4)]]
    assert first_fit_decreasing([], 10) == []


def test_oversized_item():
    with pytest.raises(ValueError):
        first_fit_decreasing([("a", 11)], 10)
