from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def intersect_intervals(a: Iterable[Tuple[int, int]], b: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Return the time covered by both `a` and `b` (for example the free time two
    people share) as a sorted list of disjoint (start, end) tuples.

    Each input is first normalised with merge_intervals, so unsorted or
    overlapping input is fine and the inputs are not modified.

    Example:
        intersect_intervals([(540, 720)], [(600, 660), (700, 800)]) == [(600, 660), (700, 720)]
    """
    raise NotImplementedError
