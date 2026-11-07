import textwrap
from typing import List

from textkit.normalize_whitespace import normalize_whitespace


def wrap_text(text: str, width: int) -> List[str]:
    if width < 1:
        raise ValueError("width must be >= 1")
    return textwrap.wrap(normalize_whitespace(text), width)
