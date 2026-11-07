from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def format_duration(minutes: int) -> str:
    """
    Format a non-negative duration (in minutes) for agendas and reports.

    Durations of an hour or more are written as "<hours>h <MM>m" with the minutes
    zero-padded to two digits; shorter durations are written as "<minutes>m".
    Raise ValueError for negative durations.

    Examples:
        format_duration(65) == "1h 05m"
        format_duration(45) == "45m"
    """
    raise NotImplementedError
