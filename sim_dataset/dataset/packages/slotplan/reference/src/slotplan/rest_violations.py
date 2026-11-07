from typing import List, Mapping, Sequence, Tuple

from slotplan.parse_shift import parse_shift

_WEEK = 7 * 1440


def rest_violations(rota: Mapping[str, Sequence[str]], min_rest: int = 660) -> List[Tuple[str, int, int]]:
    found: List[Tuple[str, int, int]] = []
    for worker, entries in rota.items():
        shifts = []
        for entry in entries:
            day, start, end = parse_shift(entry)
            shifts.append((day * 1440 + start, day * 1440 + end, day))
        shifts.sort()
        for index, (start, _end, day) in enumerate(shifts):
            previous_end = shifts[index - 1][1]
            if index == 0:
                previous_end -= _WEEK
            rest = start - previous_end
            if rest < min_rest:
                found.append((worker, day, rest))
    found.sort()
    return found
