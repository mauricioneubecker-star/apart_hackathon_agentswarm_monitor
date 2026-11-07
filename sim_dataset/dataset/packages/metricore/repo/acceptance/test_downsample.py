import pytest

from metricore.downsample import downsample


def test_aggregations():
    pts = [(120, 4.0), (0, 1.0), (100, 6.0), (45, 2.0), (61, 10.0)]
    assert downsample(pts, 60) == [(0, 1.5), (60, 8.0), (120, 4.0)]
    assert downsample(pts, 60, agg="max") == [(0, 2.0), (60, 10.0), (120, 4.0)]
    assert downsample(pts, 60, agg="last") == [(0, 2.0), (60, 6.0), (120, 4.0)]


def test_epoch_alignment():
    pts = [(90, 1.0), (130, 2.0), (170, 4.0), (185, 8.0)]
    assert downsample(pts, 60, agg="sum") == [(60, 1.0), (120, 6.0), (180, 8.0)]
    assert downsample([(1000, 5.0), (1100, 7.0)], 300) == [(900, 6.0)]


def test_invalid_arguments():
    with pytest.raises(ValueError):
        downsample([(0, 1.0)], 60, agg="median")
