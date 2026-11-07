from typing import Dict, Mapping, Optional, Sequence

from routekit.shortest_path import shortest_path


def assign_depots(adj: Mapping[str, Mapping[str, int]], depots: Sequence[str], customers: Sequence[str]) -> Dict[str, Optional[str]]:
    for code in [*depots, *customers]:
        if code not in adj:
            raise KeyError(code)
    result: Dict[str, Optional[str]] = {}
    for customer in customers:
        best_depot, best_km = None, None
        for depot in depots:
            route = shortest_path(adj, depot, customer)
            if route is None:
                continue
            if best_km is None or route[0] < best_km:
                best_depot, best_km = depot, route[0]
        result[customer] = best_depot
    return result
