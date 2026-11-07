from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def similarity(a: str, b: str) -> float:
    """
    Return a similarity score between 0.0 and 1.0 for two strings, based on
    edit_distance():

        score = 1 - edit_distance(a, b) / max(len(a), len(b))

    rounded to 2 decimal places with round(). Two empty strings score 1.0.

    Examples:
        similarity("kitten", "sitting") == 0.57
        similarity("abc", "abc") == 1.0
    """
    raise NotImplementedError
