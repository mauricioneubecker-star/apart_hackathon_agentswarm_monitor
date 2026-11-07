from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def percentile_by_group(records: Iterable[Mapping[str, Any]], key: str, field: str, p: float) -> Dict[Any, float]:
    """
    Group records by `key` and return the p-th percentile of `field` for each group.

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
    """
    raise NotImplementedError
