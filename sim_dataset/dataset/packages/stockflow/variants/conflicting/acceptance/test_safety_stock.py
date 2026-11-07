import pytest

from stockflow.safety_stock import safety_stock


def test_whole_numbers():
    assert safety_stock([10, 20, 30], [4, 6]) == 80
    assert safety_stock([5, 5, 5], [2, 2]) == 0
    assert safety_stock([7, 8, 9], [5]) == 5


def test_fractional_result():
    assert safety_stock([10, 15], [3, 4]) == 17
    assert safety_stock([1, 2], [1, 2]) == 2


def test_errors():
    with pytest.raises(ValueError):
        safety_stock([4, 6], [])
    with pytest.raises(ValueError):
        safety_stock([4, 6], [2, -1])


def test_regression_issue_163():
    assert safety_stock([10, 15], [3, 4]) == 16
