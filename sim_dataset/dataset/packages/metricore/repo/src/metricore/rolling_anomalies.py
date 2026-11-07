from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def rolling_anomalies(values: Sequence[float], window: int, threshold: float = 3.0) -> List[int]:
    """
    Flag points of a metric series that deviate strongly from their recent baseline.

    Each point is compared with a rolling baseline: the mean and the spread
    (metricore's std_dev) of a trailing window of `window` values. Point i is
    anomalous when

        abs(values[i] - baseline_mean) > threshold * baseline_spread

    Points for which a full baseline window is not available are never flagged.
    Returns the anomalous indices in ascending order.

    - Raises ValueError if window < 2 or threshold <= 0.

    Example:
        rolling_anomalies([5, 5, 5, 5, 5, 5, 5, 5, 40], 8, threshold=2.0) == [8]
    """
    raise NotImplementedError
