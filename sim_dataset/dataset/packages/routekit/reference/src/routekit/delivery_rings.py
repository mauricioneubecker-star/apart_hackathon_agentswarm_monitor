from typing import List, Mapping

from routekit.hop_distances import hop_distances


def delivery_rings(adj: Mapping[str, Mapping[str, int]], depot: str, max_hops: int) -> List[List[str]]:
    if max_hops < 1:
        raise ValueError("max_hops must be at least 1")
    rings: List[List[str]] = []
    for code, hops in hop_distances(adj, depot, max_hops).items():
        if hops == 0:
            continue
        while len(rings) < hops:
            rings.append([])
        rings[hops - 1].append(code)
    return [sorted(ring) for ring in rings]
