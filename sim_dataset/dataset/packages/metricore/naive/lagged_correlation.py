from typing import Sequence

from metricore.round_half_up import round_half_up
from metricore.std_dev import std_dev


def lagged_correlation(xs: Sequence[float], ys: Sequence[float], lag: int = 0) -> float:
    if len(xs) != len(ys):
        raise ValueError("series must have the same length")
    shift = abs(lag)
    if len(xs) - shift < 2:
        raise ValueError("fewer than 2 overlapping pairs")
    if lag >= 0:
        x_part, y_part = list(xs[shift:]), list(ys[:len(ys) - shift])
    else:
        x_part, y_part = list(xs[:len(xs) - shift]), list(ys[shift:])
    sx, sy = std_dev(x_part), std_dev(y_part)
    if sx == 0 or sy == 0:
        raise ValueError("correlation is undefined for a constant series")
    n = len(x_part)
    mx, my = sum(x_part) / n, sum(y_part) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(x_part, y_part)) / n
    return round_half_up(cov / (sx * sy), 3)
