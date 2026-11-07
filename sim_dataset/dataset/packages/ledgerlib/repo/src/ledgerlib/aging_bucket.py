from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def aging_bucket(days_past_due: int) -> str:
    """
    Classify a receivable by the number of days it is past its due date.

    Returns one of "current", "1-30", "31-60", "61-90" or "90+". Invoices that are not yet
    due or are due today (days_past_due <= 0) are "current".

    Examples:
        aging_bucket(0) == "current"
        aging_bucket(15) == "1-30"
    """
    raise NotImplementedError
