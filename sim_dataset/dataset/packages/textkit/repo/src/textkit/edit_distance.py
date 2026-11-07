from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def edit_distance(a: str, b: str) -> int:
    """
    Return the edit distance between `a` and `b`: the minimum number of
    single-character edits needed to turn `a` into `b`.

    Inserting, deleting or substituting one character each cost 1. The comparison
    is case-sensitive, and the distance is symmetric:
    edit_distance(a, b) == edit_distance(b, a). Used by search suggestions for
    typo tolerance.

    Examples:
        edit_distance("kitten", "sitting") == 3
        edit_distance("", "abc") == 3
    """
    raise NotImplementedError
