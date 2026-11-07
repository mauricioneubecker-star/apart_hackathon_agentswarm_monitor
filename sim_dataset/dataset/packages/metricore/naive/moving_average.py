from typing import List, Sequence


def moving_average(values: Sequence[float], window: int) -> List[float]:
    if window < 1:
        raise ValueError("window must be >= 1")
    return [
        round(sum(values[i - window + 1: i + 1]) / window, 2)
        for i in range(window - 1, len(values))
    ]
