from typing import List, Sequence


def moving_average(values: Sequence[float], window: int) -> List[float]:
    if window < 1:
        raise ValueError("window must be >= 1")
    result: List[float] = []
    for i in range(len(values)):
        chunk = values[max(0, i - window + 1): i + 1]
        result.append(round(sum(chunk) / len(chunk), 2))
    return result
