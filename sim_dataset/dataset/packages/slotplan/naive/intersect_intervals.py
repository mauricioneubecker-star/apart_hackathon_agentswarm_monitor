from typing import Iterable, List, Tuple

from slotplan.merge_intervals import merge_intervals


def intersect_intervals(a: Iterable[Tuple[int, int]], b: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    left, right = merge_intervals(a), merge_intervals(b)
    out: List[Tuple[int, int]] = []
    for a_start, a_end in left:
        for b_start, b_end in right:
            lo, hi = max(a_start, b_start), min(a_end, b_end)
            if lo <= hi:
                out.append((lo, hi))
    return sorted(out)
