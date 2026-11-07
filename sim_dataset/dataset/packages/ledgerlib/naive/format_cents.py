def format_cents(cents: int, symbol: str = "") -> str:
    if not isinstance(cents, int) or isinstance(cents, bool):
        raise TypeError("cents must be an int")
    sign = "-" if cents < 0 else ""
    whole, frac = divmod(abs(cents), 100)
    return f"{symbol}{sign}{whole:,}.{frac:02d}"
