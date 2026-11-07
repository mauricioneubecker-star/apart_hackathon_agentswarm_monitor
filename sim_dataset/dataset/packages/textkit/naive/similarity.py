from textkit.edit_distance import edit_distance


def similarity(a: str, b: str) -> float:
    longest = max(len(a), len(b))
    if longest == 0:
        return 1.0
    return round(1 - edit_distance(a, b) / longest, 2)
