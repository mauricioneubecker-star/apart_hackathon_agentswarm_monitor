from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def utilization(busy: Iterable[Tuple[int, int]], day_start: int, day_end: int) -> int:
    """
    Return the share of the working window [day_start, day_end) that is covered
    by `busy` intervals, as a whole-number percentage between 0 and 100.

    Overlapping busy intervals are counted once (normalise them with
    merge_intervals) and busy time outside the window is ignored. The percentage
    is rounded to the nearest integer.

    Raise ValueError if day_end <= day_start.

    Example:
        utilization([(540, 660)], 540, 1020) == 25
    """
    raise NotImplementedError
