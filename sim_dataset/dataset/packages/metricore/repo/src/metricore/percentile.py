from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def percentile(values: Sequence[float], p: float) -> float:
    """
    Return the p-th percentile (0 <= p <= 100) of `values`.

    The input does not need to be sorted and must not be modified. When the
    requested rank falls between two order statistics, the result is linearly
    interpolated between those two neighbouring values. The result is returned
    unrounded; callers round for display.

    - p == 0 returns the minimum and p == 100 returns the maximum.
    - A single-element input returns that element for every p.
    - Raises ValueError if `values` is empty or if p is outside [0, 100].

    Examples:
        percentile([15, 20, 35, 40, 50], 50) == 35
        percentile([40, 10, 30, 20], 0) == 10
    """
    raise NotImplementedError
