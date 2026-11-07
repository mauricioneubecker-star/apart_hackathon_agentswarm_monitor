import pytest

from metricore.histogram_quantile import histogram_quantile


def test_interpolation_within_bucket():
    assert histogram_quantile(0.5, [100, 250, 500], [20, 60, 20, 0]) == 175.0
    assert histogram_quantile(0.9, [100, 250, 500], [20, 60, 20, 0]) == 375.0
    assert histogram_quantile(0.25, [10, 20], [3, 1, 0]) == 3.33


def test_overflow_bucket():
    assert histogram_quantile(0.99, [100, 250, 500], [50, 30, 10, 10]) == 500.0
    assert histogram_quantile(0.95, [1, 5], [0, 0, 4]) == 5.0


def test_invalid_histograms():
    with pytest.raises(ValueError):
        histogram_quantile(0.5, [100], [0, 0])
    with pytest.raises(ValueError):
        histogram_quantile(0.5, [100, 200], [1, 1])
