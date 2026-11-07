import heapq
from typing import List, Mapping, Optional, Tuple


def shortest_path(adj: Mapping[str, Mapping[str, int]], src: str, dst: str) -> Optional[Tuple[int, List[str]]]:
    for code in (src, dst):
        if code not in adj:
            raise KeyError(code)
    dist = {src: 0}
    prev = {}
    heap = [(0, src)]
    done = set()
    while heap:
        cost, node = heapq.heappop(heap)
        if node in done:
            continue
        done.add(node)
        if node == dst:
            break
        neighbours = adj.get(node, {})
        for nxt in sorted(neighbours):
            new_cost = cost + neighbours[nxt]
            if nxt not in dist or new_cost < dist[nxt]:
                dist[nxt] = new_cost
                prev[nxt] = node
                heapq.heappush(heap, (new_cost, nxt))
    if dst not in done:
        return None
    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])
    return dist[dst], path[::-1]
