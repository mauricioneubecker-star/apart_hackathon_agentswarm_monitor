from typing import Dict, Mapping, Sequence

from slotplan.format_duration import format_duration
from slotplan.parse_shift import parse_shift


def paid_hours(rota: Mapping[str, Sequence[str]]) -> Dict[str, str]:
    totals: Dict[str, str] = {}
    for worker, entries in rota.items():
        minutes = 0
        for entry in entries:
            _day, start, end = parse_shift(entry)
            minutes += end - start
        totals[worker] = format_duration(minutes)
    return totals
