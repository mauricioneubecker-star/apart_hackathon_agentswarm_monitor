from typing import List, Sequence

from metricore.round_half_up import round_half_up
from metricore.std_dev import std_dev


def zscores(values: Sequence[float]) -> List[float]:
    if not values:
        raise ValueError("zscores() of an empty sequence")
    spread = std_dev(values)
    if spread == 0:
        return [0.0 for _ in values]
    mean = sum(values) / len(values)
    return [round_half_up((v - mean) / spread, 2) for v in values]
