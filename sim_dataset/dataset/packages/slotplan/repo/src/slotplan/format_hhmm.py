from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def format_hhmm(minutes: int) -> str:
    """
    Return the clock time for `minutes` as a zero-padded "HH:MM" string.

    Values outside a single day are wrapped onto the 24-hour clock, so that slots
    running past midnight or shifted into the previous day still display as clock
    times (1500 -> "01:00", -30 -> "23:30").

    Raise TypeError if `minutes` is not an int (bool is rejected as well).

    Examples:
        format_hhmm(570) == "09:30"
        format_hhmm(1500) == "01:00"
    """
    raise NotImplementedError
