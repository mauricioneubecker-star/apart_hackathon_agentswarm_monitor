from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def count_syllables(word: str) -> int:
    """
    Estimate the number of syllables in an English word (heuristic used by the
    readability score).

    The word is lowercased and every character other than a-z is removed. Then:
      1. Count the groups of consecutive vowels, where vowels are a, e, i, o, u, y.
      2. Silent e: if the word ends in "e" and there is more than one vowel group,
         subtract 1 ("cake" -> 1, while "the" stays 1).
      3. The result is never below 1 for a word that has at least one letter.
    A word with no letters a-z at all returns 0.

    Examples:
        count_syllables("readability") == 5
        count_syllables("cake") == 1
    """
    raise NotImplementedError
