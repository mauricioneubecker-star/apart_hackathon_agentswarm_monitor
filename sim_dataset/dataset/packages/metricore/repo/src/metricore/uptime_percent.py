from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def uptime_percent(incidents: Sequence[Tuple[int, int]], window_start: int, window_end: int) -> float:
    """
    Return the availability of a service over a reporting window, in percent.

    `incidents` are (start, end) outage intervals in epoch seconds, as exported
    from the incident tracker; the reporting window is [window_start, window_end].
    Overlapping incidents (for example two alerts for the same outage) must not be
    counted twice, so combine them with metricore's merge_intervals first. The
    result is

        100 * (window length - downtime) / window length

    rounded to 3 decimal places with metricore's round_half_up.

    - Raises ValueError if window_end <= window_start.
    - No incidents means 100.0.

    Example:
        uptime_percent([(0, 36), (18, 72)], 0, 3600) == 98.0
    """
    raise NotImplementedError
