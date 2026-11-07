from metricore.latency_summary import latency_summary


def test_summary_values():
    assert latency_summary([10, 20, 30, 40]) == {
        "count": 4, "min": 10.0, "mean": 25.0, "p50": 25.0,
        "p95": 38.5, "p99": 39.7, "max": 40.0}
    s = latency_summary(list(range(1, 101)))
    assert (s["p50"], s["p95"], s["p99"]) == (50.5, 95.1, 99.0)


def test_rounding():
    assert latency_summary([7.25, 7.25])["p99"] == 7.2
    assert latency_summary([12.2, 12.3])["mean"] == 12.3


def test_empty_window():
    assert latency_summary([]) == {"count": 0, "min": None, "mean": None, "p50": None,
                                   "p95": None, "p99": None, "max": None}
