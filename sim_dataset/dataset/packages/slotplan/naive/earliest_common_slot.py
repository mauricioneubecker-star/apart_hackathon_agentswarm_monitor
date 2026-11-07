from typing import Optional, Sequence, Tuple

from slotplan.free_slots import free_slots
from slotplan.intersect_intervals import intersect_intervals


def earliest_common_slot(calendars: Sequence[Sequence[Tuple[int, int]]], duration: int, day_start: int, day_end: int, step: int = 15) -> Optional[int]:
    if duration <= 0 or step <= 0:
        raise ValueError("duration and step must be positive")
    if day_end <= day_start:
        raise ValueError("empty working window")
    common = [(day_start, day_end)]
    for busy in calendars:
        common = intersect_intervals(common, free_slots(busy, day_start, day_end))
    for start, end in common:
        steps_in = -(-(start - day_start) // step)
        candidate = day_start + steps_in * step
        if candidate + duration <= end:
            return candidate
    return None
