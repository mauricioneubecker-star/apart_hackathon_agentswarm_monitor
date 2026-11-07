from typing import Dict, Iterable, List, Tuple


def min_spanning_tree(edges: Iterable[Tuple[str, str, int]]) -> List[Tuple[str, str, int]]:
    roads = []
    for a, b, km in edges:
        if a == b:
            continue
        a, b = sorted((a, b))
        roads.append((km, a, b))
    parent: Dict[str, str] = {}

    def find(code: str) -> str:
        parent.setdefault(code, code)
        while parent[code] != code:
            parent[code] = parent[parent[code]]
            code = parent[code]
        return code

    chosen = []
    for km, a, b in sorted(roads):
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_a] = root_b
            chosen.append((a, b, km))
    return sorted(chosen, key=lambda road: (road[2], road[0], road[1]))
