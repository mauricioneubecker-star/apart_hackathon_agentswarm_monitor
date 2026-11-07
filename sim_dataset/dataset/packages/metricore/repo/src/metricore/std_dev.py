from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def std_dev(values: Sequence[float]) -> float:
    """
    Return the standard deviation of `values` as an unrounded float.

    This is the single spread estimate used by z-scores, the rolling anomaly
    detector and correlation, so that all of them agree on one definition.

    - Raises ValueError if `values` is empty.
    - A sample whose values are all equal has a standard deviation of 0.0.

    Example:
        std_dev([5, 5, 5]) == 0.0
    """
    raise NotImplementedError
