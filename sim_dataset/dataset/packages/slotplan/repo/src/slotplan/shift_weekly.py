from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def shift_weekly(entries: Iterable[Tuple[int, int, int]], offset: int) -> List[Tuple[int, int, int]]:
    """
    Shift recurring weekly entries (day, start, end) by `offset` minutes, e.g.
    to convert a schedule kept in local time to UTC (offset=-120 for a UTC+2
    office). `day` is a weekday index 0..6 (Monday..Sunday); start and end are
    minutes since midnight of that day with 0 <= start < 1440 and end > start
    (end may exceed 1440 for entries that run past midnight).

    The week wraps around: moving past the end of Sunday continues on Monday and
    moving before Monday 00:00 continues on Sunday. The result is sorted by
    (day, start, end).

    Raise ValueError for an entry whose day is outside 0..6 or whose start/end
    are invalid.

    Examples:
        shift_weekly([(0, 600, 660)], -120) == [(0, 480, 540)]
        shift_weekly([(0, 60, 120)], -120) == [(6, 1380, 1440)]
    """
    raise NotImplementedError
