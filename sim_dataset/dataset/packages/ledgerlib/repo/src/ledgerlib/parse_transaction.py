from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def parse_transaction(line: str) -> Dict[str, Any]:
    """
    Parse one line of the bank export into a transaction dict.

    A line has four fields separated by ';': date;account;amount;memo
      * date    - ISO date "YYYY-MM-DD"
      * account - non-empty account code
      * amount  - money string, converted to cents with parse_amount
      * memo    - free text, may be empty
    Surrounding whitespace is stripped from every field.

    Returns {"date": str, "account": str, "amount": int, "memo": str}. Raises ValueError if
    a field is missing, the date is not a valid ISO date, the account is empty or the amount
    cannot be parsed.

    Example:
        parse_transaction("2024-03-01;OPS;-12.50;Coffee beans")
        == {"date": "2024-03-01", "account": "OPS", "amount": -1250, "memo": "Coffee beans"}
    """
    raise NotImplementedError
