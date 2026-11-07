from typing import Optional, Sequence, Tuple


def count_transfers(legs: Sequence[Tuple[str, str, Optional[str]]]) -> int:
    legs = list(legs)
    for prev, nxt in zip(legs, legs[1:]):
        if prev[1] != nxt[0]:
            raise ValueError(f"leg {nxt!r} does not start at {prev[1]!r}")
    transfers = 0
    current = None
    for _, _, line in legs:
        if line is None:
            continue
        if current is not None and line != current:
            transfers += 1
        current = line
    return transfers
