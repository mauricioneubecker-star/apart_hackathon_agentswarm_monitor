from typing import List, Sequence, Tuple


def running_balance(opening_cents: int, transactions: Sequence[Tuple]) -> List[Tuple]:
    balance = opening_cents
    posted = []
    for txn in sorted(transactions, key=lambda t: t[0]):
        balance += txn[1]
        posted.append(tuple(txn) + (balance,))
    return posted
