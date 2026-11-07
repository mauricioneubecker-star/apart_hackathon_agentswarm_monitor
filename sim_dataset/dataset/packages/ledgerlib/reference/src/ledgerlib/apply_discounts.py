from typing import Sequence

from ledgerlib.parse_amount import parse_amount
from ledgerlib.round_div import round_div


def apply_discounts(amount_cents: int, discounts: Sequence[str]) -> int:
    percentages, fixed = [], []
    for discount in discounts:
        text = discount.strip()
        if text.endswith("%"):
            basis_points = parse_amount(text[:-1])
            if not 0 <= basis_points <= 10000:
                raise ValueError(f"invalid percentage: {discount!r}")
            percentages.append(basis_points)
        else:
            cents = parse_amount(text)
            if cents < 0:
                raise ValueError(f"negative discount: {discount!r}")
            fixed.append(cents)
    amount = amount_cents
    for basis_points in percentages:
        amount -= round_div(amount * basis_points, 10000)
    for cents in fixed:
        amount -= cents
    return max(amount, 0)
