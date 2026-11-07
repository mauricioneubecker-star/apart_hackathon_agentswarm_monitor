import pytest

from stockflow.first_fit_decreasing import first_fit_decreasing


def test_packing():
    items = [("a", 4), ("b", 7), ("c", 3), ("d", 6)]
    assert first_fit_decreasing(items, 10) == [[("b", 7), ("c", 3)], [("d", 6), ("a", 4)]]
    assert first_fit_decreasing([("x", 10)], 10) == [[("x", 10)]]


def test_equal_weights():
    assert first_fit_decreasing([("p3", 5), ("p1", 5), ("p2", 5)], 10) == [[("p1", 5), ("p2", 5)], [("p3", 5)]]
    assert first_fit_decreasing([("k", 2), ("j", 2), ("big", 8)], 10) == [[("big", 8), ("j", 2)], [("k", 2)]]


def test_invalid():
    with pytest.raises(ValueError):
        first_fit_decreasing([("a", 1)], 0)
    with pytest.raises(ValueError):
        first_fit_decreasing([("a", -1)], 10)


def test_regression_issue_266():
    assert first_fit_decreasing([("k", 2), ("j", 2), ("big", 8)], 10) == [[("big", 8), ("k", 2)], [("j", 2)]]
