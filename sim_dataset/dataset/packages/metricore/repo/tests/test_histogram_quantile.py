import pytest

from metricore.histogram_quantile import histogram_quantile


def test_interpolation():
    assert histogram_quantile(0.5, [100, 200], [10, 10, 0]) == 100.0
    assert histogram_quantile(0.75, [100, 200], [10, 10, 0]) == 150.0


def test_invalid_quantile():
    with pytest.raises(ValueError):
        histogram_quantile(-0.1, [100], [1, 0])
