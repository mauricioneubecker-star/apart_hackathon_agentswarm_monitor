from typing import List, Sequence, Tuple

from slotplan.intervals_overlap import intervals_overlap


def find_double_bookings(bookings: Sequence[Tuple[str, str, int, int]]) -> List[Tuple[str, str]]:
    items = [(booking_id, room.strip().casefold(), (start, end)) for booking_id, room, start, end in bookings]
    clashes: List[Tuple[str, str]] = []
    for i, (first_id, first_room, first_span) in enumerate(items):
        for second_id, second_room, second_span in items[i + 1:]:
            if first_room == second_room and intervals_overlap(first_span, second_span):
                clashes.append((first_id, second_id))
    return clashes
