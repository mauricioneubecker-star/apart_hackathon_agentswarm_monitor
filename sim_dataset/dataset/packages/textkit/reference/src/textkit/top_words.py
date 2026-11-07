from typing import Iterable, List, Optional, Tuple

from textkit.tokenize_words import tokenize_words


def top_words(text: str, k: int, stopwords: Optional[Iterable[str]] = None) -> List[Tuple[str, int]]:
    if k < 0:
        raise ValueError("k must be >= 0")
    skip = {word.lower() for word in (stopwords or ())}
    counts = {}
    for word in tokenize_words(text):
        if word in skip or word.isdigit():
            continue
        counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:k]
