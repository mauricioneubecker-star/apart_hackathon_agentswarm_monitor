from typing import Iterable, Tuple

from slotplan.merge_intervals import merge_intervals


def utilization(busy: Iterable[Tuple[int, int]], day_start: int, day_end: int) -> int:
    if day_end <= day_start:
        raise ValueError("empty working window")
    covered = 0
    for start, end in merge_intervals(busy):
        lo, hi = max(start, day_start), min(end, day_end)
        if lo < hi:
            covered += hi - lo
    return round(covered * 100 / (day_end - day_start))
