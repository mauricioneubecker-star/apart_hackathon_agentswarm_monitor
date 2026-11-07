import re
from typing import List

_TOKEN_RE = re.compile(r"[^\W_]+(?:(?<=[^\W\d_])'(?=[^\W\d_])[^\W_]+)*")


def tokenize_words(text: str) -> List[str]:
    text = text.replace("’", "'")
    return [token.lower() for token in _TOKEN_RE.findall(text)]
