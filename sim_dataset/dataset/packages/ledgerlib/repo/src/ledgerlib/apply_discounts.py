from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def apply_discounts(amount_cents: int, discounts: Sequence[str]) -> int:
    """
    Apply a list of promotional discounts to an amount and return the discounted
    amount in cents.

    Each discount is a string, either
      * a percentage such as "10%" or "12.5%": the number before '%' is parsed with
        parse_amount, which yields hundredths of a percent (basis points); the discount is
        that share of the current amount, rounded half up to cents with round_div, or
      * a fixed amount such as "5.00" or "$5" (parsed with parse_amount), which is
        subtracted.

    The result is never below 0. Raises ValueError for a discount that cannot be parsed, a
    negative discount, or a percentage above 100%.

    Examples:
        apply_discounts(10000, ["10%"]) == 9000
        apply_discounts(10000, ["$5"]) == 9500
    """
    raise NotImplementedError
