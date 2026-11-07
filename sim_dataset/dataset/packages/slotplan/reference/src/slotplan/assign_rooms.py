from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from slotplan.intervals_overlap import intervals_overlap


def assign_rooms(meetings: Sequence[Tuple[str, int, int, int]], rooms: Mapping[str, int]) -> Dict[str, Optional[str]]:
    order = sorted(meetings, key=lambda m: (m[1], -m[3], m[0]))
    room_order = sorted(rooms, key=lambda name: (rooms[name], name))
    booked: Dict[str, List[Tuple[int, int]]] = {name: [] for name in rooms}
    result: Dict[str, Optional[str]] = {}
    for meeting_id, start, end, attendees in order:
        result[meeting_id] = None
        for name in room_order:
            if rooms[name] < attendees:
                continue
            if any(intervals_overlap((start, end), taken) for taken in booked[name]):
                continue
            booked[name].append((start, end))
            result[meeting_id] = name
            break
    return result
