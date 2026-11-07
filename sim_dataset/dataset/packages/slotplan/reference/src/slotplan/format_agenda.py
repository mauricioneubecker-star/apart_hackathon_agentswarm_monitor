from typing import Iterable, List, Tuple

from slotplan.format_duration import format_duration
from slotplan.format_hhmm import format_hhmm


def format_agenda(meetings: Iterable[Tuple[str, int, int]]) -> List[str]:
    items = []
    for title, start, end in meetings:
        if end <= start:
            raise ValueError(f"meeting {title!r} ends before it starts")
        items.append((start, end, title))
    items.sort()
    lines = []
    for start, end, title in items:
        end_text = format_hhmm(end) + ("+1" if end > 1440 else "")
        lines.append(f"{format_hhmm(start)}-{end_text}  {title} ({format_duration(end - start)})")
    return lines
