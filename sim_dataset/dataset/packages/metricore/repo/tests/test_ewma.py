import pytest

from metricore.ewma import ewma


def test_constant_series_and_no_smoothing():
    assert ewma([10, 10, 10], 5) == [10.0, 10.0, 10.0]
    assert ewma([3, 9, 1], 1) == [3.0, 9.0, 1.0]
    assert ewma([], 4) == []


def test_invalid_span():
    with pytest.raises(ValueError):
        ewma([1.0], 0)
