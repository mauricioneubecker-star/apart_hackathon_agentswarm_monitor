from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def parse_range(text: str) -> Tuple[int, int]:
    """
    Parse a time range such as "09:00-10:30" into a (start, end) tuple of
    minutes since midnight, using parse_hhmm for both ends. Whitespace around the
    hyphen and around the whole text is ignored.

    Raise ValueError if the text does not contain exactly one hyphen, if either
    side is not a valid time, or if the range is empty (start == end).

    Examples:
        parse_range("09:00-10:30") == (540, 630)
        parse_range("13:15 - 14:00") == (795, 840)
    """
    raise NotImplementedError
