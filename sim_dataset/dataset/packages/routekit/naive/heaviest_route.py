import heapq
from typing import List, Mapping, Optional, Tuple


def heaviest_route(limits: Mapping[str, Mapping[str, int]], src: str, dst: str) -> Optional[Tuple[int, List[str]]]:
    for code in (src, dst):
        if code not in limits:
            raise KeyError(code)
    if src == dst:
        raise ValueError("src and dst must differ")
    best = {src: float("inf")}
    prev = {}
    heap = [(-best[src], src)]
    done = set()
    while heap:
        neg_load, node = heapq.heappop(heap)
        if node in done:
            continue
        done.add(node)
        roads = limits.get(node, {})
        for nxt in sorted(roads):
            load = min(-neg_load, roads[nxt])
            if nxt not in best or load > best[nxt]:
                best[nxt] = load
                prev[nxt] = node
                heapq.heappush(heap, (-load, nxt))
    if dst not in best:
        return None
    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])
    return best[dst], path[::-1]
