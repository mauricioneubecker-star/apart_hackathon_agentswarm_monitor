from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def justify_text(text: str, width: int) -> List[str]:
    """
    Fully justify `text` to a fixed column width for plain-text newsletters.

    Lines are produced with wrap_text(text, width). Every line except the last one
    is then stretched to exactly `width` characters by widening the gaps between
    its words: the extra spaces are spread as evenly as possible, and when they do
    not divide evenly the leftmost gaps get one more space than the others.
    The last line is left-aligned (single spaces between words), and so is any
    line that holds a single word. A line already longer than width (a single
    over-long word) is left as it is. Raises ValueError if width < 1.

    Example:
        justify_text("This is an example of text justification.", 16)[:2]
            == ["This    is    an", "example  of text"]
    """
    raise NotImplementedError
