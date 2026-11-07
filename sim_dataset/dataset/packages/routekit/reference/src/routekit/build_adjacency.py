from typing import Dict, Iterable, Tuple


def build_adjacency(edges: Iterable[Tuple[str, str, int]], directed: bool = False) -> Dict[str, Dict[str, int]]:
    adj: Dict[str, Dict[str, int]] = {}

    def add(a: str, b: str, km: int) -> None:
        row = adj[a]
        if b not in row or km < row[b]:
            row[b] = km

    for a, b, km in edges:
        adj.setdefault(a, {})
        adj.setdefault(b, {})
        if a == b:
            continue
        add(a, b, km)
        if not directed:
            add(b, a, km)
    return adj
