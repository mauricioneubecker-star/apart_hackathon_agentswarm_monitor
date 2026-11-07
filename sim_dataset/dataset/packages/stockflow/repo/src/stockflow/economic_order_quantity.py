from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def economic_order_quantity(annual_demand: int, order_cost_cents: int, holding_cost_cents: int, pack_size: int = 1) -> int:
    """
    Economic order quantity (EOQ), rounded to supplier packs.

        raw EOQ = floor(sqrt(2 * annual_demand * order_cost_cents / holding_cost_cents))

    computed with integer arithmetic, then rounded to whole packs with
    round_to_pack(raw, pack_size).

    Args:
        annual_demand: units per year, >= 0.
        order_cost_cents: fixed cost of placing one purchase order, >= 0.
        holding_cost_cents: cost of holding one unit for a year, > 0.
        pack_size: supplier pack size, >= 1.

    Returns:
        Order quantity in eaches; 0 when annual_demand is 0.

    Raises:
        ValueError: on negative demand or order cost, holding cost <= 0, or
            pack_size < 1.

    Example:
        economic_order_quantity(1200, 5000, 300) == 200
    """
    raise NotImplementedError
