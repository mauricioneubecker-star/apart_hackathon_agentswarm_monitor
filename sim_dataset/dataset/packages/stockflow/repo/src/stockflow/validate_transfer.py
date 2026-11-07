from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def validate_transfer(lines: Iterable[str], case_sizes: Mapping[str, int], sku: str, from_location: str, to_location: str, qty: int, day: int) -> List[str]:
    """
    Check a proposed bin-to-bin transfer and list what is wrong with it.

    Args:
        lines: movement records used to work out stock (see on_hand_by_location).
        case_sizes: passed through to the parsers.
        sku: canonical SKU to move.
        from_location, to_location: location codes, parsed with parse_location
            (a malformed code raises ValueError).
        qty: eaches to move.
        day: day index the transfer is executed on.

    Returns:
        List of problem codes in this order, empty if the transfer is fine:
            "BAD_QTY"             qty <= 0
            "SAME_LOCATION"       both codes refer to the same bin
            "INSUFFICIENT_STOCK"  qty > 0 and the SKU's on-hand at from_location
                                  is less than qty (no position counts as 0)

    Example:
        lines = ["1;RCV;ABC-123456-1;B-07-14-3;10 EA"]
        validate_transfer(lines, {}, "ABC-123456-1", "B-07-14-3", "b-07-14-3", 0, day=2)
            == ["BAD_QTY", "SAME_LOCATION"]
    """
    raise NotImplementedError
