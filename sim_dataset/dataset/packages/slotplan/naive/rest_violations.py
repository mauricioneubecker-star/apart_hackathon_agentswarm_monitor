from typing import List, Mapping, Sequence, Tuple

from slotplan.parse_shift import parse_shift


def rest_violations(rota: Mapping[str, Sequence[str]], min_rest: int = 660) -> List[Tuple[str, int, int]]:
    found: List[Tuple[str, int, int]] = []
    for worker, entries in rota.items():
        shifts = []
        for entry in entries:
            day, start, end = parse_shift(entry)
            shifts.append((day * 1440 + start, day * 1440 + end, day))
        shifts.sort()
        for previous, current in zip(shifts, shifts[1:]):
            rest = current[0] - previous[1]
            if rest < min_rest:
                found.append((worker, current[2], rest))
    found.sort()
    return found
