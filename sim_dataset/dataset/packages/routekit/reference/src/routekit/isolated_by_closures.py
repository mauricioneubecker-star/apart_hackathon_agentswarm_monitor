from typing import Iterable, List, Tuple

from routekit.build_adjacency import build_adjacency
from routekit.hop_distances import hop_distances


def isolated_by_closures(edges: Iterable[Tuple[str, str, int]], depot: str, closed: Iterable[Tuple[str, str]], directed: bool = False) -> List[str]:
    edges = list(edges)
    before = hop_distances(build_adjacency(edges, directed), depot)
    blocked = {frozenset(pair) for pair in closed}
    kept = [road for road in edges if frozenset(road[:2]) not in blocked]
    reduced = build_adjacency(kept, directed)
    after = hop_distances(reduced, depot) if depot in reduced else {depot: 0}
    return sorted(set(before) - set(after))
