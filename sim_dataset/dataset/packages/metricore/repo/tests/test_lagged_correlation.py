import pytest

from metricore.lagged_correlation import lagged_correlation


def test_perfect_relationships():
    assert lagged_correlation([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert lagged_correlation([1, 2, 3], [9, 6, 3]) == -1.0


def test_length_mismatch():
    with pytest.raises(ValueError):
        lagged_correlation([1, 2, 3], [1, 2])
