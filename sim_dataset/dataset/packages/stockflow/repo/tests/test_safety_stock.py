import pytest

from stockflow.safety_stock import safety_stock


def test_examples():
    assert safety_stock([10, 20, 30], [4, 6]) == 80
    assert safety_stock([5, 5, 5], [2, 2]) == 0


def test_empty_history():
    with pytest.raises(ValueError):
        safety_stock([], [3])
