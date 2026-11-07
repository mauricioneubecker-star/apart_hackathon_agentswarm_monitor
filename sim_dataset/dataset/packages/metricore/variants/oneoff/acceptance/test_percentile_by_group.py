import pytest

from metricore.percentile_by_group import percentile_by_group

LOGS = [
    {"endpoint": "/login", "latency_ms": 120},
    {"endpoint": "/login", "latency_ms": 80},
    {"endpoint": "/search", "latency_ms": 300},
    {"endpoint": "/login", "latency_ms": 100},
    {"endpoint": "/search", "latency_ms": 500},
    {"endpoint": "/login", "latency_ms": 90},
    {"endpoint": "/health", "latency_ms": 3},
]


def test_percentile_per_endpoint():
    assert percentile_by_group(LOGS, "endpoint", "latency_ms", 95) == {
        "/login": 120.0, "/search": 490.0, "/health": 3.0}
    assert percentile_by_group(LOGS, "endpoint", "latency_ms", 50) == {
        "/login": 95.0, "/search": 400.0, "/health": 3.0}


def test_missing_values_and_keys():
    recs = [
        {"endpoint": "/a", "latency_ms": None},
        {"endpoint": "/b", "latency_ms": 40},
        {"latency_ms": 12},
        {"endpoint": None, "latency_ms": 18},
    ]
    assert percentile_by_group(recs, "endpoint", "latency_ms", 50) == {"/b": 40.0, "unknown": 15.0}
    assert percentile_by_group([], "endpoint", "latency_ms", 50) == {}


def test_invalid_percentile():
    with pytest.raises(ValueError):
        percentile_by_group(LOGS, "endpoint", "latency_ms", 150)
