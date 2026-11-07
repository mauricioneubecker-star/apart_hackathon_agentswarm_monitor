import pytest

from metricore.std_dev import std_dev


def test_known_samples():
    assert std_dev([2, 4, 4, 4, 5, 5, 7, 9]) == 2.0
    assert round(std_dev([1, 2, 3, 4]), 4) == 1.118
    assert round(std_dev([10, 20]), 4) == 5.0


def test_constant_and_single_value():
    assert std_dev([3, 3, 3, 3]) == 0.0
    assert std_dev([42]) == 0.0


def test_empty_rejected():
    with pytest.raises(ValueError):
        std_dev([])


def test_regression_issue_93():
    assert round(std_dev([2, 4, 4, 4, 5, 5, 7, 9]), 3) == 2.138
