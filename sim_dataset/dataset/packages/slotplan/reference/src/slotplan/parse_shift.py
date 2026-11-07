from typing import Tuple

from slotplan.parse_range import parse_range

_DAY_NAMES = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def parse_shift(text: str) -> Tuple[int, int, int]:
    parts = text.strip().split(None, 1)
    if len(parts) != 2:
        raise ValueError(f"invalid rota entry: {text!r}")
    name = parts[0].lower()
    for index, full in enumerate(_DAY_NAMES):
        if name == full or name == full[:3]:
            start, end = parse_range(parts[1])
            return index, start, end
    raise ValueError(f"unknown day: {parts[0]!r}")
