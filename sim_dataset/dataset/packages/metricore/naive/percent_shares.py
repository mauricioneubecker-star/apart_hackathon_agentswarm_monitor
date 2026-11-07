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
    shares = {}
    remainders = {}
    for name, count in counts.items():
        shares[name], remainders[name] = divmod(count * 100, total)
    leftover = 100 - sum(shares.values())
    for name in sorted(remainders, key=remainders.get, reverse=True)[:leftover]:
        shares[name] += 1
    return shares
