from datetime import date

from ledgerlib.due_date import due_date
from ledgerlib.round_div import round_div


def late_fee(balance_cents: int, invoice_date: str, net_days: int, paid_date: str,
             annual_rate_bp: int, grace_days: int = 0) -> int:
    if balance_cents < 0 or annual_rate_bp < 0 or grace_days < 0:
        raise ValueError("balance, rate and grace days must not be negative")
    due = date.fromisoformat(due_date(invoice_date, net_days))
    days_late = (date.fromisoformat(paid_date) - due).days
    if days_late <= grace_days:
        return 0
    return round_div(balance_cents * annual_rate_bp * days_late, 10000 * 365)
