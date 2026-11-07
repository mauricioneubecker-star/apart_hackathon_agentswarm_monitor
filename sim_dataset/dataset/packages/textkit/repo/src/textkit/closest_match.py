from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def closest_match(word: str, vocabulary: Iterable[str], max_distance: int = 2) -> Optional[str]:
    """
    Suggest the vocabulary entry closest to `word` (the "did you mean ...?" hint
    under the search box).

    Distances are computed with edit_distance() on the lowercased strings. Returns
    the entry with the smallest distance, provided that distance is <=
    max_distance; returns None when nothing is close enough or the vocabulary is
    empty. When several entries share the smallest distance, the one that appears
    first in `vocabulary` wins. The entry is returned with its original spelling.
    Raises ValueError if max_distance is negative.

    Examples:
        closest_match("pyhton", ["python", "pandas"]) == "python"
        closest_match("zzz", ["python"]) is None
    """
    raise NotImplementedError
