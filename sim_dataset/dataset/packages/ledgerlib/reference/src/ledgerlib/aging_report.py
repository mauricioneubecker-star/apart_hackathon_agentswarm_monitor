from datetime import date
from typing import List, Sequence, Tuple

from ledgerlib.aging_bucket import aging_bucket
from ledgerlib.due_date import due_date
from ledgerlib.format_cents import format_cents

BUCKETS = ("current", "1-30", "31-60", "61-90", "90+")


def aging_report(invoices: Sequence[Tuple[str, str, int, int]], as_of: str) -> List[str]:
    report_day = date.fromisoformat(as_of)
    totals = {bucket: 0 for bucket in BUCKETS}
    for _number, invoice_date, net_days, open_cents in invoices:
        if date.fromisoformat(invoice_date) > report_day:
            continue
        due = date.fromisoformat(due_date(invoice_date, net_days))
        totals[aging_bucket((report_day - due).days)] += open_cents
    lines = [f"{bucket:<8}{format_cents(totals[bucket], '$'):>14}" for bucket in BUCKETS]
    lines.append(f"{'total':<8}{format_cents(sum(totals.values()), '$'):>14}")
    return lines
