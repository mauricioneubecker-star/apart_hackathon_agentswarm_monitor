from typing import Mapping, Optional, Sequence


def path_cost(adj: Mapping[str, Mapping[str, int]], path: Sequence[str], cents_per_km: int, tolls: Optional[Mapping[str, int]] = None) -> int:
    if not path:
        raise ValueError("empty route")
    km = 0
    for a, b in zip(path, path[1:]):
        if b not in adj.get(a, {}):
            raise ValueError(f"no road {a}-{b}")
        km += adj[a][b]
    fees = tolls or {}
    return km * cents_per_km + sum(fees.get(stop, 0) for stop in path)
