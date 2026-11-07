import re

_SKU_RE = re.compile(r"([A-Z]{3})(-?)([0-9]{6})\2([0-9])")


def _check_digit(digits: str) -> int:
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(digits))
    return (10 - total % 10) % 10


def normalize_sku(code: str) -> str:
    if not isinstance(code, str):
        raise ValueError("SKU must be a string")
    m = _SKU_RE.fullmatch(code.strip().upper())
    if not m:
        raise ValueError(f"malformed SKU: {code!r}")
    prefix, _sep, digits, check = m.groups()
    if _check_digit(digits) != int(check):
        raise ValueError(f"bad check digit in SKU: {code!r}")
    return f"{prefix}-{digits}-{check}"
