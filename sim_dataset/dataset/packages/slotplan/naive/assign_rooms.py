from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from slotplan.intervals_overlap import intervals_overlap


def assign_rooms(meetings: Sequence[Tuple[str, int, int, int]], rooms: Mapping[str, int]) -> Dict[str, Optional[str]]:
    room_order = sorted(rooms, key=lambda name: (rooms[name], name))
    booked: Dict[str, List[Tuple[int, int]]] = {name: [] for name in rooms}
    result: Dict[str, Optional[str]] = {}
    for meeting_id, start, end, attendees in sorted(meetings, key=lambda m: m[1]):
        chosen = None
        for name in room_order:
            if rooms[name] >= attendees and not any(intervals_overlap((start, end), t) for t in booked[name]):
                chosen = name
                booked[name].append((start, end))
                break
        result[meeting_id] = chosen
    return result
