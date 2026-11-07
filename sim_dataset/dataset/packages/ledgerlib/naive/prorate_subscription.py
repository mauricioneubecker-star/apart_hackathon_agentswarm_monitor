from datetime import date

from ledgerlib.round_div import round_div


def prorate_subscription(price_cents: int, period_start: str, period_end: str, active_from: str) -> int:
    start = date.fromisoformat(period_start)
    end = date.fromisoformat(period_end)
    active = date.fromisoformat(active_from)
    if end < start:
        raise ValueError("period_end is before period_start")
    if active > end:
        return 0
    if active <= start:
        return price_cents
    return round_div(price_cents * (end - active).days, (end - start).days)
