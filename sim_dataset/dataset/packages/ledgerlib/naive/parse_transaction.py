from datetime import date
from typing import Any, Dict

from ledgerlib.parse_amount import parse_amount


def parse_transaction(line: str) -> Dict[str, Any]:
    parts = [part.strip() for part in line.split(";")]
    if len(parts) != 4:
        raise ValueError(f"expected 4 fields: {line!r}")
    day, account, amount, memo = parts
    if len(day) != 10:
        raise ValueError(f"invalid date: {day!r}")
    date.fromisoformat(day)
    if not account:
        raise ValueError("missing account")
    return {"date": day, "account": account, "amount": parse_amount(amount), "memo": memo}
