import re
from typing import List

from textkit.normalize_whitespace import normalize_whitespace

_ABBREVIATIONS = frozenset({"Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "St.", "vs.", "e.g.", "i.e."})
_ENDS = re.compile(r"[.!?]+[\"')\]]*$")
_STARTS = re.compile(r"[A-Z0-9\"'(\[]")
_INITIAL = re.compile(r"[\"'(\[]*[A-Z]\.$")


def split_sentences(text: str) -> List[str]:
    words = normalize_whitespace(text).split()
    sentences: List[str] = []
    current: List[str] = []
    for index, word in enumerate(words):
        current.append(word)
        if index + 1 == len(words):
            break
        if not _ENDS.search(word) or not _STARTS.match(words[index + 1]):
            continue
        if word.lstrip("\"'([") in _ABBREVIATIONS or _INITIAL.fullmatch(word):
            continue
        sentences.append(" ".join(current))
        current = []
    if current:
        sentences.append(" ".join(current))
    return sentences
