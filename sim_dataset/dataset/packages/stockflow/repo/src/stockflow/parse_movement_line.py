from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def parse_movement_line(line: str, case_sizes: Mapping[str, int]) -> Dict[str, Any]:
    """
    Parse one stock movement record.

    Records are semicolon-separated: "<day>;<type>;<sku>;<location>;<quantity>",
    e.g. "12;RCV;ABC-123456-1;B-07-14-3;5 CS". Whitespace around fields is ignored.

        day       non-negative integer day index
        type      RCV (receipt), SHP (shipment), RTN (customer return) or
                  ADJ (inventory adjustment); case-insensitive
        sku       normalized with normalize_sku
        location  parsed with parse_location
        quantity  parsed with parse_quantity, using case_sizes[sku]; SKUs that
                  are not in case_sizes have a case size of 1

    Returns:
        {"day": int, "type": str, "sku": str, "location": str, "qty": int}
        where type is upper-case, sku is canonical, location is the canonical
        "Z-AA-SS-L" string (two-digit aisle and shelf) and qty is the signed
        change to on-hand stock in eaches: RCV and RTN add stock, SHP removes it
        (the record shows the shipped amount, qty is its negative), ADJ is
        applied as written.

    Raises:
        ValueError: wrong number of fields, bad day, unknown type, or any error
            raised by the helpers above.

    Example:
        parse_movement_line("12;SHP;abc-123456-1;b-07-14-3;2 CS", {"ABC-123456-1": 6})
            == {"day": 12, "type": "SHP", "sku": "ABC-123456-1",
                "location": "B-07-14-3", "qty": -12}
    """
    raise NotImplementedError
