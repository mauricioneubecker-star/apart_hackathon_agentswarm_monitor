from typing import Iterable, List, Tuple

from slotplan.subtract_intervals import subtract_intervals


def free_slots(busy: Iterable[Tuple[int, int]], day_start: int, day_end: int, min_length: int = 0, buffer: int = 0) -> List[Tuple[int, int]]:
    if day_end <= day_start:
        raise ValueError("empty working window")
    if min_length < 0 or buffer < 0:
        raise ValueError("min_length and buffer must not be negative")
    blocked = [(start - buffer, end + buffer) for start, end in busy]
    slots = subtract_intervals([(day_start, day_end)], blocked)
    return [(start, end) for start, end in slots if end - start >= min_length]
