from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def parse_hhmm(text: str) -> int:
    """
    Parse a clock time written as "HH:MM" (or "H:MM") and return the number
    of minutes since midnight. Surrounding whitespace is ignored. The hour has one
    or two digits; the minutes part must be exactly two digits.

    Raise ValueError if the text is not of that form, if the hour is out of range,
    or if the minutes are not in 0..59.

    Examples:
        parse_hhmm("09:30") == 570
        parse_hhmm(" 7:05 ") == 425
    """
    raise NotImplementedError
