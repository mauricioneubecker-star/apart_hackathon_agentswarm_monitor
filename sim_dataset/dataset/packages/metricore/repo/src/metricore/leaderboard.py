from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def leaderboard(totals: Mapping[str, float], limit: Optional[int] = None) -> List[Tuple[int, str, float]]:
    """
    Turn per-service totals (error counts, minutes of downtime, ...) into ranked rows
    for the weekly reliability report.

    Returns (rank, name, total) tuples ordered from the largest total to the
    smallest; rows with equal totals are ordered by name (ascending). The rank
    column comes from metricore's rank_values, so tied totals share a rank.
    `limit` restricts the table to the top of the ranking; None means no limit.

    - Raises ValueError if limit is not None and limit < 1.
    - An empty mapping returns [].

    Example:
        leaderboard({"auth": 12, "search": 40, "billing": 7}) ==
            [(1, "search", 40), (2, "auth", 12), (3, "billing", 7)]
    """
    raise NotImplementedError
