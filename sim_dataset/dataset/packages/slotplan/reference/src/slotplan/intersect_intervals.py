from typing import Iterable, List, Tuple

from slotplan.merge_intervals import merge_intervals


def intersect_intervals(a: Iterable[Tuple[int, int]], b: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    left, right = merge_intervals(a), merge_intervals(b)
    out: List[Tuple[int, int]] = []
    i = j = 0
    while i < len(left) and j < len(right):
        lo = max(left[i][0], right[j][0])
        hi = min(left[i][1], right[j][1])
        if lo < hi:
            out.append((lo, hi))
        if left[i][1] < right[j][1]:
            i += 1
        else:
            j += 1
    return out
