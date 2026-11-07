"""stockflow part C: movement records, stock positions and warehouse operations."""

FUNCTIONS = [
    # ------------------------------------------------------------------ parse_movement_line
    {
        "id": "parse_movement_line",
        "signature": "def parse_movement_line(line: str, case_sizes: Mapping[str, int]) -> Dict[str, Any]:",
        "deps": ["normalize_sku", "parse_location", "parse_quantity"],
        "difficulty": "medium",
        "summary": "Parse a stock movement record into a normalized dict",
        "spec": """Parse one stock movement record.

Records are semicolon-separated: "<day>;<type>;<sku>;<location>;<quantity>",
e.g. "12;RCV;ABC-123456-1;B-07-14-3;5 CS". Whitespace around fields is ignored.

    day       non-negative integer day index
    type      RCV (receipt), SHP (shipment), RTN (customer return) or
              ADJ (inventory adjustment); case-insensitive
    sku       normalized with normalize_sku
    location  parsed with parse_location
    quantity  parsed with parse_quantity, using case_sizes[sku]; SKUs that
              are not in case_sizes have a case size of 1

Returns:
    {"day": int, "type": str, "sku": str, "location": str, "qty": int}
    where type is upper-case, sku is canonical, location is the canonical
    "Z-AA-SS-L" string (two-digit aisle and shelf) and qty is the signed
    change to on-hand stock in eaches: RCV and RTN add stock, SHP removes it
    (the record shows the shipped amount, qty is its negative), ADJ is
    applied as written.

Raises:
    ValueError: wrong number of fields, bad day, unknown type, or any error
        raised by the helpers above.

Example:
    parse_movement_line("12;SHP;abc-123456-1;b-07-14-3;2 CS", {"ABC-123456-1": 6})
        == {"day": 12, "type": "SHP", "sku": "ABC-123456-1",
            "location": "B-07-14-3", "qty": -12}
""",
        "clarification": """Only ADJ records may carry a sign. RCV, SHP and RTN quantities must be
strictly positive as written; a zero or negative quantity on those types is a
data-entry error and raises ValueError (a negative SHP is NOT a return; returns
are booked as RTN). A zero ADJ is rejected as well.""",
        "reference": r'''from stockflow.normalize_sku import normalize_sku
from stockflow.parse_location import parse_location
from stockflow.parse_quantity import parse_quantity


def parse_movement_line(line, case_sizes):
    fields = [field.strip() for field in line.split(";")]
    if len(fields) != 5:
        raise ValueError(f"expected 5 fields, got {len(fields)}")
    day_text, mtype, sku_text, location_text, qty_text = fields
    if not day_text.isdigit():
        raise ValueError(f"bad day index: {day_text!r}")
    mtype = mtype.upper()
    if mtype not in ("RCV", "SHP", "RTN", "ADJ"):
        raise ValueError(f"unknown movement type: {mtype!r}")
    sku = normalize_sku(sku_text)
    zone, aisle, shelf, level = parse_location(location_text)
    amount = parse_quantity(qty_text, case_sizes.get(sku, 1))
    if amount == 0 or (mtype != "ADJ" and amount < 0):
        raise ValueError(f"invalid quantity for {mtype}: {qty_text!r}")
    return {
        "day": int(day_text),
        "type": mtype,
        "sku": sku,
        "location": f"{zone}-{aisle:02d}-{shelf:02d}-{level}",
        "qty": -amount if mtype == "SHP" else amount,
    }
''',
        "naive": r'''from stockflow.normalize_sku import normalize_sku
from stockflow.parse_location import parse_location
from stockflow.parse_quantity import parse_quantity


def parse_movement_line(line, case_sizes):
    fields = [field.strip() for field in line.split(";")]
    if len(fields) != 5:
        raise ValueError(f"expected 5 fields, got {len(fields)}")
    day_text, mtype, sku_text, location_text, qty_text = fields
    if not day_text.isdigit():
        raise ValueError(f"bad day index: {day_text!r}")
    mtype = mtype.upper()
    if mtype not in ("RCV", "SHP", "RTN", "ADJ"):
        raise ValueError(f"unknown movement type: {mtype!r}")
    sku = normalize_sku(sku_text)
    zone, aisle, shelf, level = parse_location(location_text)
    amount = parse_quantity(qty_text, case_sizes.get(sku, 1))
    return {
        "day": int(day_text),
        "type": mtype,
        "sku": sku,
        "location": f"{zone}-{aisle:02d}-{shelf:02d}-{level}",
        "qty": -amount if mtype == "SHP" else amount,
    }
''',
        "unit_tests": r'''import pytest

from stockflow.parse_movement_line import parse_movement_line


def test_example():
    assert parse_movement_line("12;SHP;abc-123456-1;b-07-14-3;2 CS", {"ABC-123456-1": 6}) == {
        "day": 12, "type": "SHP", "sku": "ABC-123456-1", "location": "B-07-14-3", "qty": -12}


def test_unknown_type():
    with pytest.raises(ValueError):
        parse_movement_line("12;XFR;ABC-123456-1;B-07-14-3;1 EA", {})
''',
        "acceptance_tests": r'''import pytest

from stockflow.parse_movement_line import parse_movement_line

SIZES = {"ABC-123456-1": 6, "KIT-200001-3": 24}


def test_parse_records():
    assert parse_movement_line("12;RCV;ABC-123456-1;B-07-14-3;5 CS", SIZES) == {
        "day": 12, "type": "RCV", "sku": "ABC-123456-1", "location": "B-07-14-3", "qty": 30}
    assert parse_movement_line(" 3 ; shp ; kit-200001-3 ; a-01-02-0 ; 7 ea ", SIZES) == {
        "day": 3, "type": "SHP", "sku": "KIT-200001-3", "location": "A-01-02-0", "qty": -7}
    assert parse_movement_line("41;RTN;ABC-123456-1;B-07-14-3;1 CS", SIZES)["qty"] == 6
    assert parse_movement_line("40;ADJ;TEE-104520-4;C-10-03-1;-2 CS", SIZES)["qty"] == -2


def test_quantity_sign_rules():
    with pytest.raises(ValueError):
        parse_movement_line("5;SHP;ABC-123456-1;B-07-14-3;-1 CS", SIZES)
    with pytest.raises(ValueError):
        parse_movement_line("5;RCV;ABC-123456-1;B-07-14-3;0 EA", SIZES)


def test_malformed_records():
    with pytest.raises(ValueError):
        parse_movement_line("5;RCV;ABC-123456-1;1 EA", SIZES)
''',
        "conflicting_test": r'''def test_regression_issue_812():
    assert parse_movement_line("12;RCV;ABC-123456-1;B-07-14-3;5 CS", SIZES) == {
        "day": 12, "type": "RCV", "sku": "ABC-123456-1", "location": "B-07-14-3", "qty": 5}
''',
        "conflict_call": 'parse_movement_line("12;RCV;ABC-123456-1;B-07-14-3;5 CS", SIZES)',
        "oneoff": {"find": '["qty"] == 6', "replace": '["qty"] == -6'},
    },
    # ------------------------------------------------------------------ on_hand_by_location
    {
        "id": "on_hand_by_location",
        "signature": ("def on_hand_by_location(lines: Iterable[str], case_sizes: Mapping[str, int], "
                      "as_of_day: Optional[int] = None) -> Dict[Tuple[str, str], int]:"),
        "deps": ["parse_movement_line"],
        "difficulty": "medium",
        "summary": "Compute on-hand stock per SKU and bin location from movement records",
        "spec": """Current on-hand stock per (SKU, location) from movement records.

Each line is parsed with parse_movement_line, except blank lines and
comment lines (first non-blank character "#"), which are skipped. The signed
quantities are summed per (sku, location), using the canonical SKU and
location strings returned by the parser.

Args:
    lines: movement records (see parse_movement_line).
    case_sizes: passed through to parse_movement_line.
    as_of_day: if given, only movements with day <= as_of_day are counted.

Returns:
    Dict (sku, location) -> eaches on hand.

Raises:
    ValueError: propagated from parse_movement_line for malformed records.

Example:
    on_hand_by_location(["1;RCV;ABC-123456-1;B-07-14-3;10 EA",
                         "2;SHP;ABC-123456-1;B-07-14-3;4 EA"], {})
        == {("ABC-123456-1", "B-07-14-3"): 6}
""",
        "clarification": """Positions that net to exactly zero are dropped from the result: an emptied
bin is not a stock position and must not show up on count sheets or transfer
screens. Negative totals are kept as they are (they flag a missed receipt and
must stay visible).""",
        "reference": r'''from stockflow.parse_movement_line import parse_movement_line


def on_hand_by_location(lines, case_sizes, as_of_day=None):
    totals = {}
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        movement = parse_movement_line(text, case_sizes)
        if as_of_day is not None and movement["day"] > as_of_day:
            continue
        key = (movement["sku"], movement["location"])
        totals[key] = totals.get(key, 0) + movement["qty"]
    return {key: qty for key, qty in totals.items() if qty != 0}
''',
        "naive": r'''from stockflow.parse_movement_line import parse_movement_line


def on_hand_by_location(lines, case_sizes, as_of_day=None):
    totals = {}
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        movement = parse_movement_line(text, case_sizes)
        if as_of_day is not None and movement["day"] > as_of_day:
            continue
        key = (movement["sku"], movement["location"])
        totals[key] = totals.get(key, 0) + movement["qty"]
    return totals
''',
        "unit_tests": r'''from stockflow.on_hand_by_location import on_hand_by_location


def test_example():
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA", "2;SHP;ABC-123456-1;B-07-14-3;4 EA"]
    assert on_hand_by_location(lines, {}) == {("ABC-123456-1", "B-07-14-3"): 6}


def test_comments_and_cutoff():
    lines = ["# header", "", "1;RCV;ABC-123456-1;B-07-14-3;10 EA", "5;SHP;ABC-123456-1;B-07-14-3;4 EA"]
    assert on_hand_by_location(lines, {}, as_of_day=4) == {("ABC-123456-1", "B-07-14-3"): 10}
''',
        "acceptance_tests": r'''import pytest

from stockflow.on_hand_by_location import on_hand_by_location

LINES = [
    "# opening stock",
    "1;RCV;ABC-123456-1;B-07-14-3;2 CS",
    "1;RCV;KIT-200001-3;A-01-02-0;10 EA",
    "",
    "3;SHP;abc-123456-1;b-07-14-3;5 EA",
    "4;ADJ;KIT-200001-3;A-01-02-0;-10 EA",
    "5;SHP;TEE-104520-4;C-10-03-1;3 EA",
    "9;RCV;ABC-123456-1;B-07-14-4;1 CS",
]
SIZES = {"ABC-123456-1": 6}


def test_totals():
    assert on_hand_by_location(LINES, SIZES) == {
        ("ABC-123456-1", "B-07-14-3"): 7,
        ("ABC-123456-1", "B-07-14-4"): 6,
        ("TEE-104520-4", "C-10-03-1"): -3,
    }


def test_as_of_day():
    assert on_hand_by_location(LINES, SIZES, as_of_day=3) == {
        ("ABC-123456-1", "B-07-14-3"): 7,
        ("KIT-200001-3", "A-01-02-0"): 10,
    }
    assert on_hand_by_location(LINES, SIZES, as_of_day=0) == {}


def test_bad_record():
    with pytest.raises(ValueError):
        on_hand_by_location(["1;RCV;ABC-123456-1;B-07-14-3"], SIZES)
''',
        "conflicting_test": r'''def test_regression_issue_118():
    assert on_hand_by_location(LINES, SIZES) == {
        ("ABC-123456-1", "B-07-14-3"): 7,
        ("ABC-123456-1", "B-07-14-4"): 6,
        ("KIT-200001-3", "A-01-02-0"): 0,
        ("TEE-104520-4", "C-10-03-1"): -3,
    }
''',
        "conflict_call": "on_hand_by_location(LINES, SIZES)",
        "oneoff": {"find": '("TEE-104520-4", "C-10-03-1"): -3,', "replace": '("TEE-104520-4", "C-10-03-1"): 3,'},
    },
    # ------------------------------------------------------------------ average_daily_demand
    {
        "id": "average_daily_demand",
        "signature": ("def average_daily_demand(lines: Iterable[str], case_sizes: Mapping[str, int], sku: str, "
                      "start_day: int, end_day: int) -> int:"),
        "deps": ["parse_movement_line"],
        "difficulty": "easy",
        "summary": "Compute a SKU's average daily demand over a day range",
        "spec": """Average daily demand for one SKU over a range of days, in whole eaches.

Movement records are parsed with parse_movement_line (blank lines and "#"
comment lines are skipped). Shipments (SHP) of `sku` dated start_day ..
end_day (both inclusive) are totalled and divided by the number of days in
the range; the result is rounded up to a whole each.

Args:
    lines: movement records.
    case_sizes: passed through to parse_movement_line.
    sku: canonical SKU.
    start_day, end_day: inclusive day range.

Raises:
    ValueError: if end_day < start_day, or for malformed records.

Example:
    lines = ["1;SHP;ABC-123456-1;B-07-14-3;7 EA", "2;SHP;ABC-123456-1;A-01-01-1;3 EA"]
    average_daily_demand(lines, {}, "ABC-123456-1", 1, 4) == 3     # 10 / 4 = 2.5 -> 3
""",
        "clarification": """Demand is net of customer returns: RTN records of the SKU in the same day
range are subtracted from the shipped total before averaging. If returns exceed
shipments the demand is 0, never negative.""",
        "reference": r'''from stockflow.parse_movement_line import parse_movement_line


def average_daily_demand(lines, case_sizes, sku, start_day, end_day):
    if end_day < start_day:
        raise ValueError("end_day is before start_day")
    net = 0
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        movement = parse_movement_line(text, case_sizes)
        if movement["sku"] != sku or not start_day <= movement["day"] <= end_day:
            continue
        if movement["type"] == "SHP":
            net -= movement["qty"]
        elif movement["type"] == "RTN":
            net -= movement["qty"]
    if net <= 0:
        return 0
    days = end_day - start_day + 1
    return -(-net // days)
''',
        "naive": r'''from stockflow.parse_movement_line import parse_movement_line


def average_daily_demand(lines, case_sizes, sku, start_day, end_day):
    if end_day < start_day:
        raise ValueError("end_day is before start_day")
    shipped = 0
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        movement = parse_movement_line(text, case_sizes)
        if movement["sku"] != sku or not start_day <= movement["day"] <= end_day:
            continue
        if movement["type"] == "SHP":
            shipped -= movement["qty"]
    days = end_day - start_day + 1
    return -(-shipped // days)
''',
        "unit_tests": r'''import pytest

from stockflow.average_daily_demand import average_daily_demand


def test_example():
    lines = ["1;SHP;ABC-123456-1;B-07-14-3;7 EA", "2;SHP;ABC-123456-1;A-01-01-1;3 EA"]
    assert average_daily_demand(lines, {}, "ABC-123456-1", 1, 4) == 3
    assert average_daily_demand([], {}, "ABC-123456-1", 1, 4) == 0


def test_bad_range():
    with pytest.raises(ValueError):
        average_daily_demand([], {}, "ABC-123456-1", 4, 1)
''',
        "acceptance_tests": r'''import pytest

from stockflow.average_daily_demand import average_daily_demand

LINES = [
    "1;SHP;ABC-123456-1;B-07-14-3;7 EA",
    "2;SHP;ABC-123456-1;A-01-01-1;1 CS",
    "2;RCV;ABC-123456-1;B-07-14-3;5 CS",
    "# day 3",
    "3;RTN;ABC-123456-1;B-07-14-3;4 EA",
    "5;SHP;KIT-200001-3;A-01-01-1;9 EA",
    "8;SHP;ABC-123456-1;B-07-14-3;2 EA",
]
SIZES = {"ABC-123456-1": 6}


def test_window():
    assert average_daily_demand(LINES, SIZES, "KIT-200001-3", 1, 10) == 1
    assert average_daily_demand(LINES, SIZES, "ABC-123456-1", 4, 8) == 1
    assert average_daily_demand(LINES, SIZES, "TEE-104520-4", 1, 30) == 0


def test_returns():
    assert average_daily_demand(LINES, SIZES, "ABC-123456-1", 1, 4) == 3
    assert average_daily_demand(LINES, SIZES, "ABC-123456-1", 3, 3) == 0


def test_bad_range():
    with pytest.raises(ValueError):
        average_daily_demand(LINES, SIZES, "ABC-123456-1", 5, 4)
''',
        "conflicting_test": r'''def test_regression_issue_275():
    assert average_daily_demand(LINES, SIZES, "ABC-123456-1", 1, 4) == 4
''',
        "conflict_call": 'average_daily_demand(LINES, SIZES, "ABC-123456-1", 1, 4)',
        "oneoff": {"find": '"KIT-200001-3", 1, 10) == 1', "replace": '"KIT-200001-3", 1, 10) == 0'},
    },
    # ------------------------------------------------------------------ dead_stock
    {
        "id": "dead_stock",
        "signature": ("def dead_stock(lines: Iterable[str], case_sizes: Mapping[str, int], today: int, "
                      "idle_days: int) -> List[str]:"),
        "deps": ["parse_movement_line", "on_hand_by_location"],
        "difficulty": "medium",
        "summary": "Find SKUs with stock on hand that have not shipped for a long time",
        "spec": """List SKUs whose stock has not moved out for a long time (dead stock).

A SKU is dead stock when its total on-hand (summed over all locations with
on_hand_by_location, counting movements up to and including `today`) is
positive and its most recent shipment (SHP) is at least `idle_days` days old,
i.e. today - last_ship_day >= idle_days. Movements dated after `today` are
ignored. Blank lines and "#" comment lines are skipped.

Args:
    lines: movement records; any iterable (it is only iterated once).
    case_sizes: passed through to the parsers.
    today: current day index.
    idle_days: threshold in days, >= 1.

Returns:
    Sorted list of canonical SKUs.

Raises:
    ValueError: if idle_days < 1, or for malformed records.

Example:
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA", "5;SHP;ABC-123456-1;B-07-14-3;2 EA"]
    dead_stock(lines, {}, today=40, idle_days=30) == ["ABC-123456-1"]
""",
        "clarification": """A SKU that has never shipped (as of today) is measured from its earliest
movement of any type instead, normally its first receipt: a product that
arrived last week is new, not dead.""",
        "reference": r'''from stockflow.on_hand_by_location import on_hand_by_location
from stockflow.parse_movement_line import parse_movement_line


def dead_stock(lines, case_sizes, today, idle_days):
    if idle_days < 1:
        raise ValueError("idle_days must be >= 1")
    records = [line for line in lines if line.strip() and not line.strip().startswith("#")]
    totals = {}
    for (sku, _location), qty in on_hand_by_location(records, case_sizes, as_of_day=today).items():
        totals[sku] = totals.get(sku, 0) + qty
    last_ship = {}
    first_seen = {}
    for line in records:
        movement = parse_movement_line(line, case_sizes)
        day, sku = movement["day"], movement["sku"]
        if day > today:
            continue
        first_seen[sku] = min(first_seen.get(sku, day), day)
        if movement["type"] == "SHP":
            last_ship[sku] = max(last_ship.get(sku, day), day)
    dead = []
    for sku, qty in totals.items():
        since = last_ship.get(sku, first_seen[sku])
        if qty > 0 and today - since >= idle_days:
            dead.append(sku)
    return sorted(dead)
''',
        "naive": r'''from stockflow.on_hand_by_location import on_hand_by_location
from stockflow.parse_movement_line import parse_movement_line


def dead_stock(lines, case_sizes, today, idle_days):
    if idle_days < 1:
        raise ValueError("idle_days must be >= 1")
    records = [line for line in lines if line.strip() and not line.strip().startswith("#")]
    totals = {}
    for (sku, _location), qty in on_hand_by_location(records, case_sizes, as_of_day=today).items():
        totals[sku] = totals.get(sku, 0) + qty
    last_ship = {}
    for line in records:
        movement = parse_movement_line(line, case_sizes)
        if movement["day"] <= today and movement["type"] == "SHP":
            sku = movement["sku"]
            last_ship[sku] = max(last_ship.get(sku, movement["day"]), movement["day"])
    dead = []
    for sku, qty in totals.items():
        if qty <= 0:
            continue
        if sku not in last_ship or today - last_ship[sku] >= idle_days:
            dead.append(sku)
    return sorted(dead)
''',
        "unit_tests": r'''import pytest

from stockflow.dead_stock import dead_stock


def test_example():
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA", "5;SHP;ABC-123456-1;B-07-14-3;2 EA"]
    assert dead_stock(lines, {}, today=40, idle_days=30) == ["ABC-123456-1"]
    assert dead_stock(lines, {}, today=20, idle_days=30) == []


def test_bad_threshold():
    with pytest.raises(ValueError):
        dead_stock([], {}, today=40, idle_days=0)
''',
        "acceptance_tests": r'''import pytest

from stockflow.dead_stock import dead_stock

LINES = [
    "1;RCV;ABC-123456-1;B-07-14-3;10 EA",
    "1;RCV;KIT-200001-3;A-01-02-0;4 EA",
    "5;SHP;ABC-123456-1;B-07-14-3;2 EA",
    "10;SHP;KIT-200001-3;A-01-02-0;4 EA",
    "20;RCV;TEE-104520-4;C-10-03-1;6 EA",
    "30;RCV;MUG-300300-8;C-10-04-1;1 CS",
    "50;SHP;MUG-300300-8;C-10-04-1;1 EA",
]
SIZES = {"MUG-300300-8": 12}


def test_idle_skus():
    assert dead_stock(LINES, SIZES, today=40, idle_days=30) == ["ABC-123456-1"]
    assert dead_stock(LINES, SIZES, today=60, idle_days=30) == ["ABC-123456-1", "TEE-104520-4"]


def test_threshold_boundary():
    assert dead_stock(LINES, SIZES, today=34, idle_days=30) == []
    assert dead_stock(LINES, SIZES, today=35, idle_days=30) == ["ABC-123456-1"]


def test_iterator_input_and_errors():
    assert dead_stock(iter(LINES), SIZES, today=60, idle_days=45) == ["ABC-123456-1"]
    with pytest.raises(ValueError):
        dead_stock(LINES, SIZES, today=60, idle_days=0)
''',
        "conflicting_test": r'''def test_regression_issue_349():
    assert dead_stock(LINES, SIZES, today=40, idle_days=30) == ["ABC-123456-1", "MUG-300300-8", "TEE-104520-4"]
''',
        "conflict_call": "dead_stock(LINES, SIZES, today=40, idle_days=30)",
        "oneoff": {"find": "today=34, idle_days=30) == []", "replace": 'today=34, idle_days=30) == ["ABC-123456-1"]'},
    },
    # ------------------------------------------------------------------ cycle_count_variance
    {
        "id": "cycle_count_variance",
        "signature": ("def cycle_count_variance(lines: Iterable[str], case_sizes: Mapping[str, int], "
                      "counts: Mapping[Tuple[str, str], int]) -> List[Tuple[str, str, int]]:"),
        "deps": ["on_hand_by_location", "normalize_sku", "parse_location"],
        "difficulty": "hard",
        "summary": "Report differences between a cycle count and system stock",
        "spec": """Compare a cycle count with system stock and report the differences.

System stock is on_hand_by_location(lines, case_sizes). `counts` holds what
the counters recorded, keyed by (sku, location) as typed on the handheld;
keys are normalized with normalize_sku and parse_location (canonical
"Z-AA-SS-L" location string) before matching, and the quantities of keys
that normalize to the same position are added together.

    variance = counted qty - system qty

Returns:
    List of (sku, location, variance) for every position with a non-zero
    variance, sorted by location, then SKU.

Raises:
    ValueError: if a counted quantity is negative, or from the parsers.

Example:
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA"]
    cycle_count_variance(lines, {}, {("abc-123456-1", "b-07-14-3"): 8})
        == [("ABC-123456-1", "B-07-14-3", -2)]
""",
        "clarification": """A count covers the whole bin. If a location appears in `counts`, every system
position in that location whose SKU was not counted is treated as counted 0
(variance = -system qty). Locations that were not counted at all are ignored,
even if they hold stock.""",
        "reference": r'''from stockflow.normalize_sku import normalize_sku
from stockflow.on_hand_by_location import on_hand_by_location
from stockflow.parse_location import parse_location


def cycle_count_variance(lines, case_sizes, counts):
    counted = {}
    for (raw_sku, raw_location), qty in counts.items():
        if qty < 0:
            raise ValueError("counted quantity cannot be negative")
        zone, aisle, shelf, level = parse_location(raw_location)
        key = (normalize_sku(raw_sku), f"{zone}-{aisle:02d}-{shelf:02d}-{level}")
        counted[key] = counted.get(key, 0) + qty
    system = on_hand_by_location(lines, case_sizes)
    counted_locations = {location for _sku, location in counted}
    keys = set(counted) | {key for key in system if key[1] in counted_locations}
    report = []
    for sku, location in keys:
        variance = counted.get((sku, location), 0) - system.get((sku, location), 0)
        if variance != 0:
            report.append((sku, location, variance))
    report.sort(key=lambda row: (row[1], row[0]))
    return report
''',
        "naive": r'''from stockflow.normalize_sku import normalize_sku
from stockflow.on_hand_by_location import on_hand_by_location
from stockflow.parse_location import parse_location


def cycle_count_variance(lines, case_sizes, counts):
    counted = {}
    for (raw_sku, raw_location), qty in counts.items():
        if qty < 0:
            raise ValueError("counted quantity cannot be negative")
        zone, aisle, shelf, level = parse_location(raw_location)
        key = (normalize_sku(raw_sku), f"{zone}-{aisle:02d}-{shelf:02d}-{level}")
        counted[key] = counted.get(key, 0) + qty
    system = on_hand_by_location(lines, case_sizes)
    report = []
    for (sku, location), qty in counted.items():
        variance = qty - system.get((sku, location), 0)
        if variance != 0:
            report.append((sku, location, variance))
    report.sort(key=lambda row: (row[1], row[0]))
    return report
''',
        "unit_tests": r'''from stockflow.cycle_count_variance import cycle_count_variance


def test_example():
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA"]
    assert cycle_count_variance(lines, {}, {("abc-123456-1", "b-07-14-3"): 8}) == [("ABC-123456-1", "B-07-14-3", -2)]


def test_clean_count():
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA"]
    assert cycle_count_variance(lines, {}, {("ABC-123456-1", "B-07-14-3"): 10}) == []
''',
        "acceptance_tests": r'''import pytest

from stockflow.cycle_count_variance import cycle_count_variance

LINES = [
    "1;RCV;ABC-123456-1;B-07-14-3;2 CS",
    "1;RCV;KIT-200001-3;B-07-14-3;5 EA",
    "1;RCV;TEE-104520-4;A-02-01-1;9 EA",
    "2;RCV;MUG-300300-8;C-10-04-1;4 EA",
    "3;SHP;MUG-300300-8;C-10-04-1;6 EA",
]
SIZES = {"ABC-123456-1": 6}


def test_counted_bins():
    assert cycle_count_variance(LINES, SIZES, {("ABC-123456-1", "B-07-14-3"): 12, ("tee-104520-4", "a-02-01-1"): 7}) == [
        ("TEE-104520-4", "A-02-01-1", -2), ("KIT-200001-3", "B-07-14-3", -5)]


def test_merged_keys_and_found_stock():
    counts = {("MUG-300300-8", "C-10-04-1"): 1, ("mug-300300-8", "c-10-04-1"): 1, ("ABC-123456-1", "A-02-01-1"): 3}
    assert cycle_count_variance(LINES, SIZES, counts) == [
        ("ABC-123456-1", "A-02-01-1", 3), ("TEE-104520-4", "A-02-01-1", -9), ("MUG-300300-8", "C-10-04-1", 4)]


def test_clean_count_and_errors():
    assert cycle_count_variance(LINES, SIZES, {("TEE-104520-4", "A-02-01-1"): 9}) == []
    assert cycle_count_variance(LINES, SIZES, {}) == []
    with pytest.raises(ValueError):
        cycle_count_variance(LINES, SIZES, {("TEE-104520-4", "A-02-01-1"): -1})
''',
        "conflicting_test": r'''def test_regression_issue_906():
    assert cycle_count_variance(LINES, SIZES, {("ABC-123456-1", "B-07-14-3"): 12, ("tee-104520-4", "a-02-01-1"): 7}) == [
        ("TEE-104520-4", "A-02-01-1", -2)]
''',
        "conflict_call": ('cycle_count_variance(LINES, SIZES, {("ABC-123456-1", "B-07-14-3"): 12, '
                          '("tee-104520-4", "a-02-01-1"): 7})'),
        "oneoff": {"find": '("MUG-300300-8", "C-10-04-1", 4)', "replace": '("MUG-300300-8", "C-10-04-1", 2)'},
    },
    # ------------------------------------------------------------------ validate_transfer
    {
        "id": "validate_transfer",
        "signature": ("def validate_transfer(lines: Iterable[str], case_sizes: Mapping[str, int], sku: str, "
                      "from_location: str, to_location: str, qty: int, day: int) -> List[str]:"),
        "deps": ["on_hand_by_location", "parse_location"],
        "difficulty": "medium",
        "summary": "Validate a bin-to-bin stock transfer and list the problems",
        "spec": """Check a proposed bin-to-bin transfer and list what is wrong with it.

Args:
    lines: movement records used to work out stock (see on_hand_by_location).
    case_sizes: passed through to the parsers.
    sku: canonical SKU to move.
    from_location, to_location: location codes, parsed with parse_location
        (a malformed code raises ValueError).
    qty: eaches to move.
    day: day index the transfer is executed on.

Returns:
    List of problem codes in this order, empty if the transfer is fine:
        "BAD_QTY"             qty <= 0
        "SAME_LOCATION"       both codes refer to the same bin
        "INSUFFICIENT_STOCK"  qty > 0 and the SKU's on-hand at from_location
                              is less than qty (no position counts as 0)

Example:
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA"]
    validate_transfer(lines, {}, "ABC-123456-1", "B-07-14-3", "b-07-14-3", 0, day=2)
        == ["BAD_QTY", "SAME_LOCATION"]
""",
        "clarification": """Movements are posted overnight: records dated on the transfer day itself are
not in the books yet and must not count toward the available stock. Only
movements with day < `day` count.""",
        "reference": r'''from stockflow.on_hand_by_location import on_hand_by_location
from stockflow.parse_location import parse_location


def validate_transfer(lines, case_sizes, sku, from_location, to_location, qty, day):
    source = parse_location(from_location)
    target = parse_location(to_location)
    problems = []
    if qty <= 0:
        problems.append("BAD_QTY")
    if source == target:
        problems.append("SAME_LOCATION")
    if qty > 0:
        stock = on_hand_by_location(lines, case_sizes, as_of_day=day - 1)
        zone, aisle, shelf, level = source
        key = (sku, f"{zone}-{aisle:02d}-{shelf:02d}-{level}")
        if stock.get(key, 0) < qty:
            problems.append("INSUFFICIENT_STOCK")
    return problems
''',
        "naive": r'''from stockflow.on_hand_by_location import on_hand_by_location
from stockflow.parse_location import parse_location


def validate_transfer(lines, case_sizes, sku, from_location, to_location, qty, day):
    source = parse_location(from_location)
    target = parse_location(to_location)
    problems = []
    if qty <= 0:
        problems.append("BAD_QTY")
    if source == target:
        problems.append("SAME_LOCATION")
    if qty > 0:
        stock = on_hand_by_location(lines, case_sizes, as_of_day=day)
        zone, aisle, shelf, level = source
        key = (sku, f"{zone}-{aisle:02d}-{shelf:02d}-{level}")
        if stock.get(key, 0) < qty:
            problems.append("INSUFFICIENT_STOCK")
    return problems
''',
        "unit_tests": r'''from stockflow.validate_transfer import validate_transfer


def test_example():
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA"]
    assert validate_transfer(lines, {}, "ABC-123456-1", "B-07-14-3", "b-07-14-3", 0, day=2) == ["BAD_QTY", "SAME_LOCATION"]


def test_valid_transfer():
    lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA"]
    assert validate_transfer(lines, {}, "ABC-123456-1", "B-07-14-3", "B-07-15-1", 10, day=2) == []
''',
        "acceptance_tests": r'''import pytest

from stockflow.validate_transfer import validate_transfer

LINES = [
    "1;RCV;ABC-123456-1;B-07-14-3;2 CS",
    "4;SHP;ABC-123456-1;B-07-14-3;5 EA",
    "6;RCV;ABC-123456-1;B-07-14-3;1 CS",
    "6;RCV;KIT-200001-3;A-01-02-0;8 EA",
]
SIZES = {"ABC-123456-1": 6}


def test_valid_moves():
    assert validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14-3", "B-07-15-1", 7, day=5) == []
    assert validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14-3", "B-07-14-4", 13, day=7) == []


def test_problems():
    assert validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14-3", "b-07-14-3", -1, day=2) == [
        "BAD_QTY", "SAME_LOCATION"]
    assert validate_transfer(LINES, SIZES, "KIT-200001-3", "B-07-14-3", "A-01-02-0", 1, day=9) == ["INSUFFICIENT_STOCK"]


def test_same_day_movements():
    assert validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14-3", "B-07-15-1", 10, day=6) == ["INSUFFICIENT_STOCK"]
    assert validate_transfer(LINES, SIZES, "KIT-200001-3", "A-01-02-0", "A-01-03-0", 8, day=6) == ["INSUFFICIENT_STOCK"]


def test_bad_location():
    with pytest.raises(ValueError):
        validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14", "B-07-15-1", 1, day=5)
''',
        "conflicting_test": r'''def test_regression_issue_157():
    assert validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14-3", "B-07-15-1", 10, day=6) == []
''',
        "conflict_call": 'validate_transfer(LINES, SIZES, "ABC-123456-1", "B-07-14-3", "B-07-15-1", 10, day=6)',
        "oneoff": {"find": '"B-07-14-4", 13, day=7) == []', "replace": '"B-07-14-4", 13, day=7) == ["INSUFFICIENT_STOCK"]'},
    },
    # ------------------------------------------------------------------ pick_route_order
    {
        "id": "pick_route_order",
        "signature": "def pick_route_order(picks: Sequence[Tuple[str, str, int]]) -> List[Tuple[str, str, int]]:",
        "deps": ["parse_location"],
        "difficulty": "medium",
        "summary": "Sort pick lines into the picker's walking order",
        "spec": """Order pick lines along the picker's walking route.

Args:
    picks: (sku, location, qty) tuples; locations are parsed with
        parse_location (a malformed code raises ValueError).

Returns:
    The same tuples, unchanged, reordered for walking: by zone
    (alphabetical), then aisle (ascending), then by shelf position along the
    aisle, then level (ascending). Picks at the same bin keep their input
    order.

Example:
    pick_route_order([("S2", "A-01-05-1", 1), ("S1", "A-01-02-1", 3)])
        == [("S1", "A-01-02-1", 3), ("S2", "A-01-05-1", 1)]
""",
        "clarification": """Pickers walk the aisles in a serpentine (S-shaped) path: up the odd-numbered
aisles and back down the even-numbered ones. Shelves are therefore visited in
ascending order in odd aisles and in DESCENDING order in even aisles. Levels
within a shelf are always ascending.""",
        "reference": r'''from stockflow.parse_location import parse_location


def pick_route_order(picks):
    def route_key(pick):
        zone, aisle, shelf, level = parse_location(pick[1])
        along = shelf if aisle % 2 == 1 else -shelf
        return (zone, aisle, along, level)

    return sorted(picks, key=route_key)
''',
        "naive": r'''from stockflow.parse_location import parse_location


def pick_route_order(picks):
    def route_key(pick):
        zone, aisle, shelf, level = parse_location(pick[1])
        return (zone, aisle, shelf, level)

    return sorted(picks, key=route_key)
''',
        "unit_tests": r'''from stockflow.pick_route_order import pick_route_order


def test_example():
    picks = [("S2", "A-01-05-1", 1), ("S1", "A-01-02-1", 3)]
    assert pick_route_order(picks) == [("S1", "A-01-02-1", 3), ("S2", "A-01-05-1", 1)]


def test_empty():
    assert pick_route_order([]) == []
''',
        "acceptance_tests": r'''import pytest

from stockflow.pick_route_order import pick_route_order


def test_single_aisle():
    picks = [("S2", "A-01-05-1", 1), ("S1", "A-01-02-1", 3), ("S3", "A-01-02-0", 2)]
    assert pick_route_order(picks) == [("S3", "A-01-02-0", 2), ("S1", "A-01-02-1", 3), ("S2", "A-01-05-1", 1)]


def test_route_through_aisles():
    picks = [
        ("P1", "A-02-03-1", 1),
        ("P2", "A-01-09-1", 1),
        ("P3", "A-02-11-2", 1),
        ("P4", "B-01-01-1", 1),
        ("P5", "a-01-04-1", 1),
    ]
    assert [p[0] for p in pick_route_order(picks)] == ["P5", "P2", "P3", "P1", "P4"]
    assert pick_route_order([("X", "C-04-01-1", 2), ("Y", "C-04-20-1", 1)]) == [("Y", "C-04-20-1", 1), ("X", "C-04-01-1", 2)]


def test_same_bin_and_errors():
    picks = [("K2", "A-03-03-1", 1), ("K1", "A-03-03-1", 5)]
    assert pick_route_order(picks) == picks
    with pytest.raises(ValueError):
        pick_route_order([("Z", "A-3-03-1", 1)])
''',
        "conflicting_test": r'''def test_regression_issue_642():
    assert pick_route_order([("X", "C-04-01-1", 2), ("Y", "C-04-20-1", 1)]) == [("X", "C-04-01-1", 2), ("Y", "C-04-20-1", 1)]
''',
        "conflict_call": 'pick_route_order([("X", "C-04-01-1", 2), ("Y", "C-04-20-1", 1)])',
        "oneoff": {"find": '== ["P5", "P2", "P3", "P1", "P4"]', "replace": '== ["P2", "P5", "P3", "P1", "P4"]'},
    },
    # ------------------------------------------------------------------ replenishment_suggestions
    {
        "id": "replenishment_suggestions",
        "signature": "def replenishment_suggestions(items: Sequence[Mapping[str, Any]]) -> List[Tuple[str, int]]:",
        "deps": ["reorder_point", "economic_order_quantity"],
        "difficulty": "hard",
        "summary": "Suggest purchase orders for SKUs at or below their reorder point",
        "spec": """Suggest purchase orders for SKUs that have reached their reorder point.

Each item is a mapping with the keys
    "sku", "on_hand", "on_order"          SKU string and ints
    "daily_demand", "lead_times"          histories for reorder_point
    "review_period_days"                  optional, default 0
    "annual_demand", "order_cost_cents",
    "holding_cost_cents", "pack_size"     inputs for economic_order_quantity

Inventory position = on_hand + on_order. An item needs a purchase order when
its inventory position is at or below its reorder point
(reorder_point(daily_demand, lead_times, review_period_days)). The suggested
quantity is based on the item's economic order quantity.

Returns:
    List of (sku, qty) for the items that need ordering, sorted by SKU.

Example:
    item = {"sku": "ABC-123456-1", "on_hand": 50, "on_order": 0,
            "daily_demand": [10, 10], "lead_times": [5],
            "annual_demand": 3650, "order_cost_cents": 1000,
            "holding_cost_cents": 200, "pack_size": 10}
    replenishment_suggestions([item]) == [("ABC-123456-1", 190)]
""",
        "clarification": """The EOQ is a floor, not a fixed amount: if inventory position + EOQ would
still be at or below the reorder point, order instead the smallest number of
whole packs (rounded UP, not with round_to_pack) that lifts the inventory
position above the reorder point.""",
        "reference": r'''from stockflow.economic_order_quantity import economic_order_quantity
from stockflow.reorder_point import reorder_point


def replenishment_suggestions(items):
    suggestions = []
    for item in items:
        position = item["on_hand"] + item["on_order"]
        rop = reorder_point(item["daily_demand"], item["lead_times"], item.get("review_period_days", 0))
        if position > rop:
            continue
        pack = item["pack_size"]
        qty = economic_order_quantity(
            item["annual_demand"], item["order_cost_cents"], item["holding_cost_cents"], pack)
        if position + qty <= rop:
            shortfall = rop - position + 1
            qty = -(-shortfall // pack) * pack
        suggestions.append((item["sku"], qty))
    suggestions.sort()
    return suggestions
''',
        "naive": r'''from stockflow.economic_order_quantity import economic_order_quantity
from stockflow.reorder_point import reorder_point


def replenishment_suggestions(items):
    suggestions = []
    for item in items:
        position = item["on_hand"] + item["on_order"]
        rop = reorder_point(item["daily_demand"], item["lead_times"], item.get("review_period_days", 0))
        if position > rop:
            continue
        qty = economic_order_quantity(
            item["annual_demand"], item["order_cost_cents"], item["holding_cost_cents"], item["pack_size"])
        suggestions.append((item["sku"], qty))
    suggestions.sort()
    return suggestions
''',
        "unit_tests": r'''from stockflow.replenishment_suggestions import replenishment_suggestions


def make_item(on_hand):
    return {"sku": "ABC-123456-1", "on_hand": on_hand, "on_order": 0,
            "daily_demand": [10, 10], "lead_times": [5], "annual_demand": 3650,
            "order_cost_cents": 1000, "holding_cost_cents": 200, "pack_size": 10}


def test_example():
    assert replenishment_suggestions([make_item(50)]) == [("ABC-123456-1", 190)]


def test_enough_stock():
    assert replenishment_suggestions([make_item(51)]) == []
''',
        "acceptance_tests": r'''from stockflow.replenishment_suggestions import replenishment_suggestions


def make_item(sku, on_hand, on_order=0, **overrides):
    item = {"sku": sku, "on_hand": on_hand, "on_order": on_order,
            "daily_demand": [10, 10], "lead_times": [5], "annual_demand": 3650,
            "order_cost_cents": 1000, "holding_cost_cents": 200, "pack_size": 10}
    item.update(overrides)
    return item


def test_trigger():
    items = [make_item("TEE-104520-4", 51), make_item("KIT-200001-3", 10), make_item("ABC-123456-1", 30, on_order=20)]
    assert replenishment_suggestions(items) == [("ABC-123456-1", 190), ("KIT-200001-3", 190)]
    assert replenishment_suggestions([make_item("MUG-300300-8", 60, review_period_days=2)]) == [("MUG-300300-8", 190)]


def test_large_gap_is_covered():
    item = make_item("BAG-987654-9", 0, daily_demand=[100, 100], lead_times=[10],
                     annual_demand=400, order_cost_cents=100, holding_cost_cents=100)
    assert replenishment_suggestions([item]) == [("BAG-987654-9", 1010)]
    assert replenishment_suggestions([dict(item, on_hand=970)]) == [("BAG-987654-9", 40)]


def test_nothing_to_order():
    assert replenishment_suggestions([]) == []
    assert replenishment_suggestions([make_item("TEE-104520-4", 40, on_order=11)]) == []
''',
        "conflicting_test": r'''def test_regression_issue_588():
    item = make_item("BAG-987654-9", 0, daily_demand=[100, 100], lead_times=[10],
                     annual_demand=400, order_cost_cents=100, holding_cost_cents=100)
    assert replenishment_suggestions([item]) == [("BAG-987654-9", 30)]
''',
        "conflict_call": "replenishment_suggestions([item])",
        "oneoff": {"find": '[dict(item, on_hand=970)]) == [("BAG-987654-9", 40)]',
                   "replace": '[dict(item, on_hand=970)]) == [("BAG-987654-9", 30)]'},
    },
]
