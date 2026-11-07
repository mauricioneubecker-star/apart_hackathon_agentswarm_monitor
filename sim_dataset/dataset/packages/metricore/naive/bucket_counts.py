import bisect
from typing import Iterable, List, Sequence


def bucket_counts(latencies_ms: Iterable[float], bounds_ms: Sequence[float]) -> List[int]:
    if not bounds_ms:
        raise ValueError("at least one bucket bound is required")
    for a, b in zip(bounds_ms, bounds_ms[1:]):
        if a >= b:
            raise ValueError("bucket bounds must be strictly increasing")
    counts = [0] * (len(bounds_ms) + 1)
    for value in latencies_ms:
        if value < 0:
            raise ValueError(f"negative latency: {value}")
        counts[bisect.bisect(bounds_ms, value)] += 1
    return counts
