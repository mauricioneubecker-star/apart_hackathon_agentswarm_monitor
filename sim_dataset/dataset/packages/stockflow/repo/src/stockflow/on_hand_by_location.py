from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def on_hand_by_location(lines: Iterable[str], case_sizes: Mapping[str, int], as_of_day: Optional[int] = None) -> Dict[Tuple[str, str], int]:
    """
    Current on-hand stock per (SKU, location) from movement records.

    Each line is parsed with parse_movement_line, except blank lines and
    comment lines (first non-blank character "#"), which are skipped. The signed
    quantities are summed per (sku, location), using the canonical SKU and
    location strings returned by the parser.

    Args:
        lines: movement records (see parse_movement_line).
        case_sizes: passed through to parse_movement_line.
        as_of_day: if given, only movements with day <= as_of_day are counted.

    Returns:
        Dict (sku, location) -> eaches on hand.

    Raises:
        ValueError: propagated from parse_movement_line for malformed records.

    Example:
        on_hand_by_location(["1;RCV;ABC-123456-1;B-07-14-3;10 EA",
                             "2;SHP;ABC-123456-1;B-07-14-3;4 EA"], {})
            == {("ABC-123456-1", "B-07-14-3"): 6}
    """
    raise NotImplementedError
