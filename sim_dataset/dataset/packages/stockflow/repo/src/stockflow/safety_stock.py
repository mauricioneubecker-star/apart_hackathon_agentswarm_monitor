from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def safety_stock(daily_demand: Sequence[int], lead_times: Sequence[int]) -> int:
    """
    Safety stock in units, using the max-max method:

        safety stock = max daily demand * max lead time
                       - average daily demand * average lead time

    Args:
        daily_demand: units demanded per day over the history window.
        lead_times: observed supplier lead times in days.

    Returns:
        Safety stock as an int number of units (never negative).

    Raises:
        ValueError: if either sequence is empty or contains a negative value.

    Example:
        safety_stock([10, 20, 30], [4, 6]) == 30 * 6 - 20 * 5 == 80
    """
    raise NotImplementedError
