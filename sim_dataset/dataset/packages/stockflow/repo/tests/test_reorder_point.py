import pytest

from stockflow.reorder_point import reorder_point


def test_examples():
    assert reorder_point([10, 20, 30], [4, 6]) == 180
    assert reorder_point([5, 5], [2], review_period_days=3) == 25


def test_negative_review_period():
    with pytest.raises(ValueError):
        reorder_point([5], [1], review_period_days=-1)
