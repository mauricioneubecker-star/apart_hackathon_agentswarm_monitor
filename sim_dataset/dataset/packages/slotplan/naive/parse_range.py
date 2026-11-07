from typing import Tuple

from slotplan.parse_hhmm import parse_hhmm


def parse_range(text: str) -> Tuple[int, int]:
    parts = text.strip().split("-")
    if len(parts) != 2:
        raise ValueError(f"invalid range: {text!r}")
    start = parse_hhmm(parts[0])
    end = parse_hhmm(parts[1])
    if end <= start:
        raise ValueError(f"empty or reversed range: {text!r}")
    return start, end
