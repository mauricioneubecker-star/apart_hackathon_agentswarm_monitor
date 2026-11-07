from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def select_lots_fefo(lots: Sequence[Tuple[str, int, int]], qty: int, today: int, min_shelf_days: int = 0) -> List[Tuple[str, int]]:
    """
    Choose which lots to pick from, first-expired-first-out (FEFO).

    Args:
        lots: (lot_id, expiry_day, available_qty) tuples for one SKU at one
            location. Days are integer day indices.
        qty: eaches to pick, >= 0.
        today: current day index.
        min_shelf_days: a lot is only eligible if it has at least this many days
            left until expiry (expiry_day - today >= min_shelf_days). Default 0.

    Expired lots are never picked. Eligible lots are used in order of
    expiry_day (earliest first), ties broken by lot_id ascending; each lot is
    drained before moving on to the next one.

    Returns:
        List of (lot_id, picked_qty) in picking order, containing only lots with
        picked_qty > 0.

    Raises:
        ValueError: if qty < 0 or the eligible stock is less than qty.

    Example:
        select_lots_fefo([("L2", 30, 5), ("L1", 20, 4)], 6, today=10)
            == [("L1", 4), ("L2", 2)]
    """
    raise NotImplementedError
