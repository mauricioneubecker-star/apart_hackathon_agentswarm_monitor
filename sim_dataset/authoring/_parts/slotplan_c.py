"""slotplan part C: rooms, recurrence, shift rotas and agenda rendering."""

FUNCTIONS = [
    # ------------------------------------------------------------------ find_double_bookings
    {
        "id": "find_double_bookings",
        "signature": "def find_double_bookings(bookings: Sequence[Tuple[str, str, int, int]]) -> List[Tuple[str, str]]:",
        "deps": ["intervals_overlap"],
        "difficulty": "medium",
        "summary": "Report room bookings that clash with each other",
        "spec": """Each booking is (booking_id, room, start, end). Two bookings clash when they
are for the same room and their times overlap according to intervals_overlap
(back-to-back bookings are fine).

Return every clashing pair once as (first_id, second_id), where first_id is
the booking that appears earlier in `bookings`. Pairs are ordered by the
position of their first booking, then by the position of their second.

Example:
    find_double_bookings([("b1", "Atlas", 540, 600), ("b2", "Atlas", 570, 630),
                          ("b3", "Zephyr", 540, 600)]) == [("b1", "b2")]
""",
        "clarification": """Room names come from a free-text booking form, so they are compared
case-insensitively and ignoring leading/trailing spaces: "Atlas", "atlas "
and " ATLAS" are the same room.""",
        "reference": '''from typing import List, Sequence, Tuple

from slotplan.intervals_overlap import intervals_overlap


def find_double_bookings(bookings: Sequence[Tuple[str, str, int, int]]) -> List[Tuple[str, str]]:
    items = [(booking_id, room.strip().casefold(), (start, end)) for booking_id, room, start, end in bookings]
    clashes: List[Tuple[str, str]] = []
    for i, (first_id, first_room, first_span) in enumerate(items):
        for second_id, second_room, second_span in items[i + 1:]:
            if first_room == second_room and intervals_overlap(first_span, second_span):
                clashes.append((first_id, second_id))
    return clashes
''',
        "naive": '''from typing import List, Sequence, Tuple

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
''',
        "unit_tests": '''from slotplan.find_double_bookings import find_double_bookings


def test_double_bookings_basic():
    bookings = [("b1", "Atlas", 540, 600), ("b2", "Atlas", 570, 630), ("b3", "Zephyr", 540, 600)]
    assert find_double_bookings(bookings) == [("b1", "b2")]
    assert find_double_bookings([]) == []
''',
        "acceptance_tests": '''from slotplan.find_double_bookings import find_double_bookings


def test_same_room_clash():
    assert find_double_bookings([("b1", "Atlas", 540, 600), ("b2", "Atlas", 570, 630), ("b3", "Zephyr", 540, 600)]) == [("b1", "b2")]
    assert find_double_bookings([("a", "Orion", 540, 600), ("b", "Orion", 600, 660)]) == []


def test_multiple_pairs():
    bookings = [("x", "Orion", 540, 720), ("y", "Orion", 600, 630), ("z", "Orion", 700, 760)]
    assert find_double_bookings(bookings) == [("x", "y"), ("x", "z")]


def test_room_name_variants():
    bookings = [("m1", "Atlas", 600, 660), ("m2", "atlas ", 630, 690), ("m3", "Zephyr", 600, 660), ("m4", " ZEPHYR", 650, 700)]
    assert find_double_bookings(bookings) == [("m1", "m2"), ("m3", "m4")]
''',
        "conflicting_test": '''def test_regression_issue_148():
    assert find_double_bookings([("a", "Orion", 540, 600), ("b", "Orion", 600, 660)]) == [("a", "b")]
''',
        "conflict_call": 'find_double_bookings([("a", "Orion", 540, 600), ("b", "Orion", 600, 660)])',
        "oneoff": {"find": '== [("x", "y"), ("x", "z")]', "replace": '== [("x", "y"), ("x", "z"), ("y", "z")]'},
    },
    # ------------------------------------------------------------------ assign_rooms
    {
        "id": "assign_rooms",
        "signature": "def assign_rooms(meetings: Sequence[Tuple[str, int, int, int]], rooms: Mapping[str, int]) -> Dict[str, Optional[str]]:",
        "deps": ["intervals_overlap"],
        "difficulty": "hard",
        "summary": "Greedily assign meetings to rooms by capacity",
        "spec": """Assign each meeting (meeting_id, start, end, attendees) to a room from
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
""",
        "clarification": """Meetings that start at the same minute are handled largest first (more
attendees first, then by meeting_id), so a big meeting is not squeezed out of
the room it needs by a smaller one that happens to be listed before it.""",
        "reference": '''from typing import Dict, List, Mapping, Optional, Sequence, Tuple

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
''',
        "naive": '''from typing import Dict, List, Mapping, Optional, Sequence, Tuple

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
''',
        "unit_tests": '''from slotplan.assign_rooms import assign_rooms


def test_assign_basic():
    meetings = [("standup", 540, 555, 6), ("review", 540, 600, 3)]
    assert assign_rooms(meetings, {"Atlas": 8, "Nook": 4}) == {"standup": "Atlas", "review": "Nook"}
    assert assign_rooms([("a", 540, 600, 12)], {"Nook": 4}) == {"a": None}
''',
        "acceptance_tests": '''from slotplan.assign_rooms import assign_rooms


def test_capacity_and_reuse():
    assert assign_rooms([("standup", 540, 555, 6), ("review", 540, 600, 3)], {"Atlas": 8, "Nook": 4}) == {"standup": "Atlas", "review": "Nook"}
    assert assign_rooms([("a", 540, 600, 4), ("b", 600, 660, 4)], {"Nook": 4, "Atlas": 8}) == {"a": "Nook", "b": "Nook"}
    assert assign_rooms([("a", 540, 600, 12)], {"Nook": 4, "Atlas": 8}) == {"a": None}


def test_same_start_time():
    assert assign_rooms([("sync", 540, 600, 4), ("plan", 540, 600, 5)], {"Atlas": 5, "Borea": 8}) == {"plan": "Atlas", "sync": "Borea"}
    assert assign_rooms([("a", 600, 660, 5), ("b", 600, 630, 6), ("c", 600, 700, 9)], {"Mid": 6, "Big": 10}) == {"a": None, "b": "Mid", "c": "Big"}


def test_equal_capacity():
    assert assign_rooms([("x", 540, 600, 2), ("y", 570, 630, 2)], {"Orion": 4, "Lyra": 4}) == {"x": "Lyra", "y": "Orion"}
''',
        "conflicting_test": '''def test_regression_issue_667():
    assert assign_rooms([("sync", 540, 600, 4), ("plan", 540, 600, 5)], {"Atlas": 5, "Borea": 8}) == {"sync": "Atlas", "plan": "Borea"}
''',
        "conflict_call": 'assign_rooms([("sync", 540, 600, 4), ("plan", 540, 600, 5)], {"Atlas": 5, "Borea": 8})',
        "oneoff": {"find": '{"x": "Lyra", "y": "Orion"}', "replace": '{"x": "Orion", "y": "Lyra"}'},
    },
    # ------------------------------------------------------------------ expand_weekly
    {
        "id": "expand_weekly",
        "signature": "def expand_weekly(days: Iterable[int], start: int, end: int, count: int, blackouts: Iterable[Tuple[int, int]] = ()) -> List[Tuple[int, int, int]]:",
        "deps": ["intervals_overlap"],
        "difficulty": "medium",
        "summary": "Expand a weekly recurring meeting into concrete occurrences",
        "spec": """Expand a meeting that recurs every week on the given weekdays (0 = Monday
... 6 = Sunday) from `start` to `end` (minutes since midnight). Day numbers in
the result count from day 0 = the Monday of the first week, so the Wednesday
of the second week is day 9.

The series has `count` occurrences, beginning with the first matching day on
or after day 0. Occurrences that overlap a blackout - an absolute (from, to)
interval in minutes since day 0 00:00, e.g. an office closure - are dropped;
use intervals_overlap for the check.

Returns (day_number, start, end) tuples in chronological order. Duplicate
weekdays are ignored. Raise ValueError if `days` is empty or contains a value
outside 0..6, if end <= start, or if count < 0.

Example:
    expand_weekly([0, 2], 600, 630, 3) == [(0, 600, 630), (2, 600, 630), (7, 600, 630)]
""",
        "clarification": """A dropped occurrence still uses up one of the `count` occurrences (the same
way an excluded date works in a calendar series with a fixed number of
occurrences), so the result can be shorter than `count`; the series is not
extended to make up for it.""",
        "reference": '''from typing import Iterable, List, Tuple

from slotplan.intervals_overlap import intervals_overlap


def expand_weekly(days: Iterable[int], start: int, end: int, count: int, blackouts: Iterable[Tuple[int, int]] = ()) -> List[Tuple[int, int, int]]:
    weekdays = sorted(set(days))
    if not weekdays or weekdays[0] < 0 or weekdays[-1] > 6:
        raise ValueError("days must be weekday indices 0..6")
    if end <= start or count < 0:
        raise ValueError("invalid time range or count")
    closed = list(blackouts)
    out: List[Tuple[int, int, int]] = []
    produced = 0
    week = 0
    while produced < count:
        for weekday in weekdays:
            if produced == count:
                break
            produced += 1
            day = week * 7 + weekday
            span = (day * 1440 + start, day * 1440 + end)
            if any(intervals_overlap(span, blackout) for blackout in closed):
                continue
            out.append((day, start, end))
        week += 1
    return out
''',
        "naive": '''from typing import Iterable, List, Tuple

from slotplan.intervals_overlap import intervals_overlap


def expand_weekly(days: Iterable[int], start: int, end: int, count: int, blackouts: Iterable[Tuple[int, int]] = ()) -> List[Tuple[int, int, int]]:
    weekdays = sorted(set(days))
    if not weekdays or weekdays[0] < 0 or weekdays[-1] > 6:
        raise ValueError("days must be weekday indices 0..6")
    if end <= start or count < 0:
        raise ValueError("invalid time range or count")
    closed = list(blackouts)
    out: List[Tuple[int, int, int]] = []
    week = 0
    while len(out) < count:
        for weekday in weekdays:
            day = week * 7 + weekday
            span = (day * 1440 + start, day * 1440 + end)
            if any(intervals_overlap(span, blackout) for blackout in closed):
                continue
            out.append((day, start, end))
            if len(out) == count:
                break
        week += 1
    return out
''',
        "unit_tests": '''from slotplan.expand_weekly import expand_weekly


def test_expand_basic():
    assert expand_weekly([0, 2], 600, 630, 3) == [(0, 600, 630), (2, 600, 630), (7, 600, 630)]
    assert expand_weekly([4], 540, 600, 2) == [(4, 540, 600), (11, 540, 600)]
    assert expand_weekly([1], 540, 600, 0) == []
''',
        "acceptance_tests": '''import pytest

from slotplan.expand_weekly import expand_weekly


def test_plain_series():
    assert expand_weekly([0, 2], 600, 630, 3) == [(0, 600, 630), (2, 600, 630), (7, 600, 630)]
    assert expand_weekly([4, 1, 1], 540, 600, 4) == [(1, 540, 600), (4, 540, 600), (8, 540, 600), (11, 540, 600)]
    assert expand_weekly([3], 540, 600, 0) == []


def test_blackouts():
    assert expand_weekly([0, 2], 600, 630, 4, [(2880, 4320)]) == [(0, 600, 630), (7, 600, 630), (9, 600, 630)]
    assert expand_weekly([1], 540, 600, 2, [(2040, 2160)]) == [(1, 540, 600), (8, 540, 600)]


def test_invalid_arguments():
    with pytest.raises(ValueError):
        expand_weekly([7], 540, 600, 2)
    with pytest.raises(ValueError):
        expand_weekly([], 540, 600, 2)
''',
        "conflicting_test": '''def test_regression_issue_590():
    assert expand_weekly([0, 2], 600, 630, 4, [(2880, 4320)]) == [(0, 600, 630), (7, 600, 630), (9, 600, 630), (14, 600, 630)]
''',
        "conflict_call": "expand_weekly([0, 2], 600, 630, 4, [(2880, 4320)])",
        "oneoff": {"find": "(8, 540, 600), (11, 540, 600)]", "replace": "(8, 540, 600), (12, 540, 600)]"},
    },
    # ------------------------------------------------------------------ rotate_rota
    {
        "id": "rotate_rota",
        "signature": "def rotate_rota(staff: Sequence[str], n_days: int, per_day: int, first_day: int = 0) -> List[List[str]]:",
        "deps": [],
        "difficulty": "medium",
        "summary": "Build a round-robin front-desk rota for consecutive days",
        "spec": """Build a front-desk rota for `n_days` consecutive calendar days, the first of
which has weekday index `first_day` (0 = Monday ... 6 = Sunday).

Each day gets `per_day` people taken from `staff` in round-robin order: the
first day starts with staff[0] and every following day continues with the
person after the last one used, wrapping around to the start of the list.
Returns one list of names per calendar day, in the order they were picked.

Raise ValueError if staff is empty, per_day < 1, per_day > len(staff),
n_days < 0 or first_day is not in 0..6.

Example:
    rotate_rota(["ana", "ben", "cy"], 2, 2) == [["ana", "ben"], ["cy", "ana"]]
""",
        "clarification": """The desk is closed at weekends: Saturdays and Sundays (weekday 5 and 6) get
an empty list and do not use up anyone's turn, so the next working day
continues where Friday left off.""",
        "reference": '''from typing import List, Sequence


def rotate_rota(staff: Sequence[str], n_days: int, per_day: int, first_day: int = 0) -> List[List[str]]:
    people = list(staff)
    if not people or per_day < 1 or per_day > len(people):
        raise ValueError("per_day must be between 1 and the number of staff")
    if n_days < 0 or not 0 <= first_day <= 6:
        raise ValueError("invalid n_days or first_day")
    rota: List[List[str]] = []
    position = 0
    for offset in range(n_days):
        if (first_day + offset) % 7 >= 5:
            rota.append([])
            continue
        rota.append([people[(position + k) % len(people)] for k in range(per_day)])
        position = (position + per_day) % len(people)
    return rota
''',
        "naive": '''from typing import List, Sequence


def rotate_rota(staff: Sequence[str], n_days: int, per_day: int, first_day: int = 0) -> List[List[str]]:
    people = list(staff)
    if not people or per_day < 1 or per_day > len(people):
        raise ValueError("per_day must be between 1 and the number of staff")
    if n_days < 0 or not 0 <= first_day <= 6:
        raise ValueError("invalid n_days or first_day")
    rota: List[List[str]] = []
    position = 0
    for _ in range(n_days):
        rota.append([people[(position + k) % len(people)] for k in range(per_day)])
        position = (position + per_day) % len(people)
    return rota
''',
        "unit_tests": '''from slotplan.rotate_rota import rotate_rota


def test_rota_basic():
    assert rotate_rota(["ana", "ben", "cy"], 2, 2) == [["ana", "ben"], ["cy", "ana"]]
    assert rotate_rota(["a", "b", "c"], 3, 1) == [["a"], ["b"], ["c"]]
    assert rotate_rota(["a"], 0, 1) == []
''',
        "acceptance_tests": '''import pytest

from slotplan.rotate_rota import rotate_rota


def test_round_robin():
    assert rotate_rota(["ana", "ben", "cy"], 2, 2) == [["ana", "ben"], ["cy", "ana"]]
    assert rotate_rota(["ana", "ben", "cy", "dee"], 3, 1, first_day=1) == [["ana"], ["ben"], ["cy"]]


def test_weekends():
    assert rotate_rota(["ana", "ben", "cy"], 4, 1, first_day=4) == [["ana"], [], [], ["ben"]]
    assert rotate_rota(["ana", "ben"], 7, 1) == [["ana"], ["ben"], ["ana"], ["ben"], ["ana"], [], []]


def test_invalid_arguments():
    with pytest.raises(ValueError):
        rotate_rota([], 3, 1)
    with pytest.raises(ValueError):
        rotate_rota(["ana"], 3, 2)
''',
        "conflicting_test": '''def test_regression_issue_473():
    assert rotate_rota(["ana", "ben", "cy"], 4, 1, first_day=4) == [["ana"], [], [], ["ana"]]
''',
        "conflict_call": 'rotate_rota(["ana", "ben", "cy"], 4, 1, first_day=4)',
        "oneoff": {"find": '== [["ana", "ben"], ["cy", "ana"]]', "replace": '== [["ana", "ben"], ["cy", "ben"]]'},
    },
    # ------------------------------------------------------------------ rest_violations
    {
        "id": "rest_violations",
        "signature": "def rest_violations(rota: Mapping[str, Sequence[str]], min_rest: int = 660) -> List[Tuple[str, int, int]]:",
        "deps": ["parse_shift"],
        "difficulty": "hard",
        "summary": "Find shifts that start before the minimum rest period has passed",
        "spec": """`rota` maps each worker to their shifts for one week, written as rota entries
understood by parse_shift (e.g. "Mon 22:00-06:00"). The same rota repeats
every week.

For every worker, take their shifts in chronological order and measure the
rest between the end of one shift and the start of the next. Report each
case where that rest is shorter than `min_rest` minutes (default 11 hours) as
(worker, day, rest): `day` is the weekday index of the shift that starts too
early and `rest` is the rest in minutes (0 or negative if the shifts touch or
overlap).

The result is sorted by worker, then day, then rest.
Raise ValueError if an entry cannot be parsed.

Example:
    rest_violations({"kim": ["Mon 14:00-22:00", "Tue 06:00-14:00"]}) == [("kim", 1, 480)]
""",
        "clarification": """Because the rota repeats, the rest after a worker's last shift of the week
runs into their first shift of the following week (e.g. Sunday evening to
Monday morning) and has to be checked as well.""",
        "reference": '''from typing import List, Mapping, Sequence, Tuple

from slotplan.parse_shift import parse_shift

_WEEK = 7 * 1440


def rest_violations(rota: Mapping[str, Sequence[str]], min_rest: int = 660) -> List[Tuple[str, int, int]]:
    found: List[Tuple[str, int, int]] = []
    for worker, entries in rota.items():
        shifts = []
        for entry in entries:
            day, start, end = parse_shift(entry)
            shifts.append((day * 1440 + start, day * 1440 + end, day))
        shifts.sort()
        for index, (start, _end, day) in enumerate(shifts):
            previous_end = shifts[index - 1][1]
            if index == 0:
                previous_end -= _WEEK
            rest = start - previous_end
            if rest < min_rest:
                found.append((worker, day, rest))
    found.sort()
    return found
''',
        "naive": '''from typing import List, Mapping, Sequence, Tuple

from slotplan.parse_shift import parse_shift


def rest_violations(rota: Mapping[str, Sequence[str]], min_rest: int = 660) -> List[Tuple[str, int, int]]:
    found: List[Tuple[str, int, int]] = []
    for worker, entries in rota.items():
        shifts = []
        for entry in entries:
            day, start, end = parse_shift(entry)
            shifts.append((day * 1440 + start, day * 1440 + end, day))
        shifts.sort()
        for previous, current in zip(shifts, shifts[1:]):
            rest = current[0] - previous[1]
            if rest < min_rest:
                found.append((worker, current[2], rest))
    found.sort()
    return found
''',
        "unit_tests": '''from slotplan.rest_violations import rest_violations


def test_rest_basic():
    assert rest_violations({"kim": ["Mon 14:00-22:00", "Tue 06:00-14:00"]}) == [("kim", 1, 480)]
    assert rest_violations({"cy": ["Mon 09:00-17:00", "Tue 09:00-17:00"]}) == []
''',
        "acceptance_tests": '''import pytest

from slotplan.rest_violations import rest_violations


def test_short_rest():
    assert rest_violations({"kim": ["Mon 14:00-22:00", "Tue 06:00-14:00"]}) == [("kim", 1, 480)]
    assert rest_violations({"ann": ["Tue 12:00-20:00", "Mon 22:00-06:00"], "bo": ["Wed 08:00-16:00", "Wed 16:00-20:00"]}) == [("ann", 1, 360), ("bo", 2, 0)]
    assert rest_violations({"kim": ["Mon 14:00-22:00", "Tue 06:00-14:00"]}, min_rest=480) == []


def test_week_boundary():
    assert rest_violations({"lee": ["Mon 06:00-14:00", "Sun 16:00-24:00"]}) == [("lee", 0, 360)]
    assert rest_violations({"max": ["Sun 22:00-06:00", "Mon 12:00-20:00"]}) == [("max", 0, 360)]


def test_bad_entry():
    with pytest.raises(ValueError):
        rest_violations({"kim": ["Someday 09:00-17:00"]})
''',
        "conflicting_test": '''def test_regression_issue_812():
    assert rest_violations({"lee": ["Mon 06:00-14:00", "Sun 16:00-24:00"]}) == []
''',
        "conflict_call": 'rest_violations({"lee": ["Mon 06:00-14:00", "Sun 16:00-24:00"]})',
        "oneoff": {"find": '== [("kim", 1, 480)]', "replace": '== [("kim", 0, 480)]'},
    },
    # ------------------------------------------------------------------ paid_hours
    {
        "id": "paid_hours",
        "signature": "def paid_hours(rota: Mapping[str, Sequence[str]]) -> Dict[str, str]:",
        "deps": ["parse_shift", "format_duration"],
        "difficulty": "medium",
        "summary": "Total each worker's paid time for the week",
        "spec": """Compute each worker's paid working time for one week of rota entries
(parsed with parse_shift) and return it formatted with format_duration, e.g.
{"kim": "38h 30m"}. Every worker in `rota` appears in the result; a worker
with no shifts gets "0m".

Raise ValueError if an entry cannot be parsed.

Example:
    paid_hours({"kim": ["Mon 09:00-13:00", "Tue 13:00-17:30"]}) == {"kim": "8h 30m"}
""",
        "clarification": """Shifts longer than 6 hours include a 30-minute unpaid break, which is
deducted from that shift's paid time. A shift of exactly 6 hours or less has
no deduction.""",
        "reference": '''from typing import Dict, Mapping, Sequence

from slotplan.format_duration import format_duration
from slotplan.parse_shift import parse_shift


def paid_hours(rota: Mapping[str, Sequence[str]]) -> Dict[str, str]:
    totals: Dict[str, str] = {}
    for worker, entries in rota.items():
        minutes = 0
        for entry in entries:
            _day, start, end = parse_shift(entry)
            length = end - start
            if length > 360:
                length -= 30
            minutes += length
        totals[worker] = format_duration(minutes)
    return totals
''',
        "naive": '''from typing import Dict, Mapping, Sequence

from slotplan.format_duration import format_duration
from slotplan.parse_shift import parse_shift


def paid_hours(rota: Mapping[str, Sequence[str]]) -> Dict[str, str]:
    totals: Dict[str, str] = {}
    for worker, entries in rota.items():
        minutes = 0
        for entry in entries:
            _day, start, end = parse_shift(entry)
            minutes += end - start
        totals[worker] = format_duration(minutes)
    return totals
''',
        "unit_tests": '''from slotplan.paid_hours import paid_hours


def test_paid_hours_basic():
    assert paid_hours({"kim": ["Mon 09:00-13:00", "Tue 13:00-17:30"]}) == {"kim": "8h 30m"}
    assert paid_hours({"dee": []}) == {"dee": "0m"}
''',
        "acceptance_tests": '''import pytest

from slotplan.paid_hours import paid_hours


def test_short_shifts():
    assert paid_hours({"kim": ["Mon 09:00-13:00", "Tue 13:00-17:30"]}) == {"kim": "8h 30m"}
    assert paid_hours({"cy": ["Wed 08:00-14:00"], "dee": []}) == {"cy": "6h", "dee": "0m"}


def test_long_shifts():
    assert paid_hours({"ann": ["Mon 09:00-17:00", "Tue 09:00-17:00"]}) == {"ann": "15h"}
    assert paid_hours({"bo": ["Sat 22:00-06:00", "Sun 10:00-14:00"]}) == {"bo": "11h 30m"}


def test_bad_entry():
    with pytest.raises(ValueError):
        paid_hours({"kim": ["Funday 09:00-17:00"]})
''',
        "conflicting_test": '''def test_regression_issue_655():
    assert paid_hours({"ann": ["Mon 09:00-17:00", "Tue 09:00-17:00"]}) == {"ann": "16h"}
''',
        "conflict_call": 'paid_hours({"ann": ["Mon 09:00-17:00", "Tue 09:00-17:00"]})',
        "oneoff": {"find": '{"bo": "11h 30m"}', "replace": '{"bo": "11h"}'},
    },
    # ------------------------------------------------------------------ uncovered_periods
    {
        "id": "uncovered_periods",
        "signature": "def uncovered_periods(rota: Mapping[str, Sequence[str]], day: int, open_start: int, open_end: int) -> List[Tuple[int, int]]:",
        "deps": ["parse_shift", "subtract_intervals"],
        "difficulty": "hard",
        "summary": "Find opening hours on a given day with nobody on shift",
        "spec": """Return the periods within the opening hours [open_start, open_end) of weekday
`day` (0 = Monday ... 6 = Sunday) during which no worker in `rota` is on
shift. `rota` maps workers to weekly rota entries understood by parse_shift.
The result is a sorted list of (start, end) tuples in minutes since midnight
of `day`; compute it with subtract_intervals.

Raise ValueError if day is not in 0..6, if open_end <= open_start, or if an
entry cannot be parsed.

Example:
    uncovered_periods({"kim": ["Mon 08:00-12:00"], "ann": ["Mon 13:00-18:00"]}, 0, 480, 1080)
        == [(720, 780)]
""",
        "clarification": """A shift that starts on the previous day and runs past midnight (e.g.
"Mon 22:00-06:00" when looking at Tuesday) also covers the early hours of
`day`. The rota repeats weekly, so for Monday the previous day is Sunday.""",
        "reference": '''from typing import List, Mapping, Sequence, Tuple

from slotplan.parse_shift import parse_shift
from slotplan.subtract_intervals import subtract_intervals


def uncovered_periods(rota: Mapping[str, Sequence[str]], day: int, open_start: int, open_end: int) -> List[Tuple[int, int]]:
    if not 0 <= day <= 6:
        raise ValueError("day must be a weekday index 0..6")
    if open_end <= open_start:
        raise ValueError("empty opening hours")
    previous_day = (day - 1) % 7
    covered = []
    for entries in rota.values():
        for entry in entries:
            shift_day, start, end = parse_shift(entry)
            if shift_day == day:
                covered.append((start, end))
            if shift_day == previous_day and end > 1440:
                covered.append((start - 1440, end - 1440))
    return subtract_intervals([(open_start, open_end)], covered)
''',
        "naive": '''from typing import List, Mapping, Sequence, Tuple

from slotplan.parse_shift import parse_shift
from slotplan.subtract_intervals import subtract_intervals


def uncovered_periods(rota: Mapping[str, Sequence[str]], day: int, open_start: int, open_end: int) -> List[Tuple[int, int]]:
    if not 0 <= day <= 6:
        raise ValueError("day must be a weekday index 0..6")
    if open_end <= open_start:
        raise ValueError("empty opening hours")
    covered = []
    for entries in rota.values():
        for entry in entries:
            shift_day, start, end = parse_shift(entry)
            if shift_day == day:
                covered.append((start, end))
    return subtract_intervals([(open_start, open_end)], covered)
''',
        "unit_tests": '''from slotplan.uncovered_periods import uncovered_periods


def test_uncovered_basic():
    rota = {"kim": ["Mon 08:00-12:00"], "ann": ["Mon 13:00-18:00"]}
    assert uncovered_periods(rota, 0, 480, 1080) == [(720, 780)]
    assert uncovered_periods(rota, 2, 480, 1080) == [(480, 1080)]
''',
        "acceptance_tests": '''import pytest

from slotplan.uncovered_periods import uncovered_periods


def test_same_day_gaps():
    assert uncovered_periods({"kim": ["Mon 08:00-12:00"], "ann": ["Mon 13:00-18:00"]}, 0, 480, 1080) == [(720, 780)]
    assert uncovered_periods({"kim": ["Mon 08:00-12:00"]}, 2, 480, 1080) == [(480, 1080)]
    assert uncovered_periods({"kim": ["Fri 07:00-15:00"], "bo": ["Fri 14:00-22:00"]}, 4, 480, 1200) == []


def test_overnight_cover():
    assert uncovered_periods({"kim": ["Tue 06:00-14:00"], "lee": ["Mon 22:00-06:30"]}, 1, 0, 1440) == [(840, 1440)]
    assert uncovered_periods({"max": ["Sun 20:00-04:00"], "ann": ["Mon 08:00-16:00"]}, 0, 0, 960) == [(240, 480)]


def test_invalid_day():
    with pytest.raises(ValueError):
        uncovered_periods({}, 7, 480, 1080)
''',
        "conflicting_test": '''def test_regression_issue_741():
    assert uncovered_periods({"kim": ["Tue 06:00-14:00"], "lee": ["Mon 22:00-06:30"]}, 1, 0, 1440) == [(0, 360), (840, 1440)]
''',
        "conflict_call": 'uncovered_periods({"kim": ["Tue 06:00-14:00"], "lee": ["Mon 22:00-06:30"]}, 1, 0, 1440)',
        "oneoff": {"find": "== [(480, 1080)]", "replace": "== []"},
    },
    # ------------------------------------------------------------------ format_agenda
    {
        "id": "format_agenda",
        "signature": "def format_agenda(meetings: Iterable[Tuple[str, int, int]]) -> List[str]:",
        "deps": ["format_hhmm", "format_duration"],
        "difficulty": "medium",
        "summary": "Render a day's meetings as agenda lines",
        "spec": """Render meetings given as (title, start, end) into agenda lines of the form

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
""",
        "clarification": """A meeting that ends after midnight (end > 1440) gets a "+1" suffix on its end
time to show it finishes the next day, e.g. "23:00-01:00+1  Release (2h)". A
meeting ending exactly at 1440 has no suffix.""",
        "reference": '''from typing import Iterable, List, Tuple

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
''',
        "naive": '''from typing import Iterable, List, Tuple

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
''',
        "unit_tests": '''from slotplan.format_agenda import format_agenda


def test_agenda_basic():
    lines = format_agenda([("Design review", 600, 690), ("Standup", 540, 555)])
    assert lines == ["09:00-09:15  Standup (15m)", "10:00-11:30  Design review (1h 30m)"]
    assert format_agenda([]) == []
''',
        "acceptance_tests": '''import pytest

from slotplan.format_agenda import format_agenda


def test_ordering():
    assert format_agenda([("Design review", 600, 690), ("Standup", 540, 555)]) == ["09:00-09:15  Standup (15m)", "10:00-11:30  Design review (1h 30m)"]
    assert format_agenda([("B", 540, 600), ("A", 540, 600), ("C", 540, 570)]) == ["09:00-09:30  C (30m)", "09:00-10:00  A (1h)", "09:00-10:00  B (1h)"]


def test_late_meetings():
    assert format_agenda([("Late call", 1410, 1440)]) == ["23:30-24:00  Late call (30m)"]
    assert format_agenda([("Release", 1380, 1500)]) == ["23:00-01:00+1  Release (2h)"]


def test_invalid_meeting():
    with pytest.raises(ValueError):
        format_agenda([("Broken", 600, 600)])
''',
        "conflicting_test": '''def test_regression_issue_936():
    assert format_agenda([("Release", 1380, 1500)]) == ["23:00-01:00  Release (2h)"]
''',
        "conflict_call": 'format_agenda([("Release", 1380, 1500)])',
        "oneoff": {"find": '"09:00-09:30  C (30m)"', "replace": '"09:00-09:30  C (0h 30m)"'},
    },
]
