import re
from typing import Optional


def next_credit_note_number(last_number: Optional[str], year: int) -> str:
    sequence = 1
    if last_number is not None:
        match = re.fullmatch(r"CN-(\d{4})-(\d{4,})", last_number)
        if not match:
            raise ValueError(f"malformed credit note number: {last_number!r}")
        sequence = int(match.group(2)) + 1
    return f"CN-{year}-{sequence:04d}"
