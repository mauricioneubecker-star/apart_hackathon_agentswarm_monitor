import re

_LOC_RE = re.compile(r"([A-Z])-([0-9]{2})-([0-9]{2})-([0-9])")


def parse_location(code: str) -> tuple:
    m = _LOC_RE.fullmatch(code.strip().upper())
    if not m:
        raise ValueError(f"malformed location: {code!r}")
    zone = m.group(1)
    aisle, shelf, level = int(m.group(2)), int(m.group(3)), int(m.group(4))
    if aisle == 0 or shelf == 0:
        raise ValueError(f"aisle and shelf numbers start at 01: {code!r}")
    return (zone, aisle, shelf, level)
