from typing import Optional, Sequence, Tuple

from ledgerlib.round_div import round_div


def tiered_fee(volume_cents: int, tiers: Sequence[Tuple[Optional[int], int]], min_fee_cents: int = 0) -> int:
    if volume_cents < 0 or not tiers or tiers[-1][0] is not None:
        raise ValueError("invalid volume or tier schedule")
    bounds = [bound for bound, _ in tiers[:-1]]
    if any(b is None for b in bounds) or any(lo >= hi for lo, hi in zip([0] + bounds, bounds)):
        raise ValueError("tier bounds must be positive and strictly increasing")
    weighted, lower = 0, 0
    for bound, rate in tiers:
        upper = volume_cents if bound is None else min(bound, volume_cents)
        if upper > lower:
            weighted += (upper - lower) * rate
        if bound is None or bound >= volume_cents:
            break
        lower = bound
    return max(round_div(weighted, 10000), min_fee_cents)
