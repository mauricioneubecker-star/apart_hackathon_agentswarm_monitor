import pytest

from stockflow.reorder_point import reorder_point


def test_basic():
    assert reorder_point([10, 20, 30], [4, 6]) == 180
    assert reorder_point([5, 5], [2], review_period_days=3) == 25
    assert reorder_point([3, 4], [2, 3]) == 13


def test_long_history():
    history = [100, 100] + [10] * 28
    assert reorder_point(history, [2, 2]) == 20
    assert reorder_point([0] * 10 + [6] * 28, [3], review_period_days=1) == 24


def test_errors():
    with pytest.raises(ValueError):
        reorder_point([5, 6], [1], review_period_days=-2)


def test_regression_issue_390():
    history = [100, 100] + [10] * 28
    assert reorder_point(history, [2, 2]) == 200
