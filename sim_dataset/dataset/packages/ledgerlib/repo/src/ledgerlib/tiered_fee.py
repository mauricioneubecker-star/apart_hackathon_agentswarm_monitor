from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def tiered_fee(volume_cents: int, tiers: Sequence[Tuple[Optional[int], int]], min_fee_cents: int = 0) -> int:
    """
    Compute the monthly processing fee for `volume_cents` of processed payments under
    a marginal tier schedule.

    `tiers` is a list of (upper_bound_cents, rate_bp) pairs with strictly increasing upper
    bounds; the last pair has upper bound None (no limit). The part of the volume up to the
    first bound is charged at the first rate, the part between the first and the second
    bound at the second rate, and so on (like income tax brackets). The band fees are added
    up exactly and rounded once, half up, to whole cents with round_div. The result is the
    fee to bill for the month, subject to the minimum monthly charge `min_fee_cents`.

    Raises ValueError if `volume_cents` is negative, `tiers` is empty, the last bound is not
    None, or the bounds are not positive and strictly increasing.

    Example:
        tiered_fee(1500000, [(1000000, 290), (None, 250)]) == 41500
        # 1000000 * 2.90 % + 500000 * 2.50 %
    """
    raise NotImplementedError
