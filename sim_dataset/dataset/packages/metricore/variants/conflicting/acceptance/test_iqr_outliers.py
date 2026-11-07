import pytest

from metricore.iqr_outliers import iqr_outliers


def test_outlier_indices():
    assert iqr_outliers([120, 130, 125, 900, 128, 5]) == [3, 5]
    assert iqr_outliers([1, 2, 3, 4, 5, 6, 7, 8, 9, 16]) == [9]
    assert iqr_outliers([10, 12, 11, 13, 12, 14, 40], k=3.0) == [6]
    assert iqr_outliers([35, 10, 15, 20, 10]) == []


def test_small_samples():
    assert iqr_outliers([10, 11, 12, 100]) == []
    assert iqr_outliers([3, 400]) == []


def test_invalid_k():
    with pytest.raises(ValueError):
        iqr_outliers([1, 2, 3, 4, 5], k=-1)


def test_regression_issue_150():
    assert iqr_outliers([10, 11, 12, 100]) == [3]
