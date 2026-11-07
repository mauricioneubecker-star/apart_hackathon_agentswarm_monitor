from datetime import date, timedelta


def due_date(invoice_date: str, net_days: int) -> str:
    if net_days < 0:
        raise ValueError("net_days must not be negative")
    return (date.fromisoformat(invoice_date) + timedelta(days=net_days)).isoformat()
