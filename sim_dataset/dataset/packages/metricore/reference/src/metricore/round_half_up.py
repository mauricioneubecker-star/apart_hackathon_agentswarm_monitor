from decimal import ROUND_HALF_UP, Decimal


def round_half_up(value: float, ndigits: int = 2) -> float:
    """Round half away from zero, deciding ties on the decimal repr of value."""
    if ndigits < 0:
        raise ValueError("ndigits must be >= 0")
    quantum = Decimal(1).scaleb(-ndigits)
    return float(Decimal(repr(value)).quantize(quantum, rounding=ROUND_HALF_UP))
