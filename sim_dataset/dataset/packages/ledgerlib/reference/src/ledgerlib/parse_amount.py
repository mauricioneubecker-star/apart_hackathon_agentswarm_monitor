import re

_AMOUNT = re.compile(r"([+-]?)\$?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?")


def parse_amount(text: str) -> int:
    match = _AMOUNT.fullmatch(text.strip())
    if not match:
        raise ValueError(f"invalid amount: {text!r}")
    sign, whole, frac = match.groups()
    cents = int(whole.replace(",", "")) * 100 + int((frac or "").ljust(2, "0"))
    return -cents if sign == "-" else cents
