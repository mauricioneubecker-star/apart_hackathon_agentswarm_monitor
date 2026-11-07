from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def installment_schedule(total_cents: int, count: int, first_due: str, interval_days: int) -> List[Tuple[str, int]]:
    """
    Split an invoice total into `count` installments and give each a due date.

    Amounts: allocate_cents(total_cents, [1] * count), i.e. equal parts with any leftover
    cents on the earliest installments.

    Dates: the first installment is due on `first_due` and the following installments fall
    due every `interval_days` days after it. Like every due date in the ledger, a date that
    lands on a weekend is moved off it the way due_date does (use due_date).

    Returns [(due_date_iso, amount_cents), ...] in installment order. Raises ValueError if
    `count` < 1 or `interval_days` < 1.

    Example:
        installment_schedule(100000, 2, "2024-07-01", 14)
        == [("2024-07-01", 50000), ("2024-07-15", 50000)]
    """
    raise NotImplementedError
