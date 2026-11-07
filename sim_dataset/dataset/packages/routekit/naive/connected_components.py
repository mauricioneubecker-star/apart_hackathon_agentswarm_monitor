from typing import Iterable, List, Tuple

from routekit.build_adjacency import build_adjacency


def connected_components(edges: Iterable[Tuple[str, str, int]], depots: Iterable[str] = ()) -> List[List[str]]:
    adj = build_adjacency(edges)
    for code in depots:
        adj.setdefault(code, {})
    seen = set()
    regions = []
    for start in adj:
        if start in seen:
            continue
        seen.add(start)
        stack, region = [start], []
        while stack:
            node = stack.pop()
            region.append(node)
            for nxt in adj[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        regions.append(sorted(region))
    return sorted(regions)
