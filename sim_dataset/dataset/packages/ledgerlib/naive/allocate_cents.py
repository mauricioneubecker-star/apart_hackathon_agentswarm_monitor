from typing import List, Sequence


def allocate_cents(total: int, weights: Sequence[int]) -> List[int]:
    if not weights or any(w < 0 for w in weights) or sum(weights) == 0:
        raise ValueError("weights must be non-empty, non-negative and not all zero")
    weight_sum = sum(weights)
    parts = [total * w // weight_sum for w in weights]
    remainders = [total * w % weight_sum for w in weights]
    missing = total - sum(parts)
    order = sorted(range(len(weights)), key=lambda i: (-remainders[i], i))
    for i in order[:missing]:
        parts[i] += 1
    return parts
