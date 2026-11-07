from typing import Iterable, Optional

from textkit.edit_distance import edit_distance


def closest_match(word: str, vocabulary: Iterable[str], max_distance: int = 2) -> Optional[str]:
    if max_distance < 0:
        raise ValueError("max_distance must be >= 0")
    target = word.lower()
    best, best_distance = None, None
    for entry in vocabulary:
        distance = edit_distance(target, entry.lower())
        if distance <= max_distance and (best_distance is None or distance < best_distance):
            best, best_distance = entry, distance
    return best
