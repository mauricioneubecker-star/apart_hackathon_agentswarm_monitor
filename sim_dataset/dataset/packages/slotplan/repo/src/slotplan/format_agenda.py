from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def format_agenda(meetings: Iterable[Tuple[str, int, int]]) -> List[str]:
    """
    Render meetings given as (title, start, end) into agenda lines of the form

        "<start>-<end>  <title> (<duration>)"

    where start and end are formatted with format_hhmm, the duration (end - start)
    with format_duration, and two spaces separate the time range from the title.
    Lines are ordered by start time, then end time, then title.

    Raise ValueError if a meeting has end <= start.

    Example:
        format_agenda([("Design review", 600, 690), ("Standup", 540, 555)]) == [
            "09:00-09:15  Standup (15m)",
            "10:00-11:30  Design review (1h 30m)",
        ]
    """
    raise NotImplementedError
