from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def stock_valuation(on_hand: Mapping[str, int], cost_layers: Mapping[str, Sequence[Tuple[int, int]]]) -> Tuple[List[Tuple[str, int, int, int]], int]:
    """
    Value on-hand stock at weighted average cost.

    Args:
        on_hand: SKU -> eaches on hand. Keys may be in any format accepted by
            normalize_sku; quantities of keys that normalize to the same SKU are
            added together.
        cost_layers: canonical SKU -> list of (qty, unit_cost_cents) layers,
            averaged with weighted_average_cost.

    Returns:
        (rows, total_cents). rows is a list of (sku, qty, unit_cost_cents,
        value_cents) with value = qty * unit cost, sorted by value descending,
        then SKU ascending; total_cents is the sum of the row values.

    Raises:
        KeyError: if a SKU that has to be valued has no entry in cost_layers.
        ValueError: from normalize_sku or weighted_average_cost.

    Example:
        stock_valuation({"abc-123456-1": 10}, {"ABC-123456-1": [(5, 200), (5, 300)]})
            == ([("ABC-123456-1", 10, 250, 2500)], 2500)
    """
    raise NotImplementedError
