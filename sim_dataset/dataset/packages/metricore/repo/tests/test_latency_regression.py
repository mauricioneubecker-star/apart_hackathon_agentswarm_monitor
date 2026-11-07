import pytest

from metricore.latency_regression import latency_regression


def test_unchanged_latency():
    result = latency_regression([100] * 10, [100] * 10)
    assert result["verdict"] == "ok"
    assert result["regressed"] == []
    assert result["changes"] == {"p50": 0.0, "p95": 0.0, "p99": 0.0}


def test_negative_tolerance():
    with pytest.raises(ValueError):
        latency_regression([1], [1], tolerance_pct=-1)
