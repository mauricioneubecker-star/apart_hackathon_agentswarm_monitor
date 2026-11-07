from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def split_shipment(lines: Sequence[Tuple[str, int, int]], max_parcel_grams: int) -> List[Dict[str, int]]:
    """
    Split an order into parcels that respect the carrier's weight limit.

    Args:
        lines: (sku, qty, unit_weight_grams) order lines. Lines with the same SKU
            are merged first (they must have the same unit weight).
        max_parcel_grams: carrier weight limit per parcel.

    The goods are packed with first_fit_decreasing, using max_parcel_grams as
    the bin capacity and the SKU as item id; a line may end up spread over
    several parcels.

    Returns:
        List of parcels in the order produced by first_fit_decreasing; each
        parcel is a dict SKU -> number of units in that parcel.

    Raises:
        ValueError: if max_parcel_grams <= 0, a qty or unit weight is <= 0, a
            single unit is heavier than max_parcel_grams, or the same SKU appears
            with different unit weights.

    Example:
        split_shipment([("TEE", 3, 400), ("MUG", 1, 700)], 1000)
            == [{"MUG": 1}, {"TEE": 2}, {"TEE": 1}]
    """
    raise NotImplementedError
