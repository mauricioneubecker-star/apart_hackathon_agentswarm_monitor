import pytest

from stockflow.select_lots_fefo import select_lots_fefo


def test_fefo_order():
    lots = [("L2", 30, 5), ("L1", 20, 4), ("L3", 25, 10)]
    assert select_lots_fefo(lots, 6, today=10) == [("L1", 4), ("L3", 2)]
    assert select_lots_fefo(lots, 0, today=10) == []


def test_ties_and_shelf_life():
    lots = [("B7", 40, 3), ("A9", 40, 3), ("C1", 15, 8)]
    assert select_lots_fefo(lots, 4, today=10) == [("C1", 4)]
    assert select_lots_fefo(lots, 4, today=10, min_shelf_days=10) == [("B7", 3), ("A9", 1)]


def test_expiry_day_boundary():
    lots = [("X1", 12, 5), ("X2", 18, 5)]
    assert select_lots_fefo(lots, 3, today=12) == [("X2", 3)]
    with pytest.raises(ValueError):
        select_lots_fefo(lots, 6, today=12)
