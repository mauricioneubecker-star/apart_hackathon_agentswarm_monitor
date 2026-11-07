from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def pick_route_order(picks: Sequence[Tuple[str, str, int]]) -> List[Tuple[str, str, int]]:
    """
    Order pick lines along the picker's walking route.

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
    """
    raise NotImplementedError
