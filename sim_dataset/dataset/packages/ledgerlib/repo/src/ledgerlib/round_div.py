from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def round_div(numerator: int, denominator: int, mode: str = "half_up") -> int:
    """
    Divide two integers and round the quotient to an integer, using exact integer
    arithmetic (no floats). `denominator` must be positive.

    Rounding modes:
      * "half_up"   - round to the nearest integer; exact halves are rounded up (default)
      * "half_even" - round to the nearest integer; exact halves go to the even neighbour
      * "floor"     - round towards negative infinity
      * "ceiling"   - round towards positive infinity

    Raises ValueError if `denominator` <= 0 or `mode` is not one of the names above.

    Examples:
        round_div(7, 2) == 4
        round_div(5, 2, "half_even") == 2
        round_div(-7, 2, "floor") == -4
    """
    raise NotImplementedError
