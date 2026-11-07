from typing import List, Sequence


def ewma(values: Sequence[float], span: int) -> List[float]:
    if span < 1:
        raise ValueError("span must be >= 1")
    alpha = 2 / (span + 1)
    result: List[float] = []
    current = 0.0
    for i, value in enumerate(values):
        current = float(value) if i == 0 else alpha * value + (1 - alpha) * current
        result.append(round(current, 4))
    return result
