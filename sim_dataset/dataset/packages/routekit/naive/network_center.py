from typing import Mapping

from routekit.hop_distances import hop_distances


def network_center(adj: Mapping[str, Mapping[str, int]]) -> str:
    if not adj:
        raise ValueError("empty network")
    best = None
    for code in sorted(adj):
        dist = hop_distances(adj, code)
        if any(other not in dist for other in adj):
            continue
        ecc = max(dist.values())
        if best is None or ecc < best[0]:
            best = (ecc, code)
    if best is None:
        raise ValueError("no depot reaches every other depot")
    return best[1]
