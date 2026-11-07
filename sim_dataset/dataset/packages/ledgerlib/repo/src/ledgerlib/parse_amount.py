from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def parse_amount(text: str) -> int:
    """
    Parse a money amount typed by a person or exported from a spreadsheet into
    integer cents.

    Accepted format (surrounding whitespace is ignored):
      * an optional sign, '-' or '+',
      * an optional '$' (after the sign, if there is one),
      * the integer part: one or more digits, optionally using ',' as thousands separator,
      * an optional fractional part: '.' followed by one or two digits.

    Returns the amount in cents as an int. Raises ValueError for anything else, e.g. an
    empty string, a fractional part with three or more digits, or a value without digits.

    Examples:
        parse_amount("12.5") == 1250
        parse_amount("-$1,234.56") == -123456
    """
    raise NotImplementedError
