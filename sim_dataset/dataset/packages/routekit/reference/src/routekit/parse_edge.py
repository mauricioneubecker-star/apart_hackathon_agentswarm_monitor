import re
from typing import Tuple

_RECORD = re.compile(r"^\s*([A-Za-z0-9]+)\s*-\s*([A-Za-z0-9]+)\s*:\s*(\d+)\s*$")


def parse_edge(line: str) -> Tuple[str, str, int]:
    match = _RECORD.match(line)
    if not match:
        raise ValueError(f"malformed road record: {line!r}")
    return match.group(1).upper(), match.group(2).upper(), int(match.group(3))
