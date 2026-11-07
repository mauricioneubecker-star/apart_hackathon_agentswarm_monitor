from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def weighted_average_cost(layers: Sequence[Tuple[int, int]]) -> int:
    """
    Weighted average unit cost of a set of cost layers, in whole cents.

    Each layer is (quantity, unit_cost_cents). The result is the total cost of
    all layers divided by the total quantity, rounded to the nearest cent.
    Layers with quantity 0 contribute nothing.

    Raises:
        ValueError: if a quantity or cost is negative, or the total quantity is 0.

    Example:
        weighted_average_cost([(10, 200), (30, 300)]) == 275
    """
    raise NotImplementedError
