import pytest

from metricore.zscores import zscores


def test_known_scores():
    assert zscores([2, 4, 4, 4, 5, 5, 7, 9]) == [-1.5, -0.5, -0.5, -0.5, 0.0, 0.0, 1.0, 2.0]
    assert zscores([10, 20, 30]) == [-1.23, 0.0, 1.23]


def test_constant_series():
    assert zscores([5, 5, 5]) == [0.0, 0.0, 0.0]
    assert zscores([12.5]) == [0.0]


def test_empty():
    with pytest.raises(ValueError):
        zscores([])
