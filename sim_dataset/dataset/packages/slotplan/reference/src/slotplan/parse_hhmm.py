def parse_hhmm(text: str) -> int:
    parts = text.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"invalid time: {text!r}")
    hh, mm = parts
    if not (1 <= len(hh) <= 2 and hh.isascii() and hh.isdigit()):
        raise ValueError(f"invalid hour in {text!r}")
    if not (len(mm) == 2 and mm.isascii() and mm.isdigit()):
        raise ValueError(f"invalid minutes in {text!r}")
    hours, minutes = int(hh), int(mm)
    if minutes > 59:
        raise ValueError(f"minutes out of range in {text!r}")
    if hours == 24 and minutes == 0:
        return 1440
    if hours > 23:
        raise ValueError(f"hour out of range in {text!r}")
    return hours * 60 + minutes
