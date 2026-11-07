from typing import Optional, Sequence, Tuple


def count_transfers(legs: Sequence[Tuple[str, str, Optional[str]]]) -> int:
    legs = list(legs)
    for prev, nxt in zip(legs, legs[1:]):
        if prev[1] != nxt[0]:
            raise ValueError(f"leg {nxt!r} does not start at {prev[1]!r}")
    return sum(1 for prev, nxt in zip(legs, legs[1:]) if prev[2] != nxt[2])
