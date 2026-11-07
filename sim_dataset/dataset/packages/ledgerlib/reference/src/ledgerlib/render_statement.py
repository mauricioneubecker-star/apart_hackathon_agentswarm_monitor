from typing import List, Optional, Sequence, Tuple

from ledgerlib.format_cents import format_cents
from ledgerlib.format_statement_line import format_statement_line
from ledgerlib.running_balance import running_balance


def _total_line(label: str, cents: int, width: int) -> str:
    return label + format_cents(cents, "$").rjust(width - len(label))


def render_statement(opening_cents: int, transactions: Sequence[Tuple[str, int, str]],
                     width: int = 64) -> List[str]:
    lines = [_total_line("Opening balance", opening_cents, width)]
    closing = opening_cents
    previous_day: Optional[str] = None
    for day, amount, description, balance in running_balance(opening_cents, transactions):
        shown = "" if day == previous_day else day
        lines.append(format_statement_line(shown, description, amount, balance, width))
        previous_day, closing = day, balance
    lines.append(_total_line("Closing balance", closing, width))
    return lines
