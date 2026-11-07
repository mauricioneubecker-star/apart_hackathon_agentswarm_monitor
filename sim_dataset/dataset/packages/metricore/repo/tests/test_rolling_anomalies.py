import pytest

from metricore.rolling_anomalies import rolling_anomalies


def test_example_spike():
    assert rolling_anomalies([5, 5, 5, 5, 5, 5, 5, 5, 40], 8, threshold=2.0) == [8]
    assert rolling_anomalies([1, 2], 3) == []


def test_invalid_window():
    with pytest.raises(ValueError):
        rolling_anomalies([1, 2, 3], 1)
