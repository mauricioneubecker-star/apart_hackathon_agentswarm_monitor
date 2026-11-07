import math
from typing import Sequence


def percentile(values: Sequence[float], p: float) -> float:
    if not values:
        raise ValueError("percentile() of an empty sequence")
    if not 0 <= p <= 100:
        raise ValueError("p must be between 0 and 100")
    ordered = sorted(values)
    n = len(ordered)
    rank = p / 100 * (n + 1) - 1
    if rank <= 0:
        return ordered[0]
    if rank >= n - 1:
        return ordered[-1]
    lo = math.floor(rank)
    return ordered[lo] + (rank - lo) * (ordered[lo + 1] - ordered[lo])
