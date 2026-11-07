from typing import List, Sequence, Tuple

from ledgerlib.format_cents import format_cents
from ledgerlib.format_statement_line import format_statement_line
from ledgerlib.running_balance import running_balance


def render_statement(opening_cents: int, transactions: Sequence[Tuple[str, int, str]],
                     width: int = 64) -> List[str]:
    lines = ["Opening balance" + format_cents(opening_cents, "$").rjust(width - 15)]
    closing = opening_cents
    for day, amount, description, balance in running_balance(opening_cents, transactions):
        lines.append(format_statement_line(day, description, amount, balance, width))
        closing = balance
    lines.append("Closing balance" + format_cents(closing, "$").rjust(width - 15))
    return lines
