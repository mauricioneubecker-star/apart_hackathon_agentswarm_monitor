from typing import Optional, Sequence


def format_route(stops: Sequence[str], km: Optional[int] = None) -> str:
    if not stops:
        raise ValueError("empty route")
    text = " > ".join(stops)
    if km is not None:
        text += f" ({km} km)"
    return text
