from typing import Dict, Mapping


def percent_shares(counts: Mapping[str, int]) -> Dict[str, int]:
    if not counts:
        raise ValueError("counts must not be empty")
    for name, count in counts.items():
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"invalid count for {name!r}: {count!r}")
    total = sum(counts.values())
    if total == 0:
        raise ValueError("total count is zero")
    shares = {name: count * 100 // total for name, count in counts.items()}
    remainders = {name: count * 100 % total for name, count in counts.items()}
    leftover = 100 - sum(shares.values())
    order = sorted(counts, key=lambda name: (-remainders[name], name))
    for name in order[:leftover]:
        shares[name] += 1
    return shares
