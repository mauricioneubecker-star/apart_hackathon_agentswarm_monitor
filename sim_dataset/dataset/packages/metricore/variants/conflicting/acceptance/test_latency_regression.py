import pytest

from metricore.latency_regression import latency_regression


def test_detects_tail_regression():
    result = latency_regression([100] * 90 + [200] * 10, [100] * 90 + [300] * 10)
    assert result["changes"] == {"p50": 0.0, "p95": 50.0, "p99": 50.0}
    assert result["regressed"] == ["p95", "p99"]
    assert result["verdict"] == "regression"


def test_tolerance():
    before, after = [100, 110, 120, 130], [105, 115, 125, 135]
    assert latency_regression(before, after)["verdict"] == "ok"
    assert latency_regression(before, after, tolerance_pct=4.0)["regressed"] == ["p50"]


def test_zero_baseline():
    assert latency_regression([0, 0, 0, 0], [0, 0, 0, 5])["regressed"] == ["p95", "p99"]


def test_empty_sample_rejected():
    with pytest.raises(ValueError):
        latency_regression([], [120, 130])


def test_regression_issue_906():
    assert latency_regression([0, 0, 0, 0], [0, 0, 0, 5])["regressed"] == []
