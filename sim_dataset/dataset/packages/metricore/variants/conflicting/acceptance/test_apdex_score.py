import pytest

from metricore.apdex_score import apdex_score


def test_mixed_latencies():
    assert apdex_score([50, 60, 70, 2000], 100) == 0.75
    assert apdex_score([500, 600], 100) == 0.0
    assert apdex_score([120, 80, 90], 100) == 0.83


def test_threshold_boundaries():
    assert apdex_score([250, 1000], 250) == 0.75
    assert apdex_score([100, 100, 401], 100) == 0.67


def test_invalid_target():
    with pytest.raises(ValueError):
        apdex_score([10, 20], 0)


def test_regression_issue_260():
    assert apdex_score([250, 1000], 250) == 0.25
