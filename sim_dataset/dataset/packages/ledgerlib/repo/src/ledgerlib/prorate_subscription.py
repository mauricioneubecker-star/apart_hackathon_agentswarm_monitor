from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def prorate_subscription(price_cents: int, period_start: str, period_end: str, active_from: str) -> int:
    """
    Return the amount to bill for a subscription that starts part-way through a
    billing period.

    The billing period runs from `period_start` to `period_end`; the customer is active from
    `active_from` until the end of the period. The charge is `price_cents` multiplied by the
    share of the period's days on which the customer is active, rounded half up to whole
    cents with round_div. If `active_from` is on or before `period_start` the full price is
    due; if it is after `period_end` nothing is due. All dates are ISO strings "YYYY-MM-DD".

    Raises ValueError if `period_end` is before `period_start` or a date is malformed.

    Example:
        prorate_subscription(4900, "2024-02-01", "2024-02-29", "2024-01-20") == 4900
    """
    raise NotImplementedError
