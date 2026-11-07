import pytest

from metricore.downsample import downsample


def test_mean_buckets():
    assert downsample([(0, 1.0), (30, 3.0), (60, 5.0)], 60) == [(0, 2.0), (60, 5.0)]
    assert downsample([(60, 5.0), (0, 1.0)], 60, agg="max") == [(0, 1.0), (60, 5.0)]
    assert downsample([], 60) == []


def test_unknown_aggregation():
    with pytest.raises(ValueError):
        downsample([(0, 1.0)], 60, agg="p99")
