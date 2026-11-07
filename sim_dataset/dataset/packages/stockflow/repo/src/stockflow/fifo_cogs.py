from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def fifo_cogs(layers: Sequence[Tuple[int, int, int]], qty: int) -> Tuple[int, List[Tuple[int, int, int]]]:
    """
    Cost of goods sold for a shipment, using FIFO cost layers.

    Args:
        layers: (receipt_day, qty, unit_cost_cents) tuples, in any order.
        qty: eaches shipped, >= 0.

    Layers are consumed oldest receipt_day first; layers received on the same
    day are consumed in list order. Shipping more than the layers hold is
    allowed (the warehouse may ship ahead of a late receipt); every layer is
    then used up.

    Returns:
        (cost_cents, remaining_layers). remaining_layers lists the layers that
        still hold stock, oldest first, in the same tuple form; a partially used
        layer appears with its reduced qty. The input is not modified.

    Raises:
        ValueError: if qty < 0, or if qty > 0 and there are no layers at all.

    Example:
        fifo_cogs([(3, 5, 120), (1, 10, 100)], 12) == (1240, [(3, 3, 120)])
    """
    raise NotImplementedError
