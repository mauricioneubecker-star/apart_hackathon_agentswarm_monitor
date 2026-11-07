from typing import Dict, Iterable, List, Tuple

from routekit.build_adjacency import build_adjacency


def _connected(adj: Dict[str, Dict[str, int]], a: str, b: str) -> bool:
    if a not in adj or b not in adj:
        return False
    seen, stack = {a}, [a]
    while stack:
        node = stack.pop()
        if node == b:
            return True
        for nxt in adj[node]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False


def critical_roads(edges: Iterable[Tuple[str, str, int]]) -> List[Tuple[str, str]]:
    roads = [(a, b, km) for a, b, km in edges if a != b]
    pairs = sorted({(min(a, b), max(a, b)) for a, b, _ in roads})
    result = []
    for pair in pairs:
        rest = [road for road in roads if (min(road[:2]), max(road[:2])) != pair]
        if not _connected(build_adjacency(rest), pair[0], pair[1]):
            result.append(pair)
    return result
