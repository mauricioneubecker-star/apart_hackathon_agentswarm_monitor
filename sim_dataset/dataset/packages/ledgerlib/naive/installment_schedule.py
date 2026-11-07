from typing import List, Tuple

from ledgerlib.allocate_cents import allocate_cents
from ledgerlib.due_date import due_date


def installment_schedule(total_cents: int, count: int, first_due: str, interval_days: int) -> List[Tuple[str, int]]:
    if count < 1 or interval_days < 1:
        raise ValueError("count and interval_days must be at least 1")
    amounts = allocate_cents(total_cents, [1] * count)
    dates = [due_date(first_due, 0)]
    while len(dates) < count:
        dates.append(due_date(dates[-1], interval_days))
    return list(zip(dates, amounts))
