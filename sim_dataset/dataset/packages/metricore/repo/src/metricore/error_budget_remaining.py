from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def error_budget_remaining(slo_target: float, total_requests: int, failed_requests: int) -> float:
    """
    Return the share of the error budget that is still unspent, as a percentage.

    For an availability SLO such as 0.999 the error budget is the number of
    requests that are allowed to fail: (1 - slo_target) * total_requests. The
    result is (budget - failed_requests) / budget * 100, rounded to 1 decimal
    place with metricore's round_half_up. 100.0 means none of the budget has been
    used yet.

    - slo_target must satisfy 0 < slo_target < 1, otherwise ValueError.
    - total_requests and failed_requests must be >= 0 and failed_requests must not
      exceed total_requests, otherwise ValueError.
    - With total_requests == 0 nothing has been spent: return 100.0.

    Example:
        error_budget_remaining(0.99, 10_000, 25) == 75.0
    """
    raise NotImplementedError
