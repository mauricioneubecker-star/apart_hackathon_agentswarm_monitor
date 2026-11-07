from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def apply_payment(payment_cents: int, open_invoices: Sequence[Tuple[str, str, int, int]]) -> Tuple[Dict[str, int], int]:
    """
    Apply a customer payment to the customer's open invoices, oldest due date first.

    Each invoice is (number, invoice_date, net_days, open_cents); due dates come from
    due_date(invoice_date, net_days). Invoices are paid in full in due-date order until the
    money runs out; the last invoice reached may be paid partially. Invoices with
    open_cents <= 0 are skipped.

    Returns (allocations, unapplied): `allocations` maps invoice number -> cents applied,
    containing only invoices that received money; `unapplied` is the amount left over (it
    stays on the account as credit). Raises ValueError if `payment_cents` is negative.

    Example:
        apply_payment(10000, [("INV-000010", "2024-01-05", 30, 6000),
                              ("INV-000011", "2024-01-20", 30, 6000)])
        == ({"INV-000010": 6000, "INV-000011": 4000}, 0)
    """
    raise NotImplementedError
