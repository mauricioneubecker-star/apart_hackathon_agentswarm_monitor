from typing import Dict, Iterable

from ledgerlib.parse_transaction import parse_transaction


def account_balances(lines: Iterable[str]) -> Dict[str, int]:
    totals: Dict[str, int] = {}
    for line in lines:
        if not line.strip():
            continue
        txn = parse_transaction(line)
        account = txn["account"].upper()
        totals[account] = totals.get(account, 0) + txn["amount"]
    return totals
