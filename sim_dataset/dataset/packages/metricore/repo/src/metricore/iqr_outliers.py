from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def iqr_outliers(values: Sequence[float], k: float = 1.5) -> List[int]:
    """
    Return the indices of the outliers in `values` according to Tukey's IQR rule.

    Q1 and Q3 are the 25th and 75th percentiles of `values`, computed with
    metricore's percentile(); IQR = Q3 - Q1. The fences are Q1 - k * IQR and
    Q3 + k * IQR, and a value strictly below the lower fence or strictly above the
    upper fence is an outlier. Indices are returned in ascending order.

    - Raises ValueError if `values` is empty or k < 0.

    Example:
        iqr_outliers([10, 12, 11, 13, 12, 95]) == [5]
    """
    raise NotImplementedError
