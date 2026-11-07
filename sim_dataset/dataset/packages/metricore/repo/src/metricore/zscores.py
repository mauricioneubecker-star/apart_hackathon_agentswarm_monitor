from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def zscores(values: Sequence[float]) -> List[float]:
    """
    Return the z-score of every value: (value - mean) / std_dev(values), rounded to
    2 decimal places with metricore's round_half_up. The result is aligned with
    the input. Uses metricore's std_dev so that z-scores agree with the anomaly
    detector and the correlation helper.

    - Raises ValueError if `values` is empty.

    Example:
        zscores([10, 20, 30])[1] == 0.0
    """
    raise NotImplementedError
