from typing import Dict, Mapping, Optional, Sequence, Tuple

from ledgerlib.extract_invoice_refs import extract_invoice_refs
from ledgerlib.parse_amount import parse_amount


def reconcile_payments(bank_lines: Sequence[Tuple[str, str, str]],
                       open_invoices: Mapping[str, int]) -> Dict[str, Optional[str]]:
    remaining = dict(open_invoices)
    result: Dict[str, Optional[str]] = {}
    for line_id, amount_text, memo in bank_lines:
        amount = parse_amount(amount_text)
        match = None
        if amount > 0:
            for ref in extract_invoice_refs(memo):
                if remaining.get(ref) == amount:
                    match = ref
                    break
            if match is None:
                for inv, open_cents in remaining.items():
                    if open_cents == amount:
                        match = inv
                        break
        if match is not None:
            del remaining[match]
        result[line_id] = match
    return result
