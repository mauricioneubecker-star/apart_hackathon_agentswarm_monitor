from typing import List, Mapping, Optional, Tuple

from metricore.rank_values import rank_values


def leaderboard(totals: Mapping[str, float],
                limit: Optional[int] = None) -> List[Tuple[int, str, float]]:
    if limit is not None and limit < 1:
        raise ValueError("limit must be >= 1")
    names = sorted(totals, key=lambda name: (-totals[name], name))
    ranks = rank_values([totals[name] for name in names])
    rows = [(rank, name, totals[name]) for rank, name in zip(ranks, names)]
    return rows if limit is None else rows[:limit]
