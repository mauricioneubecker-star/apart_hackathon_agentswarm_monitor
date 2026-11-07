from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def make_acronym(phrase: str) -> str:
    """
    Build an acronym from the first character of each word of `phrase`.

    Words come from tokenize_words(), so hyphenated parts count as separate words
    ("self-contained" contributes "SC"). Letters are upper-cased; a word that starts
    with a digit contributes that digit. Returns "" when the phrase has no words.

    Examples:
        make_acronym("Portable Network Graphics") == "PNG"
        make_acronym("self-contained underwater breathing apparatus") == "SCUBA"
    """
    raise NotImplementedError
