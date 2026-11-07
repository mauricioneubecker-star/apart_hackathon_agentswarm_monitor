import pytest

from metricore.rolling_anomalies import rolling_anomalies


def test_spike_against_baseline():
    assert rolling_anomalies([10, 11, 10, 11, 10, 11, 50], 4) == [6]
    assert rolling_anomalies([10, 12, 10, 12, 30, 11, 10, 12], 4, threshold=2.0) == [4]


def test_short_series_and_flat_baseline():
    assert rolling_anomalies([1, 2, 3], 3) == []
    assert rolling_anomalies([7, 7, 7, 8], 3) == [3]


def test_invalid_threshold():
    with pytest.raises(ValueError):
        rolling_anomalies([1, 2, 3, 4], 2, threshold=0)
