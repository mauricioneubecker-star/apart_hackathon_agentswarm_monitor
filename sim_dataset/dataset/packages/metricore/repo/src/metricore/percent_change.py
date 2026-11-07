from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def percent_change(old: float, new: float) -> Optional[float]:
    """
    Return the relative change from `old` to `new` as a percentage, rounded to 2
    decimal places with metricore's round_half_up.

    Used in week-over-week report columns (error counts, p95 latency, cost, net
    capacity deltas). If `old` is 0 the change is undefined and None is returned.

    Examples:
        percent_change(200, 250) == 25.0
        percent_change(80, 60) == -25.0
    """
    raise NotImplementedError
