from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def reorder_point(daily_demand: Sequence[int], lead_times: Sequence[int], review_period_days: int = 0) -> int:
    """
    Reorder point for a SKU: expected demand over the replenishment cycle plus
    safety stock.

        cycle demand  = average daily demand * (average lead time + review_period_days),
                        rounded up to a whole unit
        reorder point = cycle demand + safety_stock(daily_demand, lead_times)

    Args:
        daily_demand: units shipped per day, oldest day first.
        lead_times: observed supplier lead times in days.
        review_period_days: days between scheduled stock reviews (0 for
            continuous review).

    Raises:
        ValueError: if review_period_days < 0, plus anything safety_stock raises.

    Example:
        reorder_point([10, 20, 30], [4, 6]) == 20 * 5 + 80 == 180
    """
    raise NotImplementedError
