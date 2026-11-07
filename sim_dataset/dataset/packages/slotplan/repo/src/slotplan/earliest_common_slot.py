from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def earliest_common_slot(calendars: Sequence[Sequence[Tuple[int, int]]], duration: int, day_start: int, day_end: int, step: int = 15) -> Optional[int]:
    """
    Given one list of busy intervals per attendee, return the earliest start
    minute s such that every attendee is free during [s, s + duration) and the
    meeting lies inside the working window [day_start, day_end). Return None if
    there is no such start.

    Meetings may only start on the booking grid, which has a point every `step`
    minutes (default 15). Compute each attendee's free time with free_slots and
    combine them with intersect_intervals. With no calendars at all everybody is
    free for the whole window.

    Raise ValueError if duration <= 0, step <= 0 or day_end <= day_start.

    Example:
        earliest_common_slot([[(540, 600)], [(600, 630)]], 30, 540, 1020) == 630
    """
    raise NotImplementedError
