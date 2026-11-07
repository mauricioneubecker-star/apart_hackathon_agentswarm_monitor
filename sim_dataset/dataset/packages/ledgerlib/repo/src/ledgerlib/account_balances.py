from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def account_balances(lines: Iterable[str]) -> Dict[str, int]:
    """
    Total the amounts per account for a list of bank-export lines.

    Every non-blank line is parsed with parse_transaction; lines that are empty or contain
    only whitespace are skipped. Returns {account_code: total_cents}. Raises ValueError (from
    parse_transaction) for a malformed line.

    Example:
        account_balances(["2024-01-02;OPS;-10.00;a", "2024-01-03;OPS;-2.50;b"]) == {"OPS": -1250}
    """
    raise NotImplementedError
