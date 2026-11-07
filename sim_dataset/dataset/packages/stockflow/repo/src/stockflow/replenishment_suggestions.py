from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def replenishment_suggestions(items: Sequence[Mapping[str, Any]]) -> List[Tuple[str, int]]:
    """
    Suggest purchase orders for SKUs that have reached their reorder point.

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
    """
    raise NotImplementedError
