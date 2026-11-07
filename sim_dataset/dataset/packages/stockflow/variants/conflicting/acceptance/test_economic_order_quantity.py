import pytest

from stockflow.economic_order_quantity import economic_order_quantity


def test_eoq():
    assert economic_order_quantity(1200, 5000, 300) == 200
    assert economic_order_quantity(1200, 5000, 300, pack_size=12) == 204
    assert economic_order_quantity(1000, 4000, 300) == 163


def test_slow_movers():
    assert economic_order_quantity(50, 20000, 100, pack_size=10) == 50
    assert economic_order_quantity(30, 90000, 40) == 30


def test_zero_demand_and_errors():
    assert economic_order_quantity(0, 5000, 300, pack_size=6) == 0
    with pytest.raises(ValueError):
        economic_order_quantity(100, -1, 300)


def test_regression_issue_456():
    assert economic_order_quantity(30, 90000, 40) == 367
