from typing import Iterable, Optional

from textkit.edit_distance import edit_distance


def closest_match(word: str, vocabulary: Iterable[str], max_distance: int = 2) -> Optional[str]:
    if max_distance < 0:
        raise ValueError("max_distance must be >= 0")
    limit = min(max_distance, 1) if len(word) <= 4 else max_distance
    target = word.lower()
    best, best_distance = None, None
    for entry in vocabulary:
        distance = edit_distance(target, entry.lower())
        if distance <= limit and (best_distance is None or distance < best_distance):
            best, best_distance = entry, distance
    return best
