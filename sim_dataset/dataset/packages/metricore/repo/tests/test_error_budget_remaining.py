import pytest

from metricore.error_budget_remaining import error_budget_remaining


def test_example_and_no_traffic():
    assert error_budget_remaining(0.99, 10_000, 25) == 75.0
    assert error_budget_remaining(0.999, 0, 0) == 100.0


def test_invalid_target():
    with pytest.raises(ValueError):
        error_budget_remaining(0.0, 100, 1)
