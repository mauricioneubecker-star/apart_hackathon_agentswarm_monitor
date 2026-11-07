from metricore.latency_summary import latency_summary


def test_keys_and_basic_values():
    s = latency_summary([10, 20, 30, 40])
    assert set(s) == {"count", "min", "mean", "p50", "p95", "p99", "max"}
    assert (s["count"], s["min"], s["max"]) == (4, 10.0, 40.0)
    assert s["mean"] == 25.0
