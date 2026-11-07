from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def tokenize_words(text: str) -> List[str]:
    """
    Split `text` into lowercase word tokens, in order of appearance.

    Tokens are made of letters and digits; matching is Unicode-aware, so accented
    words such as "café" or "naïve" are single tokens. Whitespace and
    punctuation (including underscores and hyphens) separate tokens and are
    discarded. Returns an empty list when the text contains no letters or digits.

    Examples:
        tokenize_words("Hello, World! 42 times") == ["hello", "world", "42", "times"]
        tokenize_words("state-of-the-art") == ["state", "of", "the", "art"]
    """
    raise NotImplementedError
