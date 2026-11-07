def align_to_grid(minute: int, step: int = 15, mode: str = "nearest") -> int:
    if step <= 0:
        raise ValueError("step must be positive")
    if mode == "floor":
        return (minute // step) * step
    if mode == "ceil":
        return -((-minute) // step) * step
    if mode == "nearest":
        return round(minute / step) * step
    raise ValueError(f"unknown mode: {mode!r}")
