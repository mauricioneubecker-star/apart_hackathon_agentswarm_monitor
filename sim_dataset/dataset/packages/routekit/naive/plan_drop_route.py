from itertools import permutations
from typing import List, Mapping, Optional, Sequence, Tuple

from routekit.shortest_path import shortest_path


def plan_drop_route(adj: Mapping[str, Mapping[str, int]], origin: str, destination: str, drops: Sequence[str]) -> Optional[Tuple[int, List[str]]]:
    if len(set(drops)) != len(drops):
        raise ValueError("duplicate drops")
    if len(drops) > 6:
        raise ValueError("at most 6 drops are supported")
    for code in [origin, destination, *drops]:
        if code not in adj:
            raise KeyError(code)
    best = None
    for order in permutations(sorted(drops)):
        stops = [origin, *order, destination]
        total, path = 0, [origin]
        for a, b in zip(stops, stops[1:]):
            segment = shortest_path(adj, a, b)
            if segment is None:
                break
            total += segment[0]
            path += segment[1][1:]
        else:
            if best is None or total < best[0]:
                best = (total, path)
    return best
