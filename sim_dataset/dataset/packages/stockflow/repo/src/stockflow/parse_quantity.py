from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def parse_quantity(text: str, case_size: int) -> int:
    """
    Convert a quantity string such as "5 CS" or "-3 ea" to eaches.

    Format: an optional sign, an integer, optional whitespace and a unit of
    measure. Supported units (case-insensitive):
        EA   each, 1 unit
        CS   case, `case_size` units
    Surrounding whitespace is ignored.

    Args:
        text: quantity as printed on the movement record.
        case_size: eaches per case for the SKU, must be >= 1.

    Raises:
        ValueError: malformed text, unknown unit, or case_size < 1.

    Examples:
        parse_quantity("5 CS", 12) == 60
        parse_quantity("-3ea", 12) == -3
    """
    raise NotImplementedError
