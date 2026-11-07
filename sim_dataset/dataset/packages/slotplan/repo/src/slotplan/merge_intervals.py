from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def merge_intervals(intervals: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Combine (start, end) intervals into a sorted list of disjoint (start, end)
    tuples covering exactly the same minutes. The input may be in any order and
    may contain duplicates or overlapping entries; it is not modified.

    Empty intervals (start == end) cover no time and are dropped. Raise ValueError
    if any interval has start > end.

    Example:
        merge_intervals([(600, 660), (540, 610), (720, 750)]) == [(540, 660), (720, 750)]
    """
    raise NotImplementedError
