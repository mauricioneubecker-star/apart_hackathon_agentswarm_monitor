import pytest

from stockflow.allocate_backorders import allocate_backorders


def test_sequence():
    orders = [("o1", 2, 10, {"S": 5}), ("o2", 1, 12, {"S": 4}), ("o3", 2, 9, {"S": 3})]
    assert allocate_backorders(orders, {"S": 7}) == {"o2": {"S": 4}, "o3": {"S": 3}, "o1": {"S": 0}}
    assert allocate_backorders(orders, {}) == {"o1": {"S": 0}, "o2": {"S": 0}, "o3": {"S": 0}}


def test_ship_complete():
    orders = [
        ("A100", 1, 5, {"TEE": 2, "MUG": 3}),
        ("A101", 1, 6, {"TEE": 1}),
        ("A102", 2, 1, {"MUG": 4}),
    ]
    assert allocate_backorders(orders, {"TEE": 5, "MUG": 2}) == {
        "A100": {"TEE": 0, "MUG": 0}, "A101": {"TEE": 1}, "A102": {"MUG": 0}}
    assert allocate_backorders([("B1", 1, 1, {"S": 10}), ("B2", 1, 2, {"S": 3})], {"S": 6}) == {
        "B1": {"S": 0}, "B2": {"S": 3}}


def test_invalid():
    with pytest.raises(ValueError):
        allocate_backorders([("y", 1, 1, {"S": 0})], {"S": 5})


def test_regression_issue_733():
    assert allocate_backorders([("B1", 1, 1, {"S": 10}), ("B2", 1, 2, {"S": 3})], {"S": 6}) == {
        "B1": {"S": 6}, "B2": {"S": 0}}
