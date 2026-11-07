from typing import Iterable, List, Tuple

from routekit.build_adjacency import build_adjacency


def hub_depots(edges: Iterable[Tuple[str, str, int]], top_n: int) -> List[Tuple[str, int]]:
    if top_n < 1:
        raise ValueError("top_n must be at least 1")
    adj = build_adjacency(edges)
    ranked = sorted(((code, len(nbrs)) for code, nbrs in adj.items()), key=lambda item: (-item[1], item[0]))
    if len(ranked) <= top_n:
        return ranked
    cutoff = ranked[top_n - 1][1]
    return [item for item in ranked if item[1] >= cutoff]
