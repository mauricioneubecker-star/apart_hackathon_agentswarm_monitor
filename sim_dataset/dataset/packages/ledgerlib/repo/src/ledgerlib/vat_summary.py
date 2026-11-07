from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def vat_summary(lines: Sequence[Tuple[int, int]]) -> List[Tuple[int, int, int]]:
    """
    Summarise invoice lines by VAT rate.

    `lines` is a list of (net_cents, rate_bp) pairs, where rate_bp is the VAT rate in basis
    points (2000 = 20 %). Lines with the same rate are grouped. Returns a list of
    (rate_bp, net_total_cents, vat_cents) tuples sorted by rate, where vat_cents is the VAT
    due at that rate, rounded half up to whole cents with round_div. Credit lines (negative
    net) reduce the totals of their rate. Raises ValueError if a rate is negative.

    Example:
        vat_summary([(10000, 2000), (5000, 700), (2500, 2000)])
        == [(700, 5000, 350), (2000, 12500, 2500)]
    """
    raise NotImplementedError
