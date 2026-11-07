from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def truncate_text(text: str, max_chars: int, ellipsis: str = "...") -> str:
    """
    Shorten `text` for previews and teasers without cutting words in half.

    The text is first cleaned with normalize_whitespace(). If the cleaned text has
    at most `max_chars` characters it is returned as is. Otherwise the result is the
    longest run of whole leading words (joined by single spaces) such that the
    words plus `ellipsis` fit in max_chars characters, followed by `ellipsis`. If
    not even the first word fits, the first word is hard-cut so that the result is
    exactly max_chars characters long. Raises ValueError if
    max_chars <= len(ellipsis).

    Examples:
        truncate_text("The quick brown fox jumps", 15) == "The quick..."
        truncate_text("Short text", 50) == "Short text"
    """
    raise NotImplementedError
