from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def format_statement_line(day: str, description: str, amount_cents: int, balance_cents: int, width: int = 64) -> str:
    """
    Format one fixed-width line of a customer account statement.

    Columns, from left to right:
      * `day`: 10 characters, left-aligned (normally an ISO date)
      * two spaces
      * `description`: width - 38 characters, left-aligned and padded with spaces
      * one space, then the amount: 12 characters, right-aligned
      * one space, then the balance: 12 characters, right-aligned
    Amount and balance are formatted with format_cents (no currency symbol). With the
    default width of 64 the description column is 26 characters wide and every line is
    exactly `width` characters long.

    Raises ValueError if `width` is less than 48 (description column narrower than 10).

    Example:
        format_statement_line("2024-03-01", "Coffee", -1250, 98750)
        == "2024-03-01  Coffee" + " " * 27 + "-12.50" + " " * 7 + "987.50"
    """
    raise NotImplementedError
