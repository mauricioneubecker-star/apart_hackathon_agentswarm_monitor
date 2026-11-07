import heapq
from typing import List, Mapping, Optional, Tuple


def heaviest_route(limits: Mapping[str, Mapping[str, int]], src: str, dst: str) -> Optional[Tuple[int, List[str]]]:
    for code in (src, dst):
        if code not in limits:
            raise KeyError(code)
    if src == dst:
        raise ValueError("src and dst must differ")
    best = {src: float("inf")}
    heap = [(-best[src], src)]
    while heap:
        neg_load, node = heapq.heappop(heap)
        if -neg_load < best[node]:
            continue
        for nxt, limit in limits.get(node, {}).items():
            load = min(-neg_load, limit)
            if load > best.get(nxt, 0):
                best[nxt] = load
                heapq.heappush(heap, (-load, nxt))
    if dst not in best:
        return None
    load = best[dst]
    heap = [(0, [src])]
    seen = set()
    while heap:
        legs, path = heapq.heappop(heap)
        node = path[-1]
        if node == dst:
            return load, path
        if node in seen:
            continue
        seen.add(node)
        for nxt, limit in limits.get(node, {}).items():
            if limit >= load and nxt not in seen:
                heapq.heappush(heap, (legs + 1, path + [nxt]))
    return None
