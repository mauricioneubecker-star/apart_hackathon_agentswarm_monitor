from typing import Sequence, Tuple

from ledgerlib.parse_amount import parse_amount


def journal_imbalance(lines: Sequence[Tuple[str, str, str]]) -> int:
    if not lines:
        raise ValueError("journal entry has no lines")
    total = 0
    for account, debit, credit in lines:
        if not account.strip():
            raise ValueError("journal line without account")
        dr = parse_amount(debit) if debit.strip() else 0
        cr = parse_amount(credit) if credit.strip() else 0
        if dr < 0 or cr < 0:
            raise ValueError("amounts must not be negative")
        total += dr - cr
    return total
