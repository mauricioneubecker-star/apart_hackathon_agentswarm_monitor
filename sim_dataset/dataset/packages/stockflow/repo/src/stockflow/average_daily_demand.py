from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def average_daily_demand(lines: Iterable[str], case_sizes: Mapping[str, int], sku: str, start_day: int, end_day: int) -> int:
    """
    Average daily demand for one SKU over a range of days, in whole eaches.

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
    """
    raise NotImplementedError
