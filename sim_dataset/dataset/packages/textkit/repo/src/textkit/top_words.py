from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def top_words(text: str, k: int, stopwords: Optional[Iterable[str]] = None) -> List[Tuple[str, int]]:
    """
    Return the `k` most frequent words of `text` as (word, count) pairs, most
    frequent first. Feeds the "top terms" panel of the article analytics page.

    Words come from tokenize_words(). Words listed in `stopwords` (compared
    case-insensitively) are ignored, and so are tokens made only of digits. If fewer
    than k distinct words remain, all of them are returned. Raises ValueError if
    k < 0.

    Examples:
        top_words("b a b c b a", 2) == [("b", 3), ("a", 2)]
        top_words("Data, data and more DATA", 1, stopwords=["and"]) == [("data", 3)]
    """
    raise NotImplementedError
