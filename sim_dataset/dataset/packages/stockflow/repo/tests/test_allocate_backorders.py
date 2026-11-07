import pytest

from stockflow.allocate_backorders import allocate_backorders


def test_example():
    orders = [("o1", 2, 10, {"S": 5}), ("o2", 1, 12, {"S": 4})]
    assert allocate_backorders(orders, {"S": 4}) == {"o1": {"S": 0}, "o2": {"S": 4}}
    assert allocate_backorders([], {"S": 4}) == {}


def test_duplicate_order():
    with pytest.raises(ValueError):
        allocate_backorders([("o1", 1, 1, {"S": 1}), ("o1", 1, 2, {"S": 1})], {"S": 5})
