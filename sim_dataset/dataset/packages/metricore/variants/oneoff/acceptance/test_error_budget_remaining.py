import pytest

from metricore.error_budget_remaining import error_budget_remaining


def test_partially_spent():
    assert error_budget_remaining(0.999, 1_000_000, 250) == 75.0
    assert error_budget_remaining(0.995, 40_000, 0) == 100.0
    assert error_budget_remaining(0.99, 3_000, 10) == 66.6


def test_overspent_budget():
    assert error_budget_remaining(0.99, 1000, 30) == -200.0
    assert error_budget_remaining(0.999, 20_000, 20) == 0.0


def test_invalid_arguments():
    with pytest.raises(ValueError):
        error_budget_remaining(1.0, 100, 1)
