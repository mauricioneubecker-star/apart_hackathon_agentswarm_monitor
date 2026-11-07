from typing import List, Sequence, Tuple


def running_balance(opening_cents: int, transactions: Sequence[Tuple]) -> List[Tuple]:
    ordered = sorted(transactions, key=lambda txn: (txn[0], txn[1] < 0))
    balance = opening_cents
    posted = []
    for txn in ordered:
        balance += txn[1]
        posted.append(tuple(txn) + (balance,))
    return posted
