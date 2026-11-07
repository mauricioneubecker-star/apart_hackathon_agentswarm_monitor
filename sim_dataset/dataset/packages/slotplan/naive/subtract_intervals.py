from typing import Iterable, List, Tuple

from slotplan.merge_intervals import merge_intervals


def subtract_intervals(base: Iterable[Tuple[int, int]], remove: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    holes = merge_intervals(remove)
    out: List[Tuple[int, int]] = []
    for start, end in sorted(base):
        cursor = start
        for hole_start, hole_end in holes:
            if hole_end <= cursor or hole_start >= end:
                continue
            if hole_start > cursor:
                out.append((cursor, hole_start))
            cursor = max(cursor, hole_end)
        if cursor < end:
            out.append((cursor, end))
    return out
