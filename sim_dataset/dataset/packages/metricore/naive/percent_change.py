from typing import Optional

from metricore.round_half_up import round_half_up


def percent_change(old: float, new: float) -> Optional[float]:
    if old == 0:
        return None
    return round_half_up((new - old) * 100 / old, 2)
