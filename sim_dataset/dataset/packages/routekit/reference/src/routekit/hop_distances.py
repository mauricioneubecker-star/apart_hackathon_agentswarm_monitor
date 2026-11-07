from collections import deque
from typing import Dict, Mapping, Optional


def hop_distances(adj: Mapping[str, Mapping[str, int]], source: str, max_hops: Optional[int] = None) -> Dict[str, int]:
    if source not in adj:
        raise KeyError(source)
    dist = {source: 0}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        if max_hops is not None and dist[node] >= max_hops:
            continue
        for nxt in adj.get(node, {}):
            if nxt not in dist:
                dist[nxt] = dist[node] + 1
                queue.append(nxt)
    return dict(sorted(dist.items(), key=lambda item: (item[1], item[0])))
