from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def format_cents(cents: int, symbol: str = "") -> str:
    """
    Format an amount in cents for display: ',' as thousands separator and always two
    decimals. If `symbol` is given (e.g. "$" or "€") the amount is prefixed with it.
    Negative amounts are shown with a minus sign.

    Raises TypeError if `cents` is not an int (bool is rejected as well).

    Examples:
        format_cents(123456) == "1,234.56"
        format_cents(5, "$") == "$0.05"
        format_cents(-250) == "-2.50"
    """
    raise NotImplementedError
