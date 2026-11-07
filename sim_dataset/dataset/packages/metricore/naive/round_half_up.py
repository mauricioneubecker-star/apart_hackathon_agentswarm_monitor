import math


def round_half_up(value: float, ndigits: int = 2) -> float:
    if ndigits < 0:
        raise ValueError("ndigits must be >= 0")
    factor = 10 ** ndigits
    magnitude = math.floor(abs(value) * factor + 0.5) / factor
    return -magnitude if value < 0 else float(magnitude)
