from collections import Counter
from typing import Iterable, List, Optional, Tuple

from textkit.tokenize_words import tokenize_words


def top_words(text: str, k: int, stopwords: Optional[Iterable[str]] = None) -> List[Tuple[str, int]]:
    if k < 0:
        raise ValueError("k must be >= 0")
    skip = {word.lower() for word in (stopwords or ())}
    counts = Counter(w for w in tokenize_words(text) if w not in skip and not w.isdigit())
    return counts.most_common(k)
