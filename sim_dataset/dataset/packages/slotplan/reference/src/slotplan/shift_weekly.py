from typing import Iterable, List, Tuple

_DAY = 1440
_WEEK = 7 * _DAY


def shift_weekly(entries: Iterable[Tuple[int, int, int]], offset: int) -> List[Tuple[int, int, int]]:
    out: List[Tuple[int, int, int]] = []
    for day, start, end in entries:
        if not 0 <= day <= 6 or not 0 <= start < _DAY or end <= start:
            raise ValueError(f"invalid entry: {(day, start, end)}")
        moment = (day * _DAY + start + offset) % _WEEK
        remaining = end - start
        while remaining > 0:
            new_day, minute = divmod(moment, _DAY)
            piece = min(remaining, _DAY - minute)
            out.append((new_day, minute, minute + piece))
            remaining -= piece
            moment = (moment + piece) % _WEEK
    out.sort()
    return out
