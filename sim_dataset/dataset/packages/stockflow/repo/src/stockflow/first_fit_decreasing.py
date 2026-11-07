from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def first_fit_decreasing(items: Sequence[Tuple[str, int]], capacity: int) -> List[List[Tuple[str, int]]]:
    """
    Pack weighted items into bins with the first-fit-decreasing heuristic.

    Items are taken heaviest first. Each item goes into the first bin (in the
    order the bins were opened) whose remaining capacity can hold it; if no bin
    can, a new bin is opened.

    Args:
        items: (item_id, weight) pairs; weights are non-negative ints.
        capacity: capacity of every bin, > 0.

    Returns:
        List of bins in the order they were opened; each bin is a list of the
        (item_id, weight) tuples in the order they were placed.

    Raises:
        ValueError: if capacity <= 0, a weight is negative, or a single item is
            heavier than capacity.

    Example:
        first_fit_decreasing([("a", 4), ("b", 7), ("c", 3)], 10)
            == [[("b", 7), ("c", 3)], [("a", 4)]]
    """
    raise NotImplementedError
