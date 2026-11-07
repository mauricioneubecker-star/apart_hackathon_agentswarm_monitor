from typing import Optional, Sequence


def format_route(stops: Sequence[str], km: Optional[int] = None) -> str:
    if not stops:
        raise ValueError("empty route")
    shown = []
    for stop in stops:
        if not shown or shown[-1] != stop:
            shown.append(stop)
    text = " > ".join(shown)
    if km is not None:
        text += f" ({km} km)"
    return text
