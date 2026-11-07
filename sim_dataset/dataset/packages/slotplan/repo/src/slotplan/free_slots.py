from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def free_slots(busy: Iterable[Tuple[int, int]], day_start: int, day_end: int, min_length: int = 0, buffer: int = 0) -> List[Tuple[int, int]]:
    """
    Return the free (start, end) slots inside the working window
    [day_start, day_end) for a person with the given `busy` intervals (any order,
    possibly overlapping, possibly extending outside the window). Slots are sorted
    by start time; slots shorter than `min_length` minutes are left out. Use
    subtract_intervals for the interval arithmetic.

    `buffer` is the number of minutes of slack to keep next to busy intervals (to
    wrap up or walk to another room). It is never applied at the edges of the
    working window itself.

    Raise ValueError if day_end <= day_start or if min_length or buffer is
    negative.

    Example:
        free_slots([(600, 660), (780, 840)], 540, 1020) == [(540, 600), (660, 780), (840, 1020)]
    """
    raise NotImplementedError
