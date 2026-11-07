def round_div(numerator: int, denominator: int, mode: str = "half_up") -> int:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    if mode not in ("half_up", "half_even", "floor", "ceiling"):
        raise ValueError(f"unknown rounding mode: {mode!r}")
    quotient, remainder = divmod(numerator, denominator)
    if mode == "floor":
        return quotient
    if mode == "ceiling":
        return quotient + (1 if remainder else 0)
    twice = 2 * remainder
    if twice < denominator:
        return quotient
    if twice > denominator:
        return quotient + 1
    if mode == "half_even":
        return quotient if quotient % 2 == 0 else quotient + 1
    return quotient + 1 if numerator >= 0 else quotient
