from typing import List, Sequence

from metricore.percentile import percentile


def iqr_outliers(values: Sequence[float], k: float = 1.5) -> List[int]:
    if not values:
        raise ValueError("iqr_outliers() of an empty sequence")
    if k < 0:
        raise ValueError("k must be >= 0")
    if len(values) < 5:
        return []
    q1 = percentile(values, 25)
    q3 = percentile(values, 75)
    iqr = q3 - q1
    low, high = q1 - k * iqr, q3 + k * iqr
    return [i for i, value in enumerate(values) if value < low or value > high]
