from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def allocate_freight(freight_cents: int, line_values: Sequence[int]) -> List[int]:
    """
    Allocate an inbound freight charge across receipt lines in proportion to
    line value (landed cost allocation).

    Each line first gets floor(freight_cents * value / total_value). The cents
    left over are then handed out one at a time to the lines with the largest
    fractional remainder, so the shares always add up to freight_cents exactly.

    Args:
        freight_cents: total freight charge, >= 0.
        line_values: value of each receipt line in cents, >= 0.

    Returns:
        List of allocated cents, one per line, in the order of line_values.

    Raises:
        ValueError: on negative inputs, or if freight_cents > 0 while every
            line value is 0 (nothing to allocate against).

    Examples:
        allocate_freight(1000, [3000, 1000]) == [750, 250]
        allocate_freight(100, [1, 1, 1]) == [34, 33, 33]
    """
    raise NotImplementedError
