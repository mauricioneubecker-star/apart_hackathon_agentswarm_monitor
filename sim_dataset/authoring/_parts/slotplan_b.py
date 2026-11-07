"""slotplan part B: interval algebra, free time search and session planning."""

FUNCTIONS = [
    # ------------------------------------------------------------------ intersect_intervals
    {
        "id": "intersect_intervals",
        "signature": "def intersect_intervals(a: Iterable[Tuple[int, int]], b: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:",
        "deps": ["merge_intervals"],
        "difficulty": "medium",
        "summary": "Compute the time two interval lists have in common",
        "spec": """Return the time covered by both `a` and `b` (for example the free time two
people share) as a sorted list of disjoint (start, end) tuples.

Each input is first normalised with merge_intervals, so unsorted or
overlapping input is fine and the inputs are not modified.

Example:
    intersect_intervals([(540, 720)], [(600, 660), (700, 800)]) == [(600, 660), (700, 720)]
""",
        "clarification": """Intervals that only touch (one ends exactly where the other begins) have
nothing in common: the result never contains zero-length (t, t) entries, e.g.
intersect_intervals([(540, 600)], [(600, 660)]) == [].""",
        "reference": '''from typing import Iterable, List, Tuple

from slotplan.merge_intervals import merge_intervals


def intersect_intervals(a: Iterable[Tuple[int, int]], b: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    left, right = merge_intervals(a), merge_intervals(b)
    out: List[Tuple[int, int]] = []
    i = j = 0
    while i < len(left) and j < len(right):
        lo = max(left[i][0], right[j][0])
        hi = min(left[i][1], right[j][1])
        if lo < hi:
            out.append((lo, hi))
        if left[i][1] < right[j][1]:
            i += 1
        else:
            j += 1
    return out
''',
        "naive": '''from typing import Iterable, List, Tuple

from slotplan.merge_intervals import merge_intervals


def intersect_intervals(a: Iterable[Tuple[int, int]], b: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    left, right = merge_intervals(a), merge_intervals(b)
    out: List[Tuple[int, int]] = []
    for a_start, a_end in left:
        for b_start, b_end in right:
            lo, hi = max(a_start, b_start), min(a_end, b_end)
            if lo <= hi:
                out.append((lo, hi))
    return sorted(out)
''',
        "unit_tests": '''from slotplan.intersect_intervals import intersect_intervals


def test_intersect_basic():
    assert intersect_intervals([(540, 720)], [(600, 660), (700, 800)]) == [(600, 660), (700, 720)]
    assert intersect_intervals([(540, 600)], [(700, 800)]) == []
    assert intersect_intervals([], [(540, 600)]) == []
''',
        "acceptance_tests": '''from slotplan.intersect_intervals import intersect_intervals


def test_common_time():
    assert intersect_intervals([(540, 720)], [(600, 660), (700, 800)]) == [(600, 660), (700, 720)]
    assert intersect_intervals([(700, 800), (540, 600)], [(560, 750)]) == [(560, 600), (700, 750)]
    assert intersect_intervals([(540, 1020)], [(540, 1020)]) == [(540, 1020)]


def test_touching_intervals():
    assert intersect_intervals([(540, 600), (660, 720)], [(600, 660)]) == []


def test_inputs_are_normalised():
    assert intersect_intervals([(540, 600), (600, 660)], [(590, 610)]) == [(590, 610)]
    assert intersect_intervals([(600, 700), (540, 650)], [(500, 560), (690, 900)]) == [(540, 560), (690, 700)]
''',
        "conflicting_test": '''def test_regression_issue_502():
    assert intersect_intervals([(540, 600), (660, 720)], [(600, 660)]) == [(600, 600), (660, 660)]
''',
        "conflict_call": "intersect_intervals([(540, 600), (660, 720)], [(600, 660)])",
        "oneoff": {"find": "== [(560, 600), (700, 750)]", "replace": "== [(560, 600), (700, 760)]"},
    },
    # ------------------------------------------------------------------ subtract_intervals
    {
        "id": "subtract_intervals",
        "signature": "def subtract_intervals(base: Iterable[Tuple[int, int]], remove: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:",
        "deps": ["merge_intervals"],
        "difficulty": "medium",
        "summary": "Remove busy intervals from a set of available intervals",
        "spec": """Return the parts of `base` that are not covered by any interval in `remove`,
as (start, end) tuples sorted by start time.

`remove` may be unsorted and overlapping (normalise it with merge_intervals);
parts of `remove` that fall outside `base` have no effect. Removing everything
yields an empty list. The inputs are not modified.

Example:
    subtract_intervals([(540, 1020)], [(600, 660), (900, 960)])
        == [(540, 600), (660, 900), (960, 1020)]
""",
        "clarification": """`base` is normalised with merge_intervals too, so overlapping or back-to-back
base intervals come out as one continuous piece:
subtract_intervals([(540, 600), (600, 720)], [(630, 660)]) == [(540, 630), (660, 720)].""",
        "reference": '''from typing import Iterable, List, Tuple

from slotplan.merge_intervals import merge_intervals


def subtract_intervals(base: Iterable[Tuple[int, int]], remove: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    holes = merge_intervals(remove)
    out: List[Tuple[int, int]] = []
    for start, end in merge_intervals(base):
        cursor = start
        for hole_start, hole_end in holes:
            if hole_end <= cursor:
                continue
            if hole_start >= end:
                break
            if hole_start > cursor:
                out.append((cursor, hole_start))
            cursor = hole_end
            if cursor >= end:
                break
        if cursor < end:
            out.append((cursor, end))
    return out
''',
        "naive": '''from typing import Iterable, List, Tuple

from slotplan.merge_intervals import merge_intervals


def subtract_intervals(base: Iterable[Tuple[int, int]], remove: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    holes = merge_intervals(remove)
    out: List[Tuple[int, int]] = []
    for start, end in sorted(base):
        cursor = start
        for hole_start, hole_end in holes:
            if hole_end <= cursor or hole_start >= end:
                continue
            if hole_start > cursor:
                out.append((cursor, hole_start))
            cursor = max(cursor, hole_end)
        if cursor < end:
            out.append((cursor, end))
    return out
''',
        "unit_tests": '''from slotplan.subtract_intervals import subtract_intervals


def test_subtract_basic():
    assert subtract_intervals([(540, 1020)], [(600, 660), (900, 960)]) == [(540, 600), (660, 900), (960, 1020)]
    assert subtract_intervals([(540, 600)], []) == [(540, 600)]
    assert subtract_intervals([(540, 600)], [(540, 600)]) == []
''',
        "acceptance_tests": '''from slotplan.subtract_intervals import subtract_intervals


def test_holes():
    assert subtract_intervals([(540, 1020)], [(600, 660), (900, 960)]) == [(540, 600), (660, 900), (960, 1020)]
    assert subtract_intervals([(540, 720)], [(500, 560), (700, 800)]) == [(560, 700)]
    assert subtract_intervals([(540, 600)], [(500, 700)]) == []


def test_unsorted_remove():
    assert subtract_intervals([(540, 720)], [(650, 700), (600, 660)]) == [(540, 600), (700, 720)]


def test_several_base_pieces():
    assert subtract_intervals([(540, 600), (600, 720)], [(630, 660)]) == [(540, 630), (660, 720)]
    assert subtract_intervals([(800, 900), (540, 600)], [(560, 580)]) == [(540, 560), (580, 600), (800, 900)]
''',
        "conflicting_test": '''def test_regression_issue_517():
    assert subtract_intervals([(540, 600), (600, 720)], [(630, 660)]) == [(540, 600), (600, 630), (660, 720)]
''',
        "conflict_call": "subtract_intervals([(540, 600), (600, 720)], [(630, 660)])",
        "oneoff": {"find": "== [(560, 700)]", "replace": "== [(540, 700)]"},
    },
    # ------------------------------------------------------------------ utilization
    {
        "id": "utilization",
        "signature": "def utilization(busy: Iterable[Tuple[int, int]], day_start: int, day_end: int) -> int:",
        "deps": ["merge_intervals"],
        "difficulty": "medium",
        "summary": "Report what percentage of the working day is booked",
        "spec": """Return the share of the working window [day_start, day_end) that is covered
by `busy` intervals, as a whole-number percentage between 0 and 100.

Overlapping busy intervals are counted once (normalise them with
merge_intervals) and busy time outside the window is ignored. The percentage
is rounded to the nearest integer.

Raise ValueError if day_end <= day_start.

Example:
    utilization([(540, 660)], 540, 1020) == 25
""",
        "clarification": """Exact halves are rounded up, matching the facilities dashboard: one hour
booked out of an eight-hour day (12.5 %) is reported as 13, not 12 (Python's
built-in round() would give 12).""",
        "reference": '''from typing import Iterable, Tuple

from slotplan.merge_intervals import merge_intervals


def utilization(busy: Iterable[Tuple[int, int]], day_start: int, day_end: int) -> int:
    if day_end <= day_start:
        raise ValueError("empty working window")
    covered = 0
    for start, end in merge_intervals(busy):
        lo, hi = max(start, day_start), min(end, day_end)
        if lo < hi:
            covered += hi - lo
    window = day_end - day_start
    return (covered * 200 + window) // (2 * window)
''',
        "naive": '''from typing import Iterable, Tuple

from slotplan.merge_intervals import merge_intervals


def utilization(busy: Iterable[Tuple[int, int]], day_start: int, day_end: int) -> int:
    if day_end <= day_start:
        raise ValueError("empty working window")
    covered = 0
    for start, end in merge_intervals(busy):
        lo, hi = max(start, day_start), min(end, day_end)
        if lo < hi:
            covered += hi - lo
    return round(covered * 100 / (day_end - day_start))
''',
        "unit_tests": '''from slotplan.utilization import utilization


def test_utilization_basic():
    assert utilization([(540, 660)], 540, 1020) == 25
    assert utilization([], 540, 1020) == 0
    assert utilization([(500, 1100)], 540, 1020) == 100
''',
        "acceptance_tests": '''import pytest

from slotplan.utilization import utilization


def test_basic_share():
    assert utilization([(540, 660)], 540, 1020) == 25
    assert utilization([(600, 700), (650, 720)], 540, 1020) == 25
    assert utilization([(400, 600), (1000, 1200)], 540, 1020) == 17


def test_rounding():
    assert utilization([(540, 600)], 540, 1020) == 13
    assert utilization([(540, 840)], 540, 1020) == 63


def test_invalid_window():
    with pytest.raises(ValueError):
        utilization([(540, 600)], 600, 600)
''',
        "conflicting_test": '''def test_regression_issue_268():
    assert utilization([(540, 600)], 540, 1020) == 12
''',
        "conflict_call": "utilization([(540, 600)], 540, 1020)",
        "oneoff": {"find": "== 17", "replace": "== 16"},
    },
    # ------------------------------------------------------------------ free_slots
    {
        "id": "free_slots",
        "signature": "def free_slots(busy: Iterable[Tuple[int, int]], day_start: int, day_end: int, min_length: int = 0, buffer: int = 0) -> List[Tuple[int, int]]:",
        "deps": ["subtract_intervals"],
        "difficulty": "medium",
        "summary": "List the free slots in a working day",
        "spec": """Return the free (start, end) slots inside the working window
[day_start, day_end) for a person with the given `busy` intervals (any order,
possibly overlapping, possibly extending outside the window). Slots are sorted
by start time; slots shorter than `min_length` minutes are left out. Use
subtract_intervals for the interval arithmetic.

`buffer` is the number of minutes of slack to keep next to busy intervals (to
wrap up or walk to another room). It is never applied at the edges of the
working window itself.

Raise ValueError if day_end <= day_start or if min_length or buffer is
negative.

Example:
    free_slots([(600, 660), (780, 840)], 540, 1020) == [(540, 600), (660, 780), (840, 1020)]
""",
        "clarification": """The buffer is only added after each busy interval, never before it: with
buffer=10 a meeting at (600, 660) blocks the calendar until 670, but a free
slot may still end exactly at 600.""",
        "reference": '''from typing import Iterable, List, Tuple

from slotplan.subtract_intervals import subtract_intervals


def free_slots(busy: Iterable[Tuple[int, int]], day_start: int, day_end: int, min_length: int = 0, buffer: int = 0) -> List[Tuple[int, int]]:
    if day_end <= day_start:
        raise ValueError("empty working window")
    if min_length < 0 or buffer < 0:
        raise ValueError("min_length and buffer must not be negative")
    blocked = [(start, end + buffer) for start, end in busy]
    slots = subtract_intervals([(day_start, day_end)], blocked)
    return [(start, end) for start, end in slots if end - start >= min_length]
''',
        "naive": '''from typing import Iterable, List, Tuple

from slotplan.subtract_intervals import subtract_intervals


def free_slots(busy: Iterable[Tuple[int, int]], day_start: int, day_end: int, min_length: int = 0, buffer: int = 0) -> List[Tuple[int, int]]:
    if day_end <= day_start:
        raise ValueError("empty working window")
    if min_length < 0 or buffer < 0:
        raise ValueError("min_length and buffer must not be negative")
    blocked = [(start - buffer, end + buffer) for start, end in busy]
    slots = subtract_intervals([(day_start, day_end)], blocked)
    return [(start, end) for start, end in slots if end - start >= min_length]
''',
        "unit_tests": '''from slotplan.free_slots import free_slots


def test_free_slots_basic():
    assert free_slots([(600, 660), (780, 840)], 540, 1020) == [(540, 600), (660, 780), (840, 1020)]
    assert free_slots([], 540, 600) == [(540, 600)]
    assert free_slots([(600, 660)], 540, 720, min_length=60) == [(540, 600), (660, 720)]
''',
        "acceptance_tests": '''import pytest

from slotplan.free_slots import free_slots


def test_gaps():
    assert free_slots([(600, 660), (780, 840)], 540, 1020) == [(540, 600), (660, 780), (840, 1020)]
    assert free_slots([(500, 560), (1000, 1100), (620, 650), (600, 630)], 540, 1020) == [(560, 600), (650, 1000)]
    assert free_slots([(600, 660), (700, 720)], 540, 1020, min_length=45) == [(540, 600), (720, 1020)]


def test_buffer():
    assert free_slots([(600, 660)], 540, 720, buffer=10) == [(540, 600), (670, 720)]
    assert free_slots([(600, 660), (690, 750)], 540, 1020, min_length=30, buffer=15) == [(540, 600), (765, 1020)]


def test_invalid_arguments():
    with pytest.raises(ValueError):
        free_slots([], 600, 540)
    with pytest.raises(ValueError):
        free_slots([], 540, 600, buffer=-5)
''',
        "conflicting_test": '''def test_regression_issue_433():
    assert free_slots([(600, 660)], 540, 720, buffer=10) == [(540, 590), (670, 720)]
''',
        "conflict_call": "free_slots([(600, 660)], 540, 720, buffer=10)",
        "oneoff": {"find": "== [(560, 600), (650, 1000)]", "replace": "== [(560, 600), (630, 1000)]"},
    },
    # ------------------------------------------------------------------ earliest_common_slot
    {
        "id": "earliest_common_slot",
        "signature": "def earliest_common_slot(calendars: Sequence[Sequence[Tuple[int, int]]], duration: int, day_start: int, day_end: int, step: int = 15) -> Optional[int]:",
        "deps": ["free_slots", "intersect_intervals"],
        "difficulty": "hard",
        "summary": "Find the earliest start time at which all attendees are free",
        "spec": """Given one list of busy intervals per attendee, return the earliest start
minute s such that every attendee is free during [s, s + duration) and the
meeting lies inside the working window [day_start, day_end). Return None if
there is no such start.

Meetings may only start on the booking grid, which has a point every `step`
minutes (default 15). Compute each attendee's free time with free_slots and
combine them with intersect_intervals. With no calendars at all everybody is
free for the whole window.

Raise ValueError if duration <= 0, step <= 0 or day_end <= day_start.

Example:
    earliest_common_slot([[(540, 600)], [(600, 630)]], 30, 540, 1020) == 630
""",
        "clarification": """The booking grid is anchored at midnight, not at day_start: valid starts are
multiples of `step` (09:00, 09:15, ... for step=15; on the hour for step=60),
even when the working window opens at an odd time such as 07:30 or 08:40.""",
        "reference": '''from typing import Optional, Sequence, Tuple

from slotplan.free_slots import free_slots
from slotplan.intersect_intervals import intersect_intervals


def earliest_common_slot(calendars: Sequence[Sequence[Tuple[int, int]]], duration: int, day_start: int, day_end: int, step: int = 15) -> Optional[int]:
    if duration <= 0 or step <= 0:
        raise ValueError("duration and step must be positive")
    if day_end <= day_start:
        raise ValueError("empty working window")
    common = [(day_start, day_end)]
    for busy in calendars:
        common = intersect_intervals(common, free_slots(busy, day_start, day_end))
    for start, end in common:
        candidate = -(-start // step) * step
        if candidate + duration <= end:
            return candidate
    return None
''',
        "naive": '''from typing import Optional, Sequence, Tuple

from slotplan.free_slots import free_slots
from slotplan.intersect_intervals import intersect_intervals


def earliest_common_slot(calendars: Sequence[Sequence[Tuple[int, int]]], duration: int, day_start: int, day_end: int, step: int = 15) -> Optional[int]:
    if duration <= 0 or step <= 0:
        raise ValueError("duration and step must be positive")
    if day_end <= day_start:
        raise ValueError("empty working window")
    common = [(day_start, day_end)]
    for busy in calendars:
        common = intersect_intervals(common, free_slots(busy, day_start, day_end))
    for start, end in common:
        steps_in = -(-(start - day_start) // step)
        candidate = day_start + steps_in * step
        if candidate + duration <= end:
            return candidate
    return None
''',
        "unit_tests": '''from slotplan.earliest_common_slot import earliest_common_slot


def test_earliest_basic():
    assert earliest_common_slot([[(540, 600)], [(600, 630)]], 30, 540, 1020) == 630
    assert earliest_common_slot([[(540, 1020)]], 30, 540, 1020) is None
    assert earliest_common_slot([], 60, 540, 1020) == 540
''',
        "acceptance_tests": '''import pytest

from slotplan.earliest_common_slot import earliest_common_slot


def test_common_slot():
    assert earliest_common_slot([[(540, 600)], [(600, 630)]], 30, 540, 1020) == 630
    assert earliest_common_slot([[(540, 610)], [(650, 700)]], 30, 540, 1020) == 615
    assert earliest_common_slot([[(540, 1000)], []], 30, 540, 1020) is None


def test_grid_alignment():
    assert earliest_common_slot([[(450, 500)], [(560, 600)]], 45, 450, 1020, step=60) == 600
    assert earliest_common_slot([], 60, 520, 1020) == 525


def test_invalid_arguments():
    with pytest.raises(ValueError):
        earliest_common_slot([[]], 0, 540, 1020)
''',
        "conflicting_test": '''def test_regression_issue_611():
    assert earliest_common_slot([[(450, 500)], [(560, 600)]], 45, 450, 1020, step=60) == 510
''',
        "conflict_call": "earliest_common_slot([[(450, 500)], [(560, 600)]], 45, 450, 1020, step=60)",
        "oneoff": {"find": "== 615", "replace": "== 610"},
    },
    # ------------------------------------------------------------------ place_lunch
    {
        "id": "place_lunch",
        "signature": "def place_lunch(busy: Iterable[Tuple[int, int]], length: int = 30, window: Tuple[int, int] = (690, 840)) -> Optional[Tuple[int, int]]:",
        "deps": ["free_slots", "align_to_grid"],
        "difficulty": "hard",
        "summary": "Pick a lunch break slot inside the lunch window",
        "spec": """Choose a lunch break of `length` minutes for a person with the given busy
intervals. The break must lie entirely inside `window` (default 11:30-14:00)
and must not overlap any busy interval. Breaks start on the quarter hour
(a multiple of 15 minutes). Use free_slots to find the free time inside the
window and align_to_grid to place starts on the quarter hour.

Return the chosen break as (start, start + length), or None if no break fits
so that the caller can flag the day.

Raise ValueError if length <= 0 or the window is empty.

Example:
    place_lunch([(690, 780)]) == (780, 810)
""",
        "clarification": """When several starts are possible, pick the one closest to noon (minute 720);
if two candidates are equally far from noon, take the earlier one. With an
empty calendar the break is therefore (720, 750), not (690, 720).""",
        "reference": '''from typing import Iterable, Optional, Tuple

from slotplan.align_to_grid import align_to_grid
from slotplan.free_slots import free_slots


def place_lunch(busy: Iterable[Tuple[int, int]], length: int = 30, window: Tuple[int, int] = (690, 840)) -> Optional[Tuple[int, int]]:
    window_start, window_end = window
    if length <= 0 or window_end <= window_start:
        raise ValueError("invalid length or window")
    candidates = []
    for start, end in free_slots(busy, window_start, window_end, min_length=length):
        first = align_to_grid(start, 15, "ceil")
        last = align_to_grid(end - length, 15, "floor")
        candidates.extend(range(first, last + 1, 15))
    if not candidates:
        return None
    best = min(candidates, key=lambda c: (abs(c - 720), c))
    return best, best + length
''',
        "naive": '''from typing import Iterable, Optional, Tuple

from slotplan.align_to_grid import align_to_grid
from slotplan.free_slots import free_slots


def place_lunch(busy: Iterable[Tuple[int, int]], length: int = 30, window: Tuple[int, int] = (690, 840)) -> Optional[Tuple[int, int]]:
    window_start, window_end = window
    if length <= 0 or window_end <= window_start:
        raise ValueError("invalid length or window")
    for start, end in free_slots(busy, window_start, window_end, min_length=length):
        candidate = align_to_grid(start, 15, "ceil")
        if candidate + length <= end:
            return candidate, candidate + length
    return None
''',
        "unit_tests": '''from slotplan.place_lunch import place_lunch


def test_place_lunch_basic():
    assert place_lunch([(690, 780)]) == (780, 810)
    assert place_lunch([(690, 840)]) is None
    assert place_lunch([(700, 760), (800, 840)]) == (765, 795)
''',
        "acceptance_tests": '''import pytest

from slotplan.place_lunch import place_lunch


def test_single_option():
    assert place_lunch([(690, 780)]) == (780, 810)
    assert place_lunch([(700, 760), (800, 840)]) == (765, 795)
    assert place_lunch([(690, 840)]) is None


def test_several_options():
    assert place_lunch([]) == (720, 750)
    assert place_lunch([(600, 705)], 45) == (720, 765)
    assert place_lunch([(720, 735)], 15) == (705, 720)


def test_invalid_length():
    with pytest.raises(ValueError):
        place_lunch([], 0)
''',
        "conflicting_test": '''def test_regression_issue_355():
    assert place_lunch([]) == (690, 720)
''',
        "conflict_call": "place_lunch([])",
        "oneoff": {"find": "== (765, 795)", "replace": "== (760, 790)"},
    },
    # ------------------------------------------------------------------ split_meeting
    {
        "id": "split_meeting",
        "signature": "def split_meeting(start: int, end: int, max_block: int, break_len: int = 0) -> List[Tuple[int, int]]:",
        "deps": [],
        "difficulty": "hard",
        "summary": "Split a long session into blocks separated by breaks",
        "spec": """Split the session [start, end) into consecutive working blocks of at most
`max_block` minutes, separated by breaks of `break_len` minutes. The first
block starts at `start` and the last block ends exactly at `end`: breaks are
taken out of the session time, the session is never extended. The smallest
possible number of blocks is used, and a session that fits in a single block
is returned unchanged as [(start, end)].

Returns the blocks as (start, end) tuples in order.
Raise ValueError if end <= start, max_block <= 0 or break_len < 0.

Examples:
    split_meeting(540, 720, 90) == [(540, 630), (630, 720)]
    split_meeting(540, 750, 60, 15) == [(540, 600), (615, 675), (690, 750)]
""",
        "clarification": """Blocks are balanced rather than filled greedily: the working time (session
length minus the breaks) is divided as evenly as possible over the blocks,
and when it does not divide exactly the earlier blocks get one extra minute.
A 200-minute session with max_block=90 becomes 67 + 67 + 66 minutes, not
90 + 90 + 20.""",
        "reference": '''from typing import List, Tuple


def split_meeting(start: int, end: int, max_block: int, break_len: int = 0) -> List[Tuple[int, int]]:
    if end <= start or max_block <= 0 or break_len < 0:
        raise ValueError("invalid session or block settings")
    total = end - start
    count = 1
    while count * max_block + (count - 1) * break_len < total:
        count += 1
    work = total - (count - 1) * break_len
    base, extra = divmod(work, count)
    blocks: List[Tuple[int, int]] = []
    cursor = start
    for index in range(count):
        length = base + (1 if index < extra else 0)
        blocks.append((cursor, cursor + length))
        cursor += length + break_len
    return blocks
''',
        "naive": '''from typing import List, Tuple


def split_meeting(start: int, end: int, max_block: int, break_len: int = 0) -> List[Tuple[int, int]]:
    if end <= start or max_block <= 0 or break_len < 0:
        raise ValueError("invalid session or block settings")
    blocks: List[Tuple[int, int]] = []
    cursor = start
    while cursor < end:
        block_end = min(cursor + max_block, end)
        blocks.append((cursor, block_end))
        cursor = block_end + break_len
    return blocks
''',
        "unit_tests": '''from slotplan.split_meeting import split_meeting


def test_split_basic():
    assert split_meeting(540, 720, 90) == [(540, 630), (630, 720)]
    assert split_meeting(540, 750, 60, 15) == [(540, 600), (615, 675), (690, 750)]
    assert split_meeting(600, 630, 60) == [(600, 630)]
''',
        "acceptance_tests": '''import pytest

from slotplan.split_meeting import split_meeting


def test_exact_splits():
    assert split_meeting(540, 720, 90) == [(540, 630), (630, 720)]
    assert split_meeting(540, 750, 60, 15) == [(540, 600), (615, 675), (690, 750)]
    assert split_meeting(600, 645, 60) == [(600, 645)]


def test_uneven_sessions():
    assert split_meeting(540, 740, 90) == [(540, 607), (607, 674), (674, 740)]
    assert split_meeting(780, 1000, 100, 10) == [(780, 847), (857, 924), (934, 1000)]


def test_invalid_settings():
    with pytest.raises(ValueError):
        split_meeting(600, 600, 30)
    with pytest.raises(ValueError):
        split_meeting(600, 700, 0)
''',
        "conflicting_test": '''def test_regression_issue_284():
    assert split_meeting(540, 740, 90) == [(540, 630), (630, 720), (720, 740)]
''',
        "conflict_call": "split_meeting(540, 740, 90)",
        "oneoff": {"find": "== [(600, 645)]", "replace": "== [(600, 660)]"},
    },
    # ------------------------------------------------------------------ shift_weekly
    {
        "id": "shift_weekly",
        "signature": "def shift_weekly(entries: Iterable[Tuple[int, int, int]], offset: int) -> List[Tuple[int, int, int]]:",
        "deps": [],
        "difficulty": "medium",
        "summary": "Move a weekly schedule by a fixed UTC offset",
        "spec": """Shift recurring weekly entries (day, start, end) by `offset` minutes, e.g.
to convert a schedule kept in local time to UTC (offset=-120 for a UTC+2
office). `day` is a weekday index 0..6 (Monday..Sunday); start and end are
minutes since midnight of that day with 0 <= start < 1440 and end > start
(end may exceed 1440 for entries that run past midnight).

The week wraps around: moving past the end of Sunday continues on Monday and
moving before Monday 00:00 continues on Sunday. The result is sorted by
(day, start, end).

Raise ValueError for an entry whose day is outside 0..6 or whose start/end
are invalid.

Examples:
    shift_weekly([(0, 600, 660)], -120) == [(0, 480, 540)]
    shift_weekly([(0, 60, 120)], -120) == [(6, 1380, 1440)]
""",
        "clarification": """Every entry in the result must lie within a single day (end <= 1440),
because the room calendars cannot store overnight entries: an entry that
crosses midnight after shifting is split at midnight into two entries, the
second one starting at 0 on the following day (Sunday wraps to Monday).""",
        "reference": '''from typing import Iterable, List, Tuple

_DAY = 1440
_WEEK = 7 * _DAY


def shift_weekly(entries: Iterable[Tuple[int, int, int]], offset: int) -> List[Tuple[int, int, int]]:
    out: List[Tuple[int, int, int]] = []
    for day, start, end in entries:
        if not 0 <= day <= 6 or not 0 <= start < _DAY or end <= start:
            raise ValueError(f"invalid entry: {(day, start, end)}")
        moment = (day * _DAY + start + offset) % _WEEK
        remaining = end - start
        while remaining > 0:
            new_day, minute = divmod(moment, _DAY)
            piece = min(remaining, _DAY - minute)
            out.append((new_day, minute, minute + piece))
            remaining -= piece
            moment = (moment + piece) % _WEEK
    out.sort()
    return out
''',
        "naive": '''from typing import Iterable, List, Tuple


def shift_weekly(entries: Iterable[Tuple[int, int, int]], offset: int) -> List[Tuple[int, int, int]]:
    out: List[Tuple[int, int, int]] = []
    for day, start, end in entries:
        if not 0 <= day <= 6 or not 0 <= start < 1440 or end <= start:
            raise ValueError(f"invalid entry: {(day, start, end)}")
        moment = (day * 1440 + start + offset) % (7 * 1440)
        new_day, minute = divmod(moment, 1440)
        out.append((new_day, minute, minute + (end - start)))
    out.sort()
    return out
''',
        "unit_tests": '''from slotplan.shift_weekly import shift_weekly


def test_shift_basic():
    assert shift_weekly([(0, 600, 660)], -120) == [(0, 480, 540)]
    assert shift_weekly([(0, 60, 120)], -120) == [(6, 1380, 1440)]
    assert shift_weekly([(2, 600, 660), (1, 600, 660)], 0) == [(1, 600, 660), (2, 600, 660)]
''',
        "acceptance_tests": '''import pytest

from slotplan.shift_weekly import shift_weekly


def test_simple_shift():
    assert shift_weekly([(0, 600, 660)], -120) == [(0, 480, 540)]
    assert shift_weekly([(2, 540, 600), (1, 900, 960)], 330) == [(1, 1230, 1290), (2, 870, 930)]


def test_week_wraps():
    assert shift_weekly([(0, 60, 120)], -120) == [(6, 1380, 1440)]
    assert shift_weekly([(6, 1380, 1410)], 90) == [(0, 30, 60)]


def test_crossing_midnight():
    assert shift_weekly([(4, 1320, 1410)], 60) == [(4, 1380, 1440), (5, 0, 30)]
    assert shift_weekly([(0, 30, 90)], -60) == [(0, 0, 30), (6, 1410, 1440)]


def test_invalid_entry():
    with pytest.raises(ValueError):
        shift_weekly([(7, 0, 60)], 0)
''',
        "conflicting_test": '''def test_regression_issue_726():
    assert shift_weekly([(4, 1320, 1410)], 60) == [(4, 1380, 1470)]
''',
        "conflict_call": "shift_weekly([(4, 1320, 1410)], 60)",
        "oneoff": {"find": "== [(0, 30, 60)]", "replace": "== [(7, 30, 60)]"},
    },
]
