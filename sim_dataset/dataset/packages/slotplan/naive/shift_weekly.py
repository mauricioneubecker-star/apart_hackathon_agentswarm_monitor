from typing import Iterable, List, Tuple


def shift_weekly(entries: Iterable[Tuple[int, int, int]], offset: int) -> List[Tuple[int, int, int]]:
    out: List[Tuple[int, int, int]] = []
    for day, start, end in entries:
        if not 0 <= day <= 6 or not 0 <= start < 1440 or end <= start:
            raise ValueError(f"invalid entry: {(day, start, end)}")
        moment = (day * 1440 + start + offset) % (7 * 1440)
        new_day, minute = divmod(moment, 1440)
        out.append((new_day, minute, minute + (end - start)))
    out.sort()
    return out
