from typing import List

from textkit.normalize_whitespace import normalize_whitespace


def wrap_text(text: str, width: int) -> List[str]:
    if width < 1:
        raise ValueError("width must be >= 1")
    lines: List[str] = []
    current = ""
    for word in normalize_whitespace(text).split():
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
