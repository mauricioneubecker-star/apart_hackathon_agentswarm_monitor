from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def rank_matches(query: str, candidates: Sequence[str], limit: int = 5, min_score: float = 0.0) -> List[Tuple[str, float]]:
    """
    Rank `candidates` by how closely they match `query` and return the best ones
    as (candidate, score) pairs, best score first. Used by the tag picker.

    The score of a candidate is similarity(query, candidate). Candidates scoring
    below `min_score` are dropped, then at most `limit` pairs are returned.
    Duplicate candidate strings are only ranked once. `candidates` is not modified.
    Raises ValueError if limit < 0.

    Example:
        rank_matches("python", ["java", "python", "pythons"], limit=2)
            == [("python", 1.0), ("pythons", 0.86)]
    """
    raise NotImplementedError
