from typing import Tuple

from slotplan.parse_range import parse_range

_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def parse_shift(text: str) -> Tuple[int, int, int]:
    parts = text.split()
    if len(parts) < 2:
        raise ValueError(f"invalid rota entry: {text!r}")
    if parts[0] not in _DAYS:
        raise ValueError(f"unknown day: {parts[0]!r}")
    start, end = parse_range(" ".join(parts[1:]))
    return _DAYS.index(parts[0]), start, end
