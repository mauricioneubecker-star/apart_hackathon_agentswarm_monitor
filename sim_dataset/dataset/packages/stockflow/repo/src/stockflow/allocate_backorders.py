from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def allocate_backorders(orders: Sequence[Tuple[str, int, int, Mapping[str, int]]], available: Mapping[str, int]) -> Dict[str, Dict[str, int]]:
    """
    Allocate available stock to open customer backorders.

    Args:
        orders: (order_id, priority, order_day, lines) tuples, where lines maps
            SKU -> backordered eaches. Priority 1 is the most urgent; larger
            numbers are less urgent.
        available: SKU -> eaches available to promise. SKUs that are missing
            have 0 available.

    Orders are served one after another in this sequence: priority ascending,
    then order_day ascending, then order_id ascending. Stock handed to one
    order is no longer available to the orders after it.

    Returns:
        Dict order_id -> {sku: allocated eaches} with an entry for every order and
        every SKU on its lines (0 where nothing was allocated). The inputs are not
        modified.

    Raises:
        ValueError: on a duplicate order_id or a line qty <= 0.

    Example:
        allocate_backorders([("o1", 2, 10, {"S": 5}), ("o2", 1, 12, {"S": 4})], {"S": 4})
            == {"o1": {"S": 0}, "o2": {"S": 4}}
    """
    raise NotImplementedError
