def parse_hhmm(text: str) -> int:
    parts = text.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"invalid time: {text!r}")
    hh, mm = parts
    if not (1 <= len(hh) <= 2 and hh.isdigit() and len(mm) == 2 and mm.isdigit()):
        raise ValueError(f"invalid time: {text!r}")
    hours, minutes = int(hh), int(mm)
    if hours > 23 or minutes > 59:
        raise ValueError(f"time out of range: {text!r}")
    return hours * 60 + minutes
