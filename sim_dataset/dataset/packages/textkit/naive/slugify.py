import re
import unicodedata
from typing import Optional

from textkit.tokenize_words import tokenize_words


def slugify(text: str, max_length: Optional[int] = None) -> str:
    if max_length is not None and max_length < 1:
        raise ValueError("max_length must be >= 1")
    words = []
    for token in tokenize_words(text):
        ascii_word = unicodedata.normalize("NFKD", token).encode("ascii", "ignore").decode("ascii")
        ascii_word = re.sub(r"[^a-z0-9]", "", ascii_word.lower())
        if ascii_word:
            words.append(ascii_word)
    slug = "-".join(words)
    if max_length is not None:
        slug = slug[:max_length].rstrip("-")
    return slug
