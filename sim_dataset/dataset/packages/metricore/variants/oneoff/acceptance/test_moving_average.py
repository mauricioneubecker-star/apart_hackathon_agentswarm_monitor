import pytest

from metricore.moving_average import moving_average


def test_trailing_window():
    assert moving_average([2, 4, 6, 8], 3) == [2.0, 3.0, 4.0, 6.0]
    assert moving_average([10, 20, 30, 40, 50], 2) == [10.0, 15.0, 25.0, 35.0, 45.0]
    assert moving_average([1, 2, 2], 3)[-1] == 1.66


def test_window_longer_than_series():
    assert moving_average([3, 6], 5) == [3.0, 4.5]


def test_invalid_window():
    with pytest.raises(ValueError):
        moving_average([1, 2, 3], 0)
