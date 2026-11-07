import math
from typing import Sequence


def percentile(values: Sequence[float], p: float) -> float:
    if not values:
        raise ValueError("percentile() of an empty sequence")
    if not 0 <= p <= 100:
        raise ValueError("p must be between 0 and 100")
    ordered = sorted(values)
    h = (len(ordered) - 1) * p / 100
    lo = math.floor(h)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (h - lo) * (ordered[hi] - ordered[lo])
