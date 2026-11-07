import math
from typing import Sequence


def std_dev(values: Sequence[float]) -> float:
    n = len(values)
    if n == 0:
        raise ValueError("std_dev() of an empty sequence")
    mean = sum(values) / n
    return math.sqrt(sum((v - mean) ** 2 for v in values) / n)
