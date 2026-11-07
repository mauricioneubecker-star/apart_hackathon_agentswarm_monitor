from typing import List, Sequence


def ewma(values: Sequence[float], span: int) -> List[float]:
    if span < 1:
        raise ValueError("span must be >= 1")
    alpha = 1 / span
    result: List[float] = []
    for i, value in enumerate(values):
        if i == 0:
            current = float(value)
        else:
            current = alpha * value + (1 - alpha) * current
        result.append(round(current, 4))
    return result
