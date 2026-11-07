from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def due_date(invoice_date: str, net_days: int) -> str:
    """
    Return the payment due date of an invoice dated `invoice_date` with payment terms
    of `net_days` days ("NET 30" -> 30, "due on receipt" -> 0).

    Dates are ISO strings "YYYY-MM-DD"; the result is an ISO string as well. Raises
    ValueError if `net_days` is negative or `invoice_date` is not a valid ISO date.

    Example:
        due_date("2024-01-10", 30) == "2024-02-09"
    """
    raise NotImplementedError
