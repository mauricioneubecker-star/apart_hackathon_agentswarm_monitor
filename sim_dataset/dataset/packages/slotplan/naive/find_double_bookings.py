from typing import List, Sequence, Tuple

from slotplan.intervals_overlap import intervals_overlap


def find_double_bookings(bookings: Sequence[Tuple[str, str, int, int]]) -> List[Tuple[str, str]]:
    clashes: List[Tuple[str, str]] = []
    for i in range(len(bookings)):
        for j in range(i + 1, len(bookings)):
            a_id, a_room, a_start, a_end = bookings[i]
            b_id, b_room, b_start, b_end = bookings[j]
            if a_room == b_room and intervals_overlap((a_start, a_end), (b_start, b_end)):
                clashes.append((a_id, b_id))
    return clashes
