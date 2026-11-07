from typing import List, Sequence, Tuple

from textkit.similarity import similarity


def rank_matches(query: str, candidates: Sequence[str], limit: int = 5,
                 min_score: float = 0.0) -> List[Tuple[str, float]]:
    if limit < 0:
        raise ValueError("limit must be >= 0")
    seen = set()
    scored = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        score = similarity(query, candidate)
        if score >= min_score:
            scored.append((candidate, score))
    scored.sort(key=lambda pair: -pair[1])
    return scored[:limit]
