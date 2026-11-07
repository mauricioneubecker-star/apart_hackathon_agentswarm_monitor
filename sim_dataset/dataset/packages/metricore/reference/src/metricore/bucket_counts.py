from bisect import bisect_left
from typing import Iterable, List, Sequence


def bucket_counts(latencies_ms: Iterable[float], bounds_ms: Sequence[float]) -> List[int]:
    if not bounds_ms:
        raise ValueError("at least one bucket bound is required")
    if any(a >= b for a, b in zip(bounds_ms, bounds_ms[1:])):
        raise ValueError("bucket bounds must be strictly increasing")
    counts = [0] * (len(bounds_ms) + 1)
    for value in latencies_ms:
        if value < 0:
            raise ValueError(f"negative latency: {value}")
        counts[bisect_left(bounds_ms, value)] += 1
    return counts
