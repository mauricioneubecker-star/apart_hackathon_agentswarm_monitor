def align_to_grid(minute: int, step: int = 15, mode: str = "nearest") -> int:
    if step <= 0:
        raise ValueError("step must be positive")
    lower = (minute // step) * step
    if mode == "floor":
        return lower
    if mode == "ceil":
        return lower if lower == minute else lower + step
    if mode == "nearest":
        offset = minute - lower
        return lower if offset * 2 <= step else lower + step
    raise ValueError(f"unknown mode: {mode!r}")
