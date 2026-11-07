from typing import Iterable, Optional, Tuple

from slotplan.align_to_grid import align_to_grid
from slotplan.free_slots import free_slots


def place_lunch(busy: Iterable[Tuple[int, int]], length: int = 30, window: Tuple[int, int] = (690, 840)) -> Optional[Tuple[int, int]]:
    window_start, window_end = window
    if length <= 0 or window_end <= window_start:
        raise ValueError("invalid length or window")
    for start, end in free_slots(busy, window_start, window_end, min_length=length):
        candidate = align_to_grid(start, 15, "ceil")
        if candidate + length <= end:
            return candidate, candidate + length
    return None
