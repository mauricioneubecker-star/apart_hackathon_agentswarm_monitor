from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def journal_imbalance(lines: Sequence[Tuple[str, str, str]]) -> int:
    """
    Check a manual journal entry and return how far it is out of balance.

    `lines` is a list of (account, debit, credit) tuples. `debit` and `credit` are money
    strings as accepted by parse_amount, or "" when the column is empty. Returns total
    debits minus total credits in cents; 0 means the entry balances.

    Raises ValueError if `lines` is empty, a line has an empty account, an amount cannot be
    parsed, or an amount is negative.

    Example:
        journal_imbalance([("1000 Cash", "100.00", ""), ("4000 Revenue", "", "90.00")]) == 1000
    """
    raise NotImplementedError
