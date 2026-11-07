from typing import List, Mapping, Sequence, Tuple

from slotplan.parse_shift import parse_shift
from slotplan.subtract_intervals import subtract_intervals


def uncovered_periods(rota: Mapping[str, Sequence[str]], day: int, open_start: int, open_end: int) -> List[Tuple[int, int]]:
    if not 0 <= day <= 6:
        raise ValueError("day must be a weekday index 0..6")
    if open_end <= open_start:
        raise ValueError("empty opening hours")
    previous_day = (day - 1) % 7
    covered = []
    for entries in rota.values():
        for entry in entries:
            shift_day, start, end = parse_shift(entry)
            if shift_day == day:
                covered.append((start, end))
            if shift_day == previous_day and end > 1440:
                covered.append((start - 1440, end - 1440))
    return subtract_intervals([(open_start, open_end)], covered)
