import re

_LOC_RE = re.compile(r"([A-Z])-([0-9]{2})-([0-9]{2})-([0-9])")


def parse_location(code: str) -> tuple:
    m = _LOC_RE.fullmatch(code.strip().upper())
    if not m:
        raise ValueError(f"malformed location: {code!r}")
    return (m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)))
