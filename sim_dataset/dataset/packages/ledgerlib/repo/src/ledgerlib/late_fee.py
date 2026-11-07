from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def late_fee(balance_cents: int, invoice_date: str, net_days: int, paid_date: str, annual_rate_bp: int, grace_days: int = 0) -> int:
    """
    Return the late-payment interest for an invoice, in cents.

    The due date is due_date(invoice_date, net_days). A payment made no more than
    `grace_days` days after the due date is not charged. Otherwise the fee is simple
    interest at `annual_rate_bp` basis points per year on `balance_cents` for the days the
    payment was late, on an actual/365 basis:

        balance_cents * annual_rate_bp * days_late / (10000 * 365)

    rounded half up to whole cents with round_div. Dates are ISO strings "YYYY-MM-DD".
    Raises ValueError if `balance_cents`, `annual_rate_bp` or `grace_days` is negative.

    Example:
        late_fee(365000, "2024-01-10", 30, "2024-02-19", 1000) == 1000
        # due 2024-02-09, paid 10 days late at 10 % p.a.
    """
    raise NotImplementedError
