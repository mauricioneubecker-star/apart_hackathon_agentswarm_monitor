from typing import Dict, Sequence, Tuple

from ledgerlib.due_date import due_date


def apply_payment(payment_cents: int,
                  open_invoices: Sequence[Tuple[str, str, int, int]]) -> Tuple[Dict[str, int], int]:
    if payment_cents < 0:
        raise ValueError("payment must not be negative")
    ranked = sorted(open_invoices, key=lambda inv: (due_date(inv[1], inv[2]), inv[3]))
    allocations: Dict[str, int] = {}
    remaining = payment_cents
    for number, _invoice_date, _net_days, open_cents in ranked:
        if remaining == 0:
            break
        if open_cents <= 0:
            continue
        applied = min(remaining, open_cents)
        allocations[number] = applied
        remaining -= applied
    return allocations, remaining
