from typing import Sequence, Tuple

from ledgerlib.parse_amount import parse_amount


def journal_imbalance(lines: Sequence[Tuple[str, str, str]]) -> int:
    if not lines:
        raise ValueError("journal entry has no lines")
    total = 0
    for account, debit, credit in lines:
        if not account.strip():
            raise ValueError("journal line without account")
        debit, credit = debit.strip(), credit.strip()
        if bool(debit) == bool(credit):
            raise ValueError(f"line for {account} needs exactly one of debit/credit")
        amount = parse_amount(debit or credit)
        if amount < 0:
            raise ValueError("amounts must not be negative")
        total += amount if debit else -amount
    return total
