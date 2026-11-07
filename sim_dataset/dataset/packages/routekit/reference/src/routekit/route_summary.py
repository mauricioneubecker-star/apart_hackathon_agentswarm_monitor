from typing import Mapping, Optional

from routekit.format_route import format_route
from routekit.path_cost import path_cost
from routekit.shortest_path import shortest_path


def route_summary(adj: Mapping[str, Mapping[str, int]], origin: str, destination: str, cents_per_km: int, tolls: Optional[Mapping[str, int]] = None) -> str:
    found = shortest_path(adj, origin, destination)
    if found is None:
        return f"no route {origin} -> {destination}"
    km, path = found
    cents = path_cost(adj, path, cents_per_km, tolls)
    euros, rest = divmod(cents, 100)
    return f"{format_route(path, km)} | EUR {euros:,}.{rest:02d}"
