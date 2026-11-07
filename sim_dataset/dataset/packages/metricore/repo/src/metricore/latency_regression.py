from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def latency_regression(before_ms: Sequence[float], after_ms: Sequence[float], tolerance_pct: float = 10.0) -> Dict[str, Any]:
    """
    Compare two latency samples, e.g. the hour before and the hour after a deploy.

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
    """
    raise NotImplementedError
