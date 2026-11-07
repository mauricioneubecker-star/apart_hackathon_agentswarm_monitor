from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def route_summary(adj: Mapping[str, Mapping[str, int]], origin: str, destination: str, cents_per_km: int, tolls: Optional[Mapping[str, int]] = None) -> str:
    """
    Produce the one-line dispatch summary for the shortest route between two depots.

    The route is found with ``shortest_path``, its cost with ``path_cost`` (km times
    ``cents_per_km`` plus tolls, in cents) and the route text with ``format_route``
    (including the km). The summary is that text followed by ``" | EUR "`` and the cost
    in euros with exactly two decimals. If ``destination`` cannot be reached, return
    ``"no route <origin> -> <destination>"``.

    Raises KeyError if ``origin`` or ``destination`` is not in ``adj``.

    Example:
        net = {"BER": {"LEI": 190}, "LEI": {"BER": 190, "DRE": 115}, "DRE": {"LEI": 115}}
        route_summary(net, "BER", "DRE", 150, {"LEI": 900}) == "BER > LEI > DRE (305 km) | EUR 466.50"
    """
    raise NotImplementedError
