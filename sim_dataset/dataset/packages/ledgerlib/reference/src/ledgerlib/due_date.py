from datetime import date, timedelta


def due_date(invoice_date: str, net_days: int) -> str:
    if net_days < 0:
        raise ValueError("net_days must not be negative")
    due = date.fromisoformat(invoice_date) + timedelta(days=net_days)
    if due.weekday() >= 5:
        due += timedelta(days=7 - due.weekday())
    return due.isoformat()
