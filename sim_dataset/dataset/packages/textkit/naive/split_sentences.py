import re
from typing import List

from textkit.normalize_whitespace import normalize_whitespace

_ABBREVIATIONS = ("Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "St.", "vs.", "e.g.", "i.e.")


def split_sentences(text: str) -> List[str]:
    words = normalize_whitespace(text).split()
    sentences: List[str] = []
    current: List[str] = []
    for index, word in enumerate(words):
        current.append(word)
        if index + 1 == len(words):
            break
        nxt = words[index + 1]
        ends = re.search(r"[.!?]+[\"')\]]*$", word) is not None
        starts = re.match(r"[A-Z0-9\"'(\[]", nxt) is not None
        if ends and starts and word.lstrip("\"'([") not in _ABBREVIATIONS:
            sentences.append(" ".join(current))
            current = []
    if current:
        sentences.append(" ".join(current))
    return sentences
