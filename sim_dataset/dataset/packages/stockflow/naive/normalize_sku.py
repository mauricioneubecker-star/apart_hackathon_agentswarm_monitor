import re

_SKU_RE = re.compile(r"([A-Z]{3})-([0-9]{6})-([0-9])")


def normalize_sku(code: str) -> str:
    m = _SKU_RE.fullmatch(code.strip().upper())
    if not m:
        raise ValueError(f"malformed SKU: {code!r}")
    prefix, digits, check = m.groups()
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(digits))
    if (10 - total % 10) % 10 != int(check):
        raise ValueError(f"bad check digit in SKU: {code!r}")
    return f"{prefix}-{digits}-{check}"
