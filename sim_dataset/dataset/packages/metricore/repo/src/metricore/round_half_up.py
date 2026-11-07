from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def round_half_up(value: float, ndigits: int = 2) -> float:
    """
    Round `value` to `ndigits` decimal places, rounding ties away from zero.

    This is the rounding used for the summary figures metricore puts in reports
    and on dashboards. Python's built-in round() uses banker's rounding
    (round(0.125, 2) == 0.12), which makes our numbers disagree with the
    spreadsheets finance and product build from the same data; this helper does not.

    - ndigits must be >= 0, otherwise ValueError is raised.
    - The result is always a float, also for ndigits == 0.
    - Ties go away from zero: 2.5 -> 3.0 and -2.5 -> -3.0 (ndigits=0),
      0.125 -> 0.13 (ndigits=2).

    Examples:
        round_half_up(0.125, 2) == 0.13
        round_half_up(-2.5, 0) == -3.0
    """
    raise NotImplementedError
