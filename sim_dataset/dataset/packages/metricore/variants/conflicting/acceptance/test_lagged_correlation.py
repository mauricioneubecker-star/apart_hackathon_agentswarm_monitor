import pytest

from metricore.lagged_correlation import lagged_correlation


def test_no_lag():
    assert lagged_correlation([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert lagged_correlation([1, 2, 3, 4, 5], [2, 1, 4, 3, 5]) == 0.8
    assert lagged_correlation([3, 1, 2], [1, 3, 2]) == -1.0


def test_lagged_pairs():
    assert lagged_correlation([1, 5, 2, 8, 3], [0, 1, 5, 2, 8], lag=1) == 1.0
    assert lagged_correlation([0, 1, 5, 2, 8], [1, 5, 2, 8, 3], lag=-1) == 1.0


def test_invalid_series():
    with pytest.raises(ValueError):
        lagged_correlation([4, 4, 4], [1, 2, 3])


def test_regression_issue_725():
    assert lagged_correlation([1, 5, 2, 8, 3], [0, 1, 5, 2, 8], lag=1) == 0.7
