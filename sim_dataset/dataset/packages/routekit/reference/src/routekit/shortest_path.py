import heapq
from typing import List, Mapping, Optional, Tuple


def shortest_path(adj: Mapping[str, Mapping[str, int]], src: str, dst: str) -> Optional[Tuple[int, List[str]]]:
    for code in (src, dst):
        if code not in adj:
            raise KeyError(code)
    heap = [(0, 0, [src])]
    done = set()
    while heap:
        cost, legs, path = heapq.heappop(heap)
        node = path[-1]
        if node in done:
            continue
        if node == dst:
            return cost, path
        done.add(node)
        for nxt, km in adj.get(node, {}).items():
            if nxt not in done:
                heapq.heappush(heap, (cost + km, legs + 1, path + [nxt]))
    return None
