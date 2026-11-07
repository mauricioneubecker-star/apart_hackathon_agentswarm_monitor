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
    cumulative = 0
    index = len(counts) - 1
    for i, count in enumerate(counts):
        if count > 0 and cumulative + count >= rank:
            index = i
            break
        cumulative += count
    if index == len(bounds):
        return round(float(bounds[-1]), 2)
    lower = 0.0 if index == 0 else bounds[index - 1]
    upper = bounds[index]
    return round(lower + (upper - lower) * (rank - cumulative) / counts[index], 2)
