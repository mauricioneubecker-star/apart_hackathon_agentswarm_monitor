from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def cycle_count_variance(lines: Iterable[str], case_sizes: Mapping[str, int], counts: Mapping[Tuple[str, str], int]) -> List[Tuple[str, str, int]]:
    """
    Compare a cycle count with system stock and report the differences.

    System stock is on_hand_by_location(lines, case_sizes). `counts` holds what
    the counters recorded, keyed by (sku, location) as typed on the handheld;
    keys are normalized with normalize_sku and parse_location (canonical
    "Z-AA-SS-L" location string) before matching, and the quantities of keys
    that normalize to the same position are added together.

        variance = counted qty - system qty

    Returns:
        List of (sku, location, variance) for every position with a non-zero
        variance, sorted by location, then SKU.

    Raises:
        ValueError: if a counted quantity is negative, or from the parsers.

    Example:
        lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA"]
        cycle_count_variance(lines, {}, {("abc-123456-1", "b-07-14-3"): 8})
            == [("ABC-123456-1", "B-07-14-3", -2)]
    """
    raise NotImplementedError
