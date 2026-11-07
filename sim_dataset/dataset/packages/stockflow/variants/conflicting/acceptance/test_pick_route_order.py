import pytest

from stockflow.pick_route_order import pick_route_order


def test_single_aisle():
    picks = [("S2", "A-01-05-1", 1), ("S1", "A-01-02-1", 3), ("S3", "A-01-02-0", 2)]
    assert pick_route_order(picks) == [("S3", "A-01-02-0", 2), ("S1", "A-01-02-1", 3), ("S2", "A-01-05-1", 1)]


def test_route_through_aisles():
    picks = [
        ("P1", "A-02-03-1", 1),
        ("P2", "A-01-09-1", 1),
        ("P3", "A-02-11-2", 1),
        ("P4", "B-01-01-1", 1),
        ("P5", "a-01-04-1", 1),
    ]
    assert [p[0] for p in pick_route_order(picks)] == ["P5", "P2", "P3", "P1", "P4"]
    assert pick_route_order([("X", "C-04-01-1", 2), ("Y", "C-04-20-1", 1)]) == [("Y", "C-04-20-1", 1), ("X", "C-04-01-1", 2)]


def test_same_bin_and_errors():
    picks = [("K2", "A-03-03-1", 1), ("K1", "A-03-03-1", 5)]
    assert pick_route_order(picks) == picks
    with pytest.raises(ValueError):
        pick_route_order([("Z", "A-3-03-1", 1)])


def test_regression_issue_642():
    assert pick_route_order([("X", "C-04-01-1", 2), ("Y", "C-04-20-1", 1)]) == [("X", "C-04-01-1", 2), ("Y", "C-04-20-1", 1)]
