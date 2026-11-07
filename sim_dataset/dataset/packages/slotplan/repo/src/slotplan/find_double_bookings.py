from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def find_double_bookings(bookings: Sequence[Tuple[str, str, int, int]]) -> List[Tuple[str, str]]:
    """
    Each booking is (booking_id, room, start, end). Two bookings clash when they
    are for the same room and their times overlap according to intervals_overlap
    (back-to-back bookings are fine).

    Return every clashing pair once as (first_id, second_id), where first_id is
    the booking that appears earlier in `bookings`. Pairs are ordered by the
    position of their first booking, then by the position of their second.

    Example:
        find_double_bookings([("b1", "Atlas", 540, 600), ("b2", "Atlas", 570, 630),
                              ("b3", "Zephyr", 540, 600)]) == [("b1", "b2")]
    """
    raise NotImplementedError
