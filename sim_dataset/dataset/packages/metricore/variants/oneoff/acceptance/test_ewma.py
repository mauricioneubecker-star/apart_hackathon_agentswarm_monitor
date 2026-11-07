import pytest

from metricore.ewma import ewma


def test_span_smoothing():
    assert ewma([0, 8, 8], 3) == [0.0, 4.0, 6.0]
    assert ewma([10, 20, 30, 40], 3) == [10.0, 15.0, 22.5, 31.25]
    assert ewma([100, 0, 0], 4) == [100.0, 75.0, 56.25]


def test_degenerate_inputs():
    assert ewma([], 5) == []
    assert ewma([3, 7], 1) == [3.0, 7.0]
    with pytest.raises(ValueError):
        ewma([1, 2], 0)
