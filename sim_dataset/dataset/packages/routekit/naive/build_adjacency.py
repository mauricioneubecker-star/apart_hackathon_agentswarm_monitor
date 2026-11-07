from typing import Dict, Iterable, Tuple


def build_adjacency(edges: Iterable[Tuple[str, str, int]], directed: bool = False) -> Dict[str, Dict[str, int]]:
    adj: Dict[str, Dict[str, int]] = {}
    for a, b, km in edges:
        adj.setdefault(a, {})
        adj.setdefault(b, {})
        if a == b:
            continue
        adj[a][b] = km
        if not directed:
            adj[b][a] = km
    return adj
