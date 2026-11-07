import pytest

from metricore.moving_average import moving_average


def test_basic_windows():
    assert moving_average([2, 4, 6, 8], 2)[-1] == 7.0
    assert moving_average([5, 1, 3], 1) == [5.0, 1.0, 3.0]
    assert moving_average([], 3) == []


def test_invalid_window():
    with pytest.raises(ValueError):
        moving_average([1, 2], 0)
