from typing import Iterable, List, Tuple


def merge_intervals(intervals: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    items = []
    for start, end in intervals:
        if start > end:
            raise ValueError(f"interval starts after it ends: {(start, end)}")
        if start < end:
            items.append((start, end))
    items.sort()
    merged: List[Tuple[int, int]] = []
    for start, end in items:
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
