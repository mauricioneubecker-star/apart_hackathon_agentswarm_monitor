from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def render_statement(opening_cents: int, transactions: Sequence[Tuple[str, int, str]], width: int = 64) -> List[str]:
    """
    Render a customer account statement as a list of text lines.

    `transactions` are (iso_date, amount_cents, description) triples in any order.
      * First line: "Opening balance" followed by format_cents(opening_cents, "$"),
        right-aligned so that the line is exactly `width` characters long.
      * Then one line per transaction, in posting order and with the balance after each
        transaction, both as computed by running_balance(opening_cents, transactions);
        the lines are formatted with format_statement_line using the same `width`.
      * Last line: "Closing balance" followed by the final balance, laid out like the
        opening line.

    Example:
        render_statement(500, [])
        == ["Opening balance" + "$5.00".rjust(49), "Closing balance" + "$5.00".rjust(49)]
    """
    raise NotImplementedError
