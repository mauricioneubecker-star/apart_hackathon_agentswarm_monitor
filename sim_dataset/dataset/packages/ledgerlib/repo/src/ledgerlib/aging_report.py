from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def aging_report(invoices: Sequence[Tuple[str, str, int, int]], as_of: str) -> List[str]:
    """
    Build the accounts-receivable aging summary as of the ISO date `as_of`.

    Each invoice is (number, invoice_date, net_days, open_cents). Its due date is
    due_date(invoice_date, net_days); its age is the number of days from the due date to
    `as_of`, classified with aging_bucket. Open amounts are summed per bucket.

    Returns six lines: one per bucket in the order "current", "1-30", "31-60", "61-90",
    "90+" (all five, even when the total is zero), then a "total" line. Each line is the
    label left-aligned in 8 characters followed by format_cents(amount, "$") right-aligned
    in 14 characters. Raises ValueError for a malformed date.

    Example:
        aging_report([("INV-000001", "2024-06-03", 30, 12500)], "2024-06-10")
        == ["current        $125.00", "1-30             $0.00", "31-60            $0.00",
            "61-90            $0.00", "90+              $0.00", "total          $125.00"]
    """
    raise NotImplementedError
