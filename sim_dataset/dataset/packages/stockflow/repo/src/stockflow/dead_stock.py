from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def dead_stock(lines: Iterable[str], case_sizes: Mapping[str, int], today: int, idle_days: int) -> List[str]:
    """
    List SKUs whose stock has not moved out for a long time (dead stock).

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
    """
    raise NotImplementedError
