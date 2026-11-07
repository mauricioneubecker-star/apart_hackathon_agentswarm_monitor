from typing import Dict, Mapping, Optional, Sequence

from routekit.shortest_path import shortest_path


def assign_depots(adj: Mapping[str, Mapping[str, int]], depots: Sequence[str], customers: Sequence[str]) -> Dict[str, Optional[str]]:
    for code in [*depots, *customers]:
        if code not in adj:
            raise KeyError(code)
    result: Dict[str, Optional[str]] = {}
    for customer in customers:
        best = None
        for depot in depots:
            route = shortest_path(adj, depot, customer)
            if route is None:
                continue
            key = (route[0], len(route[1]), depot)
            if best is None or key < best:
                best = key
        result[customer] = best[2] if best else None
    return result
