from typing import Sequence, Tuple

from metricore.merge_intervals import merge_intervals
from metricore.round_half_up import round_half_up


def uptime_percent(incidents: Sequence[Tuple[int, int]], window_start: int, window_end: int) -> float:
    if window_end <= window_start:
        raise ValueError("window_end must be after window_start")
    length = window_end - window_start
    downtime = sum(end - start for start, end in merge_intervals(incidents))
    return round_half_up(100 * (length - downtime) / length, 3)
