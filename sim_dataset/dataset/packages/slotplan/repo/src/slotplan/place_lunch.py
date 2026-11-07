from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def place_lunch(busy: Iterable[Tuple[int, int]], length: int = 30, window: Tuple[int, int] = (690, 840)) -> Optional[Tuple[int, int]]:
    """
    Choose a lunch break of `length` minutes for a person with the given busy
    intervals. The break must lie entirely inside `window` (default 11:30-14:00)
    and must not overlap any busy interval. Breaks start on the quarter hour
    (a multiple of 15 minutes). Use free_slots to find the free time inside the
    window and align_to_grid to place starts on the quarter hour.

    Return the chosen break as (start, start + length), or None if no break fits
    so that the caller can flag the day.

    Raise ValueError if length <= 0 or the window is empty.

    Example:
        place_lunch([(690, 780)]) == (780, 810)
    """
    raise NotImplementedError
