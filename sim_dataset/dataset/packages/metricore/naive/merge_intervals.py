from typing import Iterable, List, Tuple


def merge_intervals(intervals: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    items = [(start, end) for start, end in intervals]
    for start, end in items:
        if start > end:
            raise ValueError(f"interval ({start}, {end}) ends before it starts")
    merged: List[Tuple[int, int]] = []
    for start, end in sorted(items):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
