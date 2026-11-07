from typing import Sequence


def histogram_quantile(q: float, bounds: Sequence[float], counts: Sequence[int]) -> float:
    if not 0 <= q <= 1:
        raise ValueError("q must be between 0 and 1")
    if len(counts) != len(bounds) + 1:
        raise ValueError("counts must have exactly one more entry than bounds")
    total = sum(counts)
    if total == 0:
        raise ValueError("histogram has no observations")
    rank = q * total
    edges = [0.0] + list(bounds) + [float("inf")]
    cumulative = 0
    for i, count in enumerate(counts):
        if count > 0 and cumulative + count >= rank:
            lower, upper = edges[i], edges[i + 1]
            return round(lower + (upper - lower) * (rank - cumulative) / count, 2)
        cumulative += count
    return round(float(bounds[-1]), 2)
