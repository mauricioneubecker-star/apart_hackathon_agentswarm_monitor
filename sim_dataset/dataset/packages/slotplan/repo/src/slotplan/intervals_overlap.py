from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def intervals_overlap(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    """
    Return True if the intervals a = (start, end) and b = (start, end) overlap
    in time, False otherwise. Times are minutes with start <= end. Back-to-back
    intervals such as (540, 600) and (600, 660) do not overlap. The check is
    symmetric: intervals_overlap(a, b) == intervals_overlap(b, a).

    Raise ValueError if either interval has start > end.

    Example:
        intervals_overlap((540, 600), (570, 630)) is True
    """
    raise NotImplementedError
