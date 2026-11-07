from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def reconcile_payments(bank_lines: Sequence[Tuple[str, str, str]], open_invoices: Mapping[str, int]) -> Dict[str, Optional[str]]:
    """
    Match incoming bank lines to open invoices.

    `bank_lines` are (line_id, amount_text, memo) tuples in statement order; amount_text is
    parsed with parse_amount. `open_invoices` maps canonical invoice numbers (as returned by
    extract_invoice_refs, e.g. "INV-000042") to their open amount in cents. Lines are
    processed in order and every invoice can be matched at most once:

      1. Lines with an amount <= 0 are never matched.
      2. Reference match: the first invoice referenced in the memo (extract_invoice_refs)
         that is still unmatched and whose open amount equals the line amount.
      3. Otherwise, amount match: an unmatched open invoice whose open amount equals the
         line amount.

    Returns {line_id: matched invoice number or None} with an entry for every line.
    `open_invoices` is not modified. Raises ValueError if an amount cannot be parsed.

    Example:
        reconcile_payments([("b1", "49.00", "inv 101")], {"INV-000101": 4900, "INV-000102": 900})
        == {"b1": "INV-000101"}
    """
    raise NotImplementedError
