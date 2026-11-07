from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def percent_shares(counts: Mapping[str, int]) -> Dict[str, int]:
    """
    Convert per-category counts into integer percentages that add up to exactly 100.

    Used for the "share of errors by service" charts, where independently rounded
    percentages often add up to 99 or 101. Uses the largest remainder method:

    1. Compute each exact share: count * 100 / total.
    2. Give every category the integer part (floor) of its share.
    3. Hand out the remaining points (100 minus the sum of the floors) one at a
       time to the categories with the largest fractional remainders.

    - Counts must be non-negative integers, otherwise ValueError is raised.
    - Raises ValueError if `counts` is empty or all counts are zero.
    - The returned dict has exactly the keys of `counts`.

    Example:
        percent_shares({"api": 1, "web": 1, "db": 2}) == {"api": 25, "web": 25, "db": 50}
    """
    raise NotImplementedError
