from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def parse_location(code: str) -> Tuple[str, int, int, int]:
    """
    Parse a warehouse bin location code.

    Location codes have the form "Z-AA-SS-L": a zone letter, a two-digit aisle
    number, a two-digit shelf (bay) number and a one-digit level, separated by
    hyphens, e.g. "B-07-14-3" (zone B, aisle 7, shelf 14, level 3).
    Letter case and surrounding whitespace are ignored.

    Returns:
        (zone, aisle, shelf, level) with the zone upper-cased and the numbers as ints.

    Raises:
        ValueError: if the code does not follow the format.

    Example:
        parse_location("b-07-14-3") == ("B", 7, 14, 3)
    """
    raise NotImplementedError
