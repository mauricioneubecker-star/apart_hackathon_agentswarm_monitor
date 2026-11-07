import pytest

from stockflow.economic_order_quantity import economic_order_quantity


def test_examples():
    assert economic_order_quantity(1200, 5000, 300) == 200
    assert economic_order_quantity(0, 5000, 300) == 0


def test_zero_holding_cost():
    with pytest.raises(ValueError):
        economic_order_quantity(100, 5000, 0)
