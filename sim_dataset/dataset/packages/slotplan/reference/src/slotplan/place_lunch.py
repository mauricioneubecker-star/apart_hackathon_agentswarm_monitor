from typing import Iterable, Optional, Tuple

from slotplan.align_to_grid import align_to_grid
from slotplan.free_slots import free_slots


def place_lunch(busy: Iterable[Tuple[int, int]], length: int = 30, window: Tuple[int, int] = (690, 840)) -> Optional[Tuple[int, int]]:
    window_start, window_end = window
    if length <= 0 or window_end <= window_start:
        raise ValueError("invalid length or window")
    candidates = []
    for start, end in free_slots(busy, window_start, window_end, min_length=length):
        first = align_to_grid(start, 15, "ceil")
        last = align_to_grid(end - length, 15, "floor")
        candidates.extend(range(first, last + 1, 15))
    if not candidates:
        return None
    best = min(candidates, key=lambda c: (abs(c - 720), c))
    return best, best + length
