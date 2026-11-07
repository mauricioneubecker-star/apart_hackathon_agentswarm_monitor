from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def latency_summary(latencies_ms: Sequence[float]) -> Dict[str, Optional[float]]:
    """
    Summarise a window of request latencies for the service dashboard.

    Returns a dict with exactly the keys "count", "min", "mean", "p50", "p95",
    "p99" and "max". "count" is an int; every other value is a float rounded to
    1 decimal place with metricore's round_half_up. Percentiles are computed with
    metricore's percentile() on the unrounded data.

    Example:
        latency_summary([10, 20, 30, 40])["mean"] == 25.0
    """
    raise NotImplementedError
