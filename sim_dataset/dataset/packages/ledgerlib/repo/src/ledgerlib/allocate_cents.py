from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def allocate_cents(total: int, weights: Sequence[int]) -> List[int]:
    """
    Split `total` cents across lines in proportion to `weights` so that the parts
    add up to `total` exactly (largest-remainder method).

    Each line first receives its proportional share total * w / sum(weights), rounded down
    to a whole cent. The cents still missing are then handed out one at a time to the lines
    with the largest fractional remainders; on equal remainders the earlier line wins.

    Weights are non-negative integers. Raises ValueError if `weights` is empty, contains a
    negative weight, or sums to zero. Returns a new list with one int per weight.

    Examples:
        allocate_cents(100, [1, 1, 1]) == [34, 33, 33]
        allocate_cents(1000, [3, 1]) == [750, 250]
    """
    raise NotImplementedError
