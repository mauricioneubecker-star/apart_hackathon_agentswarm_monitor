from typing import Sequence, Tuple

from metricore.merge_intervals import merge_intervals
from metricore.round_half_up import round_half_up


def uptime_percent(incidents: Sequence[Tuple[int, int]], window_start: int, window_end: int) -> float:
    if window_end <= window_start:
        raise ValueError("window_end must be after window_start")
    downtime = 0
    for start, end in merge_intervals(incidents):
        lo, hi = max(start, window_start), min(end, window_end)
        if hi > lo:
            downtime += hi - lo
    length = window_end - window_start
    return round_half_up(100 * (length - downtime) / length, 3)
