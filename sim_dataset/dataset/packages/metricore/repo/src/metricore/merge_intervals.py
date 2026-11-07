from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def merge_intervals(intervals: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Merge overlapping (start, end) intervals and return them sorted by start.

    Intervals are incident windows in epoch seconds with start <= end. The input
    may be in any order and may contain duplicates; it is not modified. The result
    is a new list of (start, end) tuples in which no two intervals overlap,
    sorted by start.

    - An empty input returns [].
    - Raises ValueError if any interval has start > end.

    Example:
        merge_intervals([(10, 20), (0, 5), (15, 30)]) == [(0, 5), (10, 30)]
    """
    raise NotImplementedError
