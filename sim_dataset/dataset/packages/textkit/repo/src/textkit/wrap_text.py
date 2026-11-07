from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def wrap_text(text: str, width: int) -> List[str]:
    """
    Greedy word-wrap `text` into lines of at most `width` characters (used for
    plain-text emails).

    The text is cleaned with normalize_whitespace() and split into words on spaces.
    Words are added to the current line, separated by single spaces, as long as the
    line stays within `width`; otherwise a new line is started with that word. Lines
    have no leading or trailing spaces. Empty or whitespace-only text gives [].
    Raises ValueError if width < 1.

    Example:
        wrap_text("the quick brown fox jumps over the lazy dog", 10)
            == ["the quick", "brown fox", "jumps over", "the lazy", "dog"]
    """
    raise NotImplementedError
