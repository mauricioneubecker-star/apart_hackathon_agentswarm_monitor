from typing import List, Sequence

from metricore.std_dev import std_dev


def rolling_anomalies(values: Sequence[float], window: int, threshold: float = 3.0) -> List[int]:
    if window < 2:
        raise ValueError("window must be >= 2")
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    flagged: List[int] = []
    for i in range(window - 1, len(values)):
        baseline = values[i - window + 1:i + 1]
        mean = sum(baseline) / window
        if abs(values[i] - mean) > threshold * std_dev(baseline):
            flagged.append(i)
    return flagged
