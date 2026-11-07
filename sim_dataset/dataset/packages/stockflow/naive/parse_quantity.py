import re

_QTY_RE = re.compile(r"([+-]?[0-9]+)\s*([A-Za-z]+)")


def parse_quantity(text: str, case_size: int) -> int:
    if case_size < 1:
        raise ValueError("case_size must be >= 1")
    m = _QTY_RE.fullmatch(text.strip())
    if not m:
        raise ValueError(f"malformed quantity: {text!r}")
    amount = int(m.group(1))
    unit = m.group(2).upper()
    if unit == "EA":
        return amount
    if unit == "CS":
        return amount * case_size
    raise ValueError(f"unknown unit of measure: {unit!r}")
