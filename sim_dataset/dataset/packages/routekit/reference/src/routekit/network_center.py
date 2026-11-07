from typing import Mapping

from routekit.hop_distances import hop_distances


def network_center(adj: Mapping[str, Mapping[str, int]]) -> str:
    if not adj:
        raise ValueError("empty network")
    best = None
    for code in adj:
        dist = hop_distances(adj, code)
        if any(other not in dist for other in adj):
            continue
        key = (max(dist.values()), sum(dist.values()), code)
        if best is None or key < best:
            best = key
    if best is None:
        raise ValueError("no depot reaches every other depot")
    return best[2]
