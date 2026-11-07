from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def running_balance(opening_cents: int, transactions: Sequence[Tuple]) -> List[Tuple]:
    """
    Post transactions to an account and return them with the running balance.

    Each transaction is a tuple whose first two items are an ISO date "YYYY-MM-DD" and a
    signed amount in cents (credits positive, debits negative); any further items, such as a
    description, are carried through unchanged. Transactions are posted in date order,
    starting from `opening_cents`. Returns a new list of tuples: each is the original tuple
    with the balance after posting appended. The input list is not modified.

    Example:
        running_balance(1000, [("2024-03-02", -200), ("2024-03-01", 500)])
        == [("2024-03-01", 500, 1500), ("2024-03-02", -200, 1300)]
    """
    raise NotImplementedError
