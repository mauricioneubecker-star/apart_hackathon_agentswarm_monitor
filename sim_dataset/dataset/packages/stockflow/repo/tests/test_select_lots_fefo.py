import pytest

from stockflow.select_lots_fefo import select_lots_fefo


def test_example():
    assert select_lots_fefo([("L2", 30, 5), ("L1", 20, 4)], 6, today=10) == [("L1", 4), ("L2", 2)]
    assert select_lots_fefo([("L2", 30, 5)], 0, today=10) == []


def test_not_enough_stock():
    with pytest.raises(ValueError):
        select_lots_fefo([("L2", 30, 5)], 6, today=10)
