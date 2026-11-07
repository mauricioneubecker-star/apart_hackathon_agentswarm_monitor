from typing import Iterable, List, Tuple

from slotplan.intervals_overlap import intervals_overlap


def expand_weekly(days: Iterable[int], start: int, end: int, count: int, blackouts: Iterable[Tuple[int, int]] = ()) -> List[Tuple[int, int, int]]:
    weekdays = sorted(set(days))
    if not weekdays or weekdays[0] < 0 or weekdays[-1] > 6:
        raise ValueError("days must be weekday indices 0..6")
    if end <= start or count < 0:
        raise ValueError("invalid time range or count")
    closed = list(blackouts)
    out: List[Tuple[int, int, int]] = []
    produced = 0
    week = 0
    while produced < count:
        for weekday in weekdays:
            if produced == count:
                break
            produced += 1
            day = week * 7 + weekday
            span = (day * 1440 + start, day * 1440 + end)
            if any(intervals_overlap(span, blackout) for blackout in closed):
                continue
            out.append((day, start, end))
        week += 1
    return out
