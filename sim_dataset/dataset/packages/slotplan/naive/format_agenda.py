from typing import Iterable, List, Tuple

from slotplan.format_duration import format_duration
from slotplan.format_hhmm import format_hhmm


def format_agenda(meetings: Iterable[Tuple[str, int, int]]) -> List[str]:
    items = []
    for title, start, end in meetings:
        if end <= start:
            raise ValueError(f"meeting {title!r} ends before it starts")
        items.append((start, end, title))
    return [
        f"{format_hhmm(start)}-{format_hhmm(end)}  {title} ({format_duration(end - start)})"
        for start, end, title in sorted(items)
    ]
