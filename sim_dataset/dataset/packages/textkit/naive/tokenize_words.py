import re
from typing import List


def tokenize_words(text: str) -> List[str]:
    return [token.lower() for token in re.findall(r"[^\W_]+", text)]
