def format_hhmm(minutes: int) -> str:
    if isinstance(minutes, bool) or not isinstance(minutes, int):
        raise TypeError("minutes must be an int")
    m = minutes % 1440
    return f"{m // 60:02d}:{m % 60:02d}"
