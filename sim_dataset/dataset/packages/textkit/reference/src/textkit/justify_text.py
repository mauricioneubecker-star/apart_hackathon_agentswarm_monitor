from typing import List

from textkit.wrap_text import wrap_text


def justify_text(text: str, width: int) -> List[str]:
    if width < 1:
        raise ValueError("width must be >= 1")
    lines = wrap_text(text, width)
    result = []
    for index, line in enumerate(lines):
        words = line.split(" ")
        is_last = index == len(lines) - 1
        if len(line) >= width or is_last or len(words) == 1:
            result.append(line.ljust(width))
            continue
        gaps = len(words) - 1
        spaces = width - sum(len(word) for word in words)
        base, extra = divmod(spaces, gaps)
        parts = [word + " " * (base + (1 if i < extra else 0)) for i, word in enumerate(words[:-1])]
        result.append("".join(parts) + words[-1])
    return result
