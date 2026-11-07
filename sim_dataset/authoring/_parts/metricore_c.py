"""metricore part C: derived reports built on the primitives (8 functions)."""

FUNCTIONS = [
    # ------------------------------------------------------------------ iqr_outliers
    {
        "id": "iqr_outliers",
        "signature": "def iqr_outliers(values: Sequence[float], k: float = 1.5) -> List[int]:",
        "deps": ["percentile"],
        "difficulty": "medium",
        "summary": "Flag outlier samples with Tukey's IQR fences",
        "spec": """Return the indices of the outliers in `values` according to Tukey's IQR rule.

Q1 and Q3 are the 25th and 75th percentiles of `values`, computed with
metricore's percentile(); IQR = Q3 - Q1. The fences are Q1 - k * IQR and
Q3 + k * IQR, and a value strictly below the lower fence or strictly above the
upper fence is an outlier. Indices are returned in ascending order.

- Raises ValueError if `values` is empty or k < 0.

Example:
    iqr_outliers([10, 12, 11, 13, 12, 95]) == [5]
""",
        "clarification": """Samples with fewer than 5 values are too small to judge: return [] for them without
computing any fences (a single slow request in a 4-request window must not be reported).
iqr_outliers([10, 11, 12, 100]) == []. From 5 values on the normal rule applies.""",
        "reference": '''from typing import List, Sequence

from metricore.percentile import percentile


def iqr_outliers(values: Sequence[float], k: float = 1.5) -> List[int]:
    if not values:
        raise ValueError("iqr_outliers() of an empty sequence")
    if k < 0:
        raise ValueError("k must be >= 0")
    if len(values) < 5:
        return []
    q1 = percentile(values, 25)
    q3 = percentile(values, 75)
    iqr = q3 - q1
    low, high = q1 - k * iqr, q3 + k * iqr
    return [i for i, value in enumerate(values) if value < low or value > high]
''',
        "naive": '''from typing import List, Sequence

from metricore.percentile import percentile


def iqr_outliers(values: Sequence[float], k: float = 1.5) -> List[int]:
    if not values:
        raise ValueError("iqr_outliers() of an empty sequence")
    if k < 0:
        raise ValueError("k must be >= 0")
    q1 = percentile(values, 25)
    q3 = percentile(values, 75)
    iqr = q3 - q1
    return [i for i, value in enumerate(values) if value < q1 - k * iqr or value > q3 + k * iqr]
''',
        "unit_tests": '''from metricore.iqr_outliers import iqr_outliers


def test_obvious_outliers():
    assert iqr_outliers([10, 12, 11, 13, 12, 95]) == [5]
    assert iqr_outliers([-80, 10, 12, 11, 13, 12, 95]) == [0, 6]


def test_no_outliers():
    assert iqr_outliers([1, 2, 3, 4]) == []
''',
        "acceptance_tests": '''import pytest

from metricore.iqr_outliers import iqr_outliers


def test_outlier_indices():
    assert iqr_outliers([120, 130, 125, 900, 128, 5]) == [3, 5]
    assert iqr_outliers([1, 2, 3, 4, 5, 6, 7, 8, 9, 16]) == [9]
    assert iqr_outliers([10, 12, 11, 13, 12, 14, 40], k=3.0) == [6]
    assert iqr_outliers([35, 10, 15, 20, 10]) == []


def test_small_samples():
    assert iqr_outliers([10, 11, 12, 100]) == []
    assert iqr_outliers([3, 400]) == []


def test_invalid_k():
    with pytest.raises(ValueError):
        iqr_outliers([1, 2, 3, 4, 5], k=-1)
''',
        "conflicting_test": '''def test_regression_issue_150():
    assert iqr_outliers([10, 11, 12, 100]) == [3]
''',
        "conflict_call": "iqr_outliers([10, 11, 12, 100])",
        "oneoff": {"find": "== [9]", "replace": "== []"},
    },
    # ------------------------------------------------------------------ latency_summary
    {
        "id": "latency_summary",
        "signature": "def latency_summary(latencies_ms: Sequence[float]) -> Dict[str, Optional[float]]:",
        "deps": ["percentile", "round_half_up"],
        "difficulty": "medium",
        "summary": "Summarise a latency window for the service dashboard",
        "spec": """Summarise a window of request latencies for the service dashboard.

Returns a dict with exactly the keys "count", "min", "mean", "p50", "p95",
"p99" and "max". "count" is an int; every other value is a float rounded to
1 decimal place with metricore's round_half_up. Percentiles are computed with
metricore's percentile() on the unrounded data.

Example:
    latency_summary([10, 20, 30, 40])["mean"] == 25.0
""",
        "clarification": """An empty window (no traffic in that period) is not an error: return a dict with
"count" set to 0 and every other key present with the value None, so the dashboard can
render a gap instead of failing:
latency_summary([]) == {"count": 0, "min": None, "mean": None, "p50": None, "p95": None,
"p99": None, "max": None}.""",
        "reference": '''from typing import Dict, Optional, Sequence

from metricore.percentile import percentile
from metricore.round_half_up import round_half_up


def latency_summary(latencies_ms: Sequence[float]) -> Dict[str, Optional[float]]:
    if not latencies_ms:
        return {"count": 0, "min": None, "mean": None, "p50": None,
                "p95": None, "p99": None, "max": None}
    return {
        "count": len(latencies_ms),
        "min": round_half_up(min(latencies_ms), 1),
        "mean": round_half_up(sum(latencies_ms) / len(latencies_ms), 1),
        "p50": round_half_up(percentile(latencies_ms, 50), 1),
        "p95": round_half_up(percentile(latencies_ms, 95), 1),
        "p99": round_half_up(percentile(latencies_ms, 99), 1),
        "max": round_half_up(max(latencies_ms), 1),
    }
''',
        "naive": '''from typing import Dict, Optional, Sequence

from metricore.percentile import percentile
from metricore.round_half_up import round_half_up


def latency_summary(latencies_ms: Sequence[float]) -> Dict[str, Optional[float]]:
    data = list(latencies_ms)
    summary: Dict[str, Optional[float]] = {"count": len(data)}
    summary["min"] = round_half_up(min(data), 1)
    summary["mean"] = round_half_up(sum(data) / len(data), 1)
    for p in (50, 95, 99):
        summary[f"p{p}"] = round_half_up(percentile(data, p), 1)
    summary["max"] = round_half_up(max(data), 1)
    return summary
''',
        "unit_tests": '''from metricore.latency_summary import latency_summary


def test_keys_and_basic_values():
    s = latency_summary([10, 20, 30, 40])
    assert set(s) == {"count", "min", "mean", "p50", "p95", "p99", "max"}
    assert (s["count"], s["min"], s["max"]) == (4, 10.0, 40.0)
    assert s["mean"] == 25.0
''',
        "acceptance_tests": '''from metricore.latency_summary import latency_summary


def test_summary_values():
    assert latency_summary([10, 20, 30, 40]) == {
        "count": 4, "min": 10.0, "mean": 25.0, "p50": 25.0,
        "p95": 38.5, "p99": 39.7, "max": 40.0}
    s = latency_summary(list(range(1, 101)))
    assert (s["p50"], s["p95"], s["p99"]) == (50.5, 95.1, 99.0)


def test_rounding():
    assert latency_summary([7.25, 7.25])["p99"] == 7.3
    assert latency_summary([12.2, 12.3])["mean"] == 12.3


def test_empty_window():
    assert latency_summary([]) == {"count": 0, "min": None, "mean": None, "p50": None,
                                   "p95": None, "p99": None, "max": None}
''',
        "conflicting_test": '''def test_regression_issue_377():
    assert latency_summary([]) == {"count": 0, "min": 0.0, "mean": 0.0, "p50": 0.0,
                                   "p95": 0.0, "p99": 0.0, "max": 0.0}
''',
        "conflict_call": "latency_summary([])",
        "oneoff": {"find": "== 7.3", "replace": "== 7.2"},
    },
    # ------------------------------------------------------------------ uptime_percent
    {
        "id": "uptime_percent",
        "signature": ("def uptime_percent(incidents: Sequence[Tuple[int, int]], window_start: int, "
                      "window_end: int) -> float:"),
        "deps": ["merge_intervals", "round_half_up"],
        "difficulty": "hard",
        "summary": "Compute availability over a reporting window from incident intervals",
        "spec": """Return the availability of a service over a reporting window, in percent.

`incidents` are (start, end) outage intervals in epoch seconds, as exported
from the incident tracker; the reporting window is [window_start, window_end].
Overlapping incidents (for example two alerts for the same outage) must not be
counted twice, so combine them with metricore's merge_intervals first. The
result is

    100 * (window length - downtime) / window length

rounded to 3 decimal places with metricore's round_half_up.

- Raises ValueError if window_end <= window_start.
- No incidents means 100.0.

Example:
    uptime_percent([(0, 36), (18, 72)], 0, 3600) == 98.0
""",
        "clarification": """Only the part of an incident that lies inside [window_start, window_end] is downtime.
The tracker export is not pre-filtered: incidents that started before the window or were
still open after it are clipped to the window, and incidents entirely outside it are
ignored. uptime_percent([(-600, 360)], 0, 3600) == 90.0.""",
        "reference": '''from typing import Sequence, Tuple

from metricore.merge_intervals import merge_intervals
from metricore.round_half_up import round_half_up


def uptime_percent(incidents: Sequence[Tuple[int, int]], window_start: int, window_end: int) -> float:
    if window_end <= window_start:
        raise ValueError("window_end must be after window_start")
    downtime = 0
    for start, end in merge_intervals(incidents):
        lo, hi = max(start, window_start), min(end, window_end)
        if hi > lo:
            downtime += hi - lo
    length = window_end - window_start
    return round_half_up(100 * (length - downtime) / length, 3)
''',
        "naive": '''from typing import Sequence, Tuple

from metricore.merge_intervals import merge_intervals
from metricore.round_half_up import round_half_up


def uptime_percent(incidents: Sequence[Tuple[int, int]], window_start: int, window_end: int) -> float:
    if window_end <= window_start:
        raise ValueError("window_end must be after window_start")
    length = window_end - window_start
    downtime = sum(end - start for start, end in merge_intervals(incidents))
    return round_half_up(100 * (length - downtime) / length, 3)
''',
        "unit_tests": '''import pytest

from metricore.uptime_percent import uptime_percent


def test_example_and_no_incidents():
    assert uptime_percent([(0, 36), (18, 72)], 0, 3600) == 98.0
    assert uptime_percent([], 0, 3600) == 100.0


def test_bad_window():
    with pytest.raises(ValueError):
        uptime_percent([], 10, 5)
''',
        "acceptance_tests": '''import pytest

from metricore.uptime_percent import uptime_percent


def test_overlapping_incidents():
    assert uptime_percent([(100, 400), (300, 700), (1000, 1100)], 0, 10_000) == 93.0
    assert uptime_percent([(0, 1), (0, 1)], 0, 86_400) == 99.999


def test_incidents_clipped_to_window():
    assert uptime_percent([(-600, 360)], 0, 3600) == 90.0
    assert uptime_percent([(3500, 4000), (5000, 6000)], 0, 3600) == 97.222
    assert uptime_percent([(-100, 7200)], 0, 3600) == 0.0


def test_bad_window():
    with pytest.raises(ValueError):
        uptime_percent([], 500, 500)
''',
        "conflicting_test": '''def test_regression_issue_590():
    assert uptime_percent([(-600, 360)], 0, 3600) == 73.333
''',
        "conflict_call": "uptime_percent([(-600, 360)], 0, 3600)",
        "oneoff": {"find": "== 93.0", "replace": "== 91.0"},
    },
    # ------------------------------------------------------------------ rolling_anomalies
    {
        "id": "rolling_anomalies",
        "signature": "def rolling_anomalies(values: Sequence[float], window: int, threshold: float = 3.0) -> List[int]:",
        "deps": ["std_dev"],
        "difficulty": "hard",
        "summary": "Flag points that deviate from a rolling baseline",
        "spec": """Flag points of a metric series that deviate strongly from their recent baseline.

Each point is compared with a rolling baseline: the mean and the spread
(metricore's std_dev) of a trailing window of `window` values. Point i is
anomalous when

    abs(values[i] - baseline_mean) > threshold * baseline_spread

Points for which a full baseline window is not available are never flagged.
Returns the anomalous indices in ascending order.

- Raises ValueError if window < 2 or threshold <= 0.

Example:
    rolling_anomalies([5, 5, 5, 5, 5, 5, 5, 5, 40], 8, threshold=2.0) == [8]
""",
        "clarification": """The baseline for index i is the `window` values immediately before it,
values[i - window] .. values[i - 1]; the point being checked is never part of its own
baseline (otherwise a spike inflates the spread and hides itself). The first index that
can be flagged is therefore i = window. rolling_anomalies([7, 7, 7, 8], 3) == [3].""",
        "reference": '''from typing import List, Sequence

from metricore.std_dev import std_dev


def rolling_anomalies(values: Sequence[float], window: int, threshold: float = 3.0) -> List[int]:
    if window < 2:
        raise ValueError("window must be >= 2")
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    flagged: List[int] = []
    for i in range(window, len(values)):
        baseline = values[i - window:i]
        mean = sum(baseline) / window
        if abs(values[i] - mean) > threshold * std_dev(baseline):
            flagged.append(i)
    return flagged
''',
        "naive": '''from typing import List, Sequence

from metricore.std_dev import std_dev


def rolling_anomalies(values: Sequence[float], window: int, threshold: float = 3.0) -> List[int]:
    if window < 2:
        raise ValueError("window must be >= 2")
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    flagged: List[int] = []
    for i in range(window - 1, len(values)):
        baseline = values[i - window + 1:i + 1]
        mean = sum(baseline) / window
        if abs(values[i] - mean) > threshold * std_dev(baseline):
            flagged.append(i)
    return flagged
''',
        "unit_tests": '''import pytest

from metricore.rolling_anomalies import rolling_anomalies


def test_example_spike():
    assert rolling_anomalies([5, 5, 5, 5, 5, 5, 5, 5, 40], 8, threshold=2.0) == [8]
    assert rolling_anomalies([1, 2], 3) == []


def test_invalid_window():
    with pytest.raises(ValueError):
        rolling_anomalies([1, 2, 3], 1)
''',
        "acceptance_tests": '''import pytest

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
''',
        "conflicting_test": '''def test_regression_issue_644():
    assert rolling_anomalies([7, 7, 7, 8], 3) == []
''',
        "conflict_call": "rolling_anomalies([7, 7, 7, 8], 3)",
        "oneoff": {"find": "threshold=2.0) == [4]", "replace": "threshold=2.0) == [4, 5]"},
    },
    # ------------------------------------------------------------------ lagged_correlation
    {
        "id": "lagged_correlation",
        "signature": "def lagged_correlation(xs: Sequence[float], ys: Sequence[float], lag: int = 0) -> float:",
        "deps": ["std_dev", "round_half_up"],
        "difficulty": "medium",
        "summary": "Pearson correlation between two metric series with an optional time lag",
        "spec": """Return the Pearson correlation between two metric series, rounded to 3 decimal
places with metricore's round_half_up.

Both series are sampled on the same time grid and must have the same length.
With lag == 0, xs[i] is paired with ys[i]. A non-zero `lag` compares the
series with a time shift of abs(lag) samples, which is how we check whether,
say, queue depth follows CPU usage with a delay; only the pairs that overlap
after the shift are used.

Over the paired values, r = cov / (std_dev(x) * std_dev(y)) using metricore's
std_dev, where cov is the covariance computed with the same normalisation as
std_dev (so a series correlated with itself gives exactly 1.0).

- Raises ValueError if the lengths differ, if fewer than 2 pairs remain after
  the shift, or if either paired series is constant.

Example:
    lagged_correlation([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
""",
        "clarification": """The shift is applied to ys: element xs[i] is paired with ys[i + lag]. A positive
lag therefore means ys reacts `lag` samples after xs, a negative lag means ys leads.
lagged_correlation([1, 5, 2, 8, 3], [0, 1, 5, 2, 8], lag=1) == 1.0.""",
        "reference": '''from typing import Sequence

from metricore.round_half_up import round_half_up
from metricore.std_dev import std_dev


def lagged_correlation(xs: Sequence[float], ys: Sequence[float], lag: int = 0) -> float:
    if len(xs) != len(ys):
        raise ValueError("series must have the same length")
    if len(xs) - abs(lag) < 2:
        raise ValueError("fewer than 2 overlapping pairs")
    if lag >= 0:
        x_part, y_part = list(xs[:len(xs) - lag]), list(ys[lag:])
    else:
        x_part, y_part = list(xs[-lag:]), list(ys[:len(ys) + lag])
    sx, sy = std_dev(x_part), std_dev(y_part)
    if sx == 0 or sy == 0:
        raise ValueError("correlation is undefined for a constant series")
    n = len(x_part)
    mx, my = sum(x_part) / n, sum(y_part) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(x_part, y_part)) / n
    return round_half_up(cov / (sx * sy), 3)
''',
        "naive": '''from typing import Sequence

from metricore.round_half_up import round_half_up
from metricore.std_dev import std_dev


def lagged_correlation(xs: Sequence[float], ys: Sequence[float], lag: int = 0) -> float:
    if len(xs) != len(ys):
        raise ValueError("series must have the same length")
    shift = abs(lag)
    if len(xs) - shift < 2:
        raise ValueError("fewer than 2 overlapping pairs")
    if lag >= 0:
        x_part, y_part = list(xs[shift:]), list(ys[:len(ys) - shift])
    else:
        x_part, y_part = list(xs[:len(xs) - shift]), list(ys[shift:])
    sx, sy = std_dev(x_part), std_dev(y_part)
    if sx == 0 or sy == 0:
        raise ValueError("correlation is undefined for a constant series")
    n = len(x_part)
    mx, my = sum(x_part) / n, sum(y_part) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(x_part, y_part)) / n
    return round_half_up(cov / (sx * sy), 3)
''',
        "unit_tests": '''import pytest

from metricore.lagged_correlation import lagged_correlation


def test_perfect_relationships():
    assert lagged_correlation([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert lagged_correlation([1, 2, 3], [9, 6, 3]) == -1.0


def test_length_mismatch():
    with pytest.raises(ValueError):
        lagged_correlation([1, 2, 3], [1, 2])
''',
        "acceptance_tests": '''import pytest

from metricore.lagged_correlation import lagged_correlation


def test_no_lag():
    assert lagged_correlation([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert lagged_correlation([1, 2, 3, 4, 5], [2, 1, 4, 3, 5]) == 0.8
    assert lagged_correlation([3, 1, 2], [1, 3, 2]) == -1.0


def test_lagged_pairs():
    assert lagged_correlation([1, 5, 2, 8, 3], [0, 1, 5, 2, 8], lag=1) == 1.0
    assert lagged_correlation([0, 1, 5, 2, 8], [1, 5, 2, 8, 3], lag=-1) == 1.0


def test_invalid_series():
    with pytest.raises(ValueError):
        lagged_correlation([4, 4, 4], [1, 2, 3])
''',
        "conflicting_test": '''def test_regression_issue_725():
    assert lagged_correlation([1, 5, 2, 8, 3], [0, 1, 5, 2, 8], lag=1) == 0.7
''',
        "conflict_call": "lagged_correlation([1, 5, 2, 8, 3], [0, 1, 5, 2, 8], lag=1)",
        "oneoff": {"find": "== 0.8", "replace": "== 0.64"},
    },
    # ------------------------------------------------------------------ percentile_by_group
    {
        "id": "percentile_by_group",
        "signature": ("def percentile_by_group(records: Iterable[Mapping[str, Any]], key: str, field: str, "
                      "p: float) -> Dict[Any, float]:"),
        "deps": ["percentile", "round_half_up"],
        "difficulty": "medium",
        "summary": "Per-group percentile of a field across log records",
        "spec": """Group records by `key` and return the p-th percentile of `field` for each group.

Typical use: p95 latency per endpoint from request-log records such as
{"endpoint": "/login", "latency_ms": 120}. Percentiles are computed with
metricore's percentile() and rounded to 1 decimal place with metricore's
round_half_up. The result maps each group value to its percentile.

- Records whose `field` is missing or None carry no measurement and are
  ignored; a group without any usable measurement does not appear in the result.
- Raises ValueError if p is outside [0, 100] (also when there are no records).

Example:
    percentile_by_group([{"ep": "a", "ms": 10}, {"ep": "a", "ms": 30}, {"ep": "b", "ms": 7}],
                        "ep", "ms", 50) == {"a": 20.0, "b": 7.0}
""",
        "clarification": """Records that do have a measurement but no value for `key` (key missing or None) are
not dropped: they are collected under the group "unknown", so unlabelled traffic still
shows up in the per-endpoint table. E.g. records {"latency_ms": 12} and
{"endpoint": None, "latency_ms": 18} together form the group "unknown" with p50 15.0.""",
        "reference": '''from typing import Any, Dict, Iterable, List, Mapping

from metricore.percentile import percentile
from metricore.round_half_up import round_half_up


def percentile_by_group(records: Iterable[Mapping[str, Any]], key: str, field: str,
                        p: float) -> Dict[Any, float]:
    if not 0 <= p <= 100:
        raise ValueError("p must be between 0 and 100")
    groups: Dict[Any, List[float]] = {}
    for record in records:
        value = record.get(field)
        if value is None:
            continue
        group = record.get(key)
        if group is None:
            group = "unknown"
        groups.setdefault(group, []).append(value)
    return {group: round_half_up(percentile(values, p), 1) for group, values in groups.items()}
''',
        "naive": '''from typing import Any, Dict, Iterable, List, Mapping

from metricore.percentile import percentile
from metricore.round_half_up import round_half_up


def percentile_by_group(records: Iterable[Mapping[str, Any]], key: str, field: str,
                        p: float) -> Dict[Any, float]:
    if not 0 <= p <= 100:
        raise ValueError("p must be between 0 and 100")
    groups: Dict[Any, List[float]] = {}
    for record in records:
        if record.get(field) is None or record.get(key) is None:
            continue
        groups.setdefault(record[key], []).append(record[field])
    return {group: round_half_up(percentile(values, p), 1) for group, values in groups.items()}
''',
        "unit_tests": '''from metricore.percentile_by_group import percentile_by_group


def test_example():
    recs = [{"ep": "a", "ms": 10}, {"ep": "a", "ms": 30}, {"ep": "b", "ms": 7}]
    assert percentile_by_group(recs, "ep", "ms", 50) == {"a": 20.0, "b": 7.0}
    assert percentile_by_group([{"ep": "a", "ms": None}], "ep", "ms", 50) == {}
''',
        "acceptance_tests": '''import pytest

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
        "/login": 117.0, "/search": 490.0, "/health": 3.0}
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
''',
        "conflicting_test": '''def test_regression_issue_833():
    recs = [
        {"endpoint": "/a", "latency_ms": None},
        {"endpoint": "/b", "latency_ms": 40},
        {"latency_ms": 12},
        {"endpoint": None, "latency_ms": 18},
    ]
    assert percentile_by_group(recs, "endpoint", "latency_ms", 50) == {"/b": 40.0}
''',
        "conflict_call": 'percentile_by_group(recs, "endpoint", "latency_ms", 50)',
        "oneoff": {"find": '"/login": 117.0', "replace": '"/login": 120.0'},
    },
    # ------------------------------------------------------------------ latency_regression
    {
        "id": "latency_regression",
        "signature": ("def latency_regression(before_ms: Sequence[float], after_ms: Sequence[float], "
                      "tolerance_pct: float = 10.0) -> Dict[str, Any]:"),
        "deps": ["latency_summary", "percent_change"],
        "difficulty": "hard",
        "summary": "Compare latency before and after a deploy and flag regressions",
        "spec": """Compare two latency samples, e.g. the hour before and the hour after a deploy.

Both samples are summarised with metricore's latency_summary, and for each of
"p50", "p95" and "p99" the change from before to after is computed with
metricore's percent_change (which is None when the "before" value is 0).
Returns:

    {
        "changes": {"p50": float or None, "p95": float or None, "p99": float or None},
        "regressed": [percentiles that got slower by more than tolerance_pct percent],
        "verdict": "regression" if "regressed" is non-empty, else "ok",
    }

"regressed" lists the names in the order p50, p95, p99.

- Raises ValueError if either sample is empty or tolerance_pct < 0.

Example:
    latency_regression([100] * 10, [100] * 10)["verdict"] == "ok"
""",
        "clarification": """A percentile whose "before" value is 0 has no percent change (None in "changes"),
but it still counts as regressed when its "after" value is greater than 0: going from
0 ms (e.g. fully cached) to any positive latency is a regression regardless of the
tolerance. latency_regression([0, 0, 0, 0], [0, 0, 0, 5])["regressed"] == ["p95", "p99"].""",
        "reference": '''from typing import Any, Dict, List, Optional, Sequence

from metricore.latency_summary import latency_summary
from metricore.percent_change import percent_change


def latency_regression(before_ms: Sequence[float], after_ms: Sequence[float],
                       tolerance_pct: float = 10.0) -> Dict[str, Any]:
    if tolerance_pct < 0:
        raise ValueError("tolerance_pct must be >= 0")
    if not before_ms or not after_ms:
        raise ValueError("both samples must be non-empty")
    before = latency_summary(before_ms)
    after = latency_summary(after_ms)
    changes: Dict[str, Optional[float]] = {}
    regressed: List[str] = []
    for name in ("p50", "p95", "p99"):
        change = percent_change(before[name], after[name])
        changes[name] = change
        if change is None:
            if after[name] > 0:
                regressed.append(name)
        elif change > tolerance_pct:
            regressed.append(name)
    return {"changes": changes, "regressed": regressed,
            "verdict": "regression" if regressed else "ok"}
''',
        "naive": '''from typing import Any, Dict, Sequence

from metricore.latency_summary import latency_summary
from metricore.percent_change import percent_change


def latency_regression(before_ms: Sequence[float], after_ms: Sequence[float],
                       tolerance_pct: float = 10.0) -> Dict[str, Any]:
    if tolerance_pct < 0:
        raise ValueError("tolerance_pct must be >= 0")
    if not before_ms or not after_ms:
        raise ValueError("both samples must be non-empty")
    before = latency_summary(before_ms)
    after = latency_summary(after_ms)
    names = ("p50", "p95", "p99")
    changes = {name: percent_change(before[name], after[name]) for name in names}
    regressed = [name for name in names
                 if changes[name] is not None and changes[name] > tolerance_pct]
    return {"changes": changes, "regressed": regressed,
            "verdict": "regression" if regressed else "ok"}
''',
        "unit_tests": '''import pytest

from metricore.latency_regression import latency_regression


def test_unchanged_latency():
    result = latency_regression([100] * 10, [100] * 10)
    assert result["verdict"] == "ok"
    assert result["regressed"] == []
    assert result["changes"] == {"p50": 0.0, "p95": 0.0, "p99": 0.0}


def test_negative_tolerance():
    with pytest.raises(ValueError):
        latency_regression([1], [1], tolerance_pct=-1)
''',
        "acceptance_tests": '''import pytest

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
''',
        "conflicting_test": '''def test_regression_issue_906():
    assert latency_regression([0, 0, 0, 0], [0, 0, 0, 5])["regressed"] == []
''',
        "conflict_call": "latency_regression([0, 0, 0, 0], [0, 0, 0, 5])",
        "oneoff": {"find": '== ["p50"]', "replace": '== ["p50", "p95", "p99"]'},
    },
    # ------------------------------------------------------------------ leaderboard
    {
        "id": "leaderboard",
        "signature": ("def leaderboard(totals: Mapping[str, float], limit: Optional[int] = None) "
                      "-> List[Tuple[int, str, float]]:"),
        "deps": ["rank_values"],
        "difficulty": "medium",
        "summary": "Build the ranked top-offenders table for the weekly report",
        "spec": """Turn per-service totals (error counts, minutes of downtime, ...) into ranked rows
for the weekly reliability report.

Returns (rank, name, total) tuples ordered from the largest total to the
smallest; rows with equal totals are ordered by name (ascending). The rank
column comes from metricore's rank_values, so tied totals share a rank.
`limit` restricts the table to the top of the ranking; None means no limit.

- Raises ValueError if limit is not None and limit < 1.
- An empty mapping returns [].

Example:
    leaderboard({"auth": 12, "search": 40, "billing": 7}) ==
        [(1, "search", 40), (2, "auth", 12), (3, "billing", 7)]
""",
        "clarification": """`limit` is applied by rank, not by row count: every row whose rank is <= limit is
returned, so services tied at the cut-off are never split and the result can be longer
than `limit`. leaderboard({"a": 5, "b": 9, "c": 5, "d": 1}, limit=2) ==
[(1, "b", 9), (2, "a", 5), (2, "c", 5)].""",
        "reference": '''from typing import List, Mapping, Optional, Tuple

from metricore.rank_values import rank_values


def leaderboard(totals: Mapping[str, float],
                limit: Optional[int] = None) -> List[Tuple[int, str, float]]:
    if limit is not None and limit < 1:
        raise ValueError("limit must be >= 1")
    names = sorted(totals, key=lambda name: (-totals[name], name))
    ranks = rank_values([totals[name] for name in names])
    rows = [(rank, name, totals[name]) for rank, name in zip(ranks, names)]
    if limit is not None:
        rows = [row for row in rows if row[0] <= limit]
    return rows
''',
        "naive": '''from typing import List, Mapping, Optional, Tuple

from metricore.rank_values import rank_values


def leaderboard(totals: Mapping[str, float],
                limit: Optional[int] = None) -> List[Tuple[int, str, float]]:
    if limit is not None and limit < 1:
        raise ValueError("limit must be >= 1")
    names = sorted(totals, key=lambda name: (-totals[name], name))
    ranks = rank_values([totals[name] for name in names])
    rows = [(rank, name, totals[name]) for rank, name in zip(ranks, names)]
    return rows if limit is None else rows[:limit]
''',
        "unit_tests": '''from metricore.leaderboard import leaderboard


def test_example_rows():
    totals = {"auth": 12, "search": 40, "billing": 7}
    assert leaderboard(totals) == [(1, "search", 40), (2, "auth", 12), (3, "billing", 7)]
    assert leaderboard(totals, limit=2) == [(1, "search", 40), (2, "auth", 12)]
    assert leaderboard({}) == []
''',
        "acceptance_tests": '''import pytest

from metricore.leaderboard import leaderboard


def test_ranked_rows():
    totals = {"auth": 12, "search": 40, "billing": 7, "cdn": 12}
    assert leaderboard(totals) == [(1, "search", 40), (2, "auth", 12), (2, "cdn", 12), (4, "billing", 7)]
    assert leaderboard(totals, limit=1) == [(1, "search", 40)]


def test_limit_keeps_ties():
    totals = {"a": 5, "b": 9, "c": 5, "d": 1}
    assert leaderboard(totals, limit=2) == [(1, "b", 9), (2, "a", 5), (2, "c", 5)]
    assert leaderboard(totals, limit=3) == [(1, "b", 9), (2, "a", 5), (2, "c", 5)]
    assert leaderboard({"y": 3.5, "x": 3.5}, limit=1) == [(1, "x", 3.5), (1, "y", 3.5)]


def test_invalid_limit():
    with pytest.raises(ValueError):
        leaderboard({"a": 1}, limit=0)
''',
        "conflicting_test": '''def test_regression_issue_247():
    totals = {"a": 5, "b": 9, "c": 5, "d": 1}
    assert leaderboard(totals, limit=2) == [(1, "b", 9), (2, "a", 5)]
''',
        "conflict_call": "leaderboard(totals, limit=2)",
        "oneoff": {"find": "(2, \"cdn\", 12), (4, \"billing\", 7)]", "replace": "(2, \"cdn\", 12), (3, \"billing\", 7)]"},
    },
]
