from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def abc_classify(values: Mapping[str, int], a_pct: int = 80, b_pct: int = 95) -> Dict[str, str]:
    """
    ABC classification of SKUs by value share.

    SKUs are ranked by value, highest first (ties: SKU ascending), and the
    running total of value is tracked as a share of the grand total. The top
    SKUs making up the first `a_pct` percent of value are class "A", those up
    to `b_pct` percent are "B", the rest are "C".

    Args:
        values: SKU -> value in cents (e.g. annual consumption value).
        a_pct, b_pct: cumulative percentage thresholds, 0 < a_pct <= b_pct <= 100.

    Returns:
        Dict SKU -> "A" | "B" | "C" for every SKU in `values`. SKUs with value 0
        are always "C" (so is every SKU when the total is 0).

    Raises:
        ValueError: if a value is negative or the thresholds are invalid.

    Example:
        abc_classify({"S1": 80, "S2": 15, "S3": 5}) == {"S1": "A", "S2": "B", "S3": "C"}
    """
    raise NotImplementedError
