from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def assign_rooms(meetings: Sequence[Tuple[str, int, int, int]], rooms: Mapping[str, int]) -> Dict[str, Optional[str]]:
    """
    Assign each meeting (meeting_id, start, end, attendees) to a room from
    `rooms` (room name -> capacity).

    Meetings are handled in order of start time. Each meeting gets the smallest
    room whose capacity is at least `attendees` and that has no already-assigned
    meeting overlapping it (checked with intervals_overlap); among rooms of equal
    capacity the alphabetically first name wins. A meeting that cannot be placed
    maps to None and blocks nothing.

    Returns a dict meeting_id -> room name (or None).

    Example:
        assign_rooms([("standup", 540, 555, 6), ("review", 540, 600, 3)],
                     {"Atlas": 8, "Nook": 4}) == {"standup": "Atlas", "review": "Nook"}
    """
    raise NotImplementedError
