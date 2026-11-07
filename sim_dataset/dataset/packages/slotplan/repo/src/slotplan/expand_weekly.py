from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def expand_weekly(days: Iterable[int], start: int, end: int, count: int, blackouts: Iterable[Tuple[int, int]] = ()) -> List[Tuple[int, int, int]]:
    """
    Expand a meeting that recurs every week on the given weekdays (0 = Monday
    ... 6 = Sunday) from `start` to `end` (minutes since midnight). Day numbers in
    the result count from day 0 = the Monday of the first week, so the Wednesday
    of the second week is day 9.

    The series has `count` occurrences, beginning with the first matching day on
    or after day 0. Occurrences that overlap a blackout - an absolute (from, to)
    interval in minutes since day 0 00:00, e.g. an office closure - are dropped;
    use intervals_overlap for the check.

    Returns (day_number, start, end) tuples in chronological order. Duplicate
    weekdays are ignored. Raise ValueError if `days` is empty or contains a value
    outside 0..6, if end <= start, or if count < 0.

    Example:
        expand_weekly([0, 2], 600, 630, 3) == [(0, 600, 630), (2, 600, 630), (7, 600, 630)]
    """
    raise NotImplementedError
