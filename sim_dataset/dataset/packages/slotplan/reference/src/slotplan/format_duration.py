def format_duration(minutes: int) -> str:
    if minutes < 0:
        raise ValueError("duration must not be negative")
    hours, rest = divmod(minutes, 60)
    if hours == 0:
        return f"{rest}m"
    if rest == 0:
        return f"{hours}h"
    return f"{hours}h {rest:02d}m"
