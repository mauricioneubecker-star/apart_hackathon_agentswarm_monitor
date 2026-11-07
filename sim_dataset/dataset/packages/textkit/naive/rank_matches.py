from typing import List, Sequence, Tuple

from textkit.similarity import similarity


def rank_matches(query: str, candidates: Sequence[str], limit: int = 5,
                 min_score: float = 0.0) -> List[Tuple[str, float]]:
    if limit < 0:
        raise ValueError("limit must be >= 0")
    scores = {}
    for candidate in candidates:
        if candidate not in scores:
            scores[candidate] = similarity(query, candidate)
    kept = [(c, s) for c, s in scores.items() if s >= min_score]
    kept.sort(key=lambda pair: (-pair[1], pair[0]))
    return kept[:limit]
