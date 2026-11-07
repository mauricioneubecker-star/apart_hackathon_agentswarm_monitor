import re


def parse_amount(text: str) -> int:
    match = re.fullmatch(r"([+-]?)\$?([\d,]+)(?:\.(\d{1,2}))?", text.strip())
    if not match or not match.group(2).replace(",", ""):
        raise ValueError(f"invalid amount: {text!r}")
    sign, whole, frac = match.groups()
    cents = int(whole.replace(",", "")) * 100 + int((frac or "").ljust(2, "0"))
    return -cents if sign == "-" else cents
