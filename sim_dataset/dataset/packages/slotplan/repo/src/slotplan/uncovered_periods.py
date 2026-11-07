from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def uncovered_periods(rota: Mapping[str, Sequence[str]], day: int, open_start: int, open_end: int) -> List[Tuple[int, int]]:
    """
    Return the periods within the opening hours [open_start, open_end) of weekday
    `day` (0 = Monday ... 6 = Sunday) during which no worker in `rota` is on
    shift. `rota` maps workers to weekly rota entries understood by parse_shift.
    The result is a sorted list of (start, end) tuples in minutes since midnight
    of `day`; compute it with subtract_intervals.

    Raise ValueError if day is not in 0..6, if open_end <= open_start, or if an
    entry cannot be parsed.

    Example:
        uncovered_periods({"kim": ["Mon 08:00-12:00"], "ann": ["Mon 13:00-18:00"]}, 0, 480, 1080)
            == [(720, 780)]
    """
    raise NotImplementedError
