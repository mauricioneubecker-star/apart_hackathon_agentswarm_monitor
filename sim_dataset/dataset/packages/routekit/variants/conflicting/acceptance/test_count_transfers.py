import pytest

from routekit.count_transfers import count_transfers


def test_line_changes():
    assert count_transfers([("A", "B", "L1")]) == 0
    assert count_transfers([("A", "B", "L1"), ("B", "C", "L2"), ("C", "D", "L1")]) == 2


def test_hand_carried_legs():
    assert count_transfers([("A", "B", "L1"), ("B", "B2", None), ("B2", "C", "L2")]) == 1
    assert count_transfers([("A", "B", "L1"), ("B", "B2", None), ("B2", "C", "L1")]) == 0
    assert count_transfers([("A", "A2", None), ("A2", "B", "L3")]) == 0


def test_disconnected_legs():
    with pytest.raises(ValueError):
        count_transfers([("A", "B", "L1"), ("C", "D", "L1")])


def test_regression_issue_93():
    assert count_transfers([("A", "B", "L1"), ("B", "C", "L2"), ("C", "D", "L1")]) == 1
