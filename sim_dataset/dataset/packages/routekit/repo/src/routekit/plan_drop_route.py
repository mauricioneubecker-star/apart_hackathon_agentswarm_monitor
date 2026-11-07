from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def plan_drop_route(adj: Mapping[str, Mapping[str, int]], origin: str, destination: str, drops: Sequence[str]) -> Optional[Tuple[int, List[str]]]:
    """
    Plan the shortest tour from ``origin`` to ``destination`` that visits all ``drops``.

    The drops may be visited in any order. For a given visiting order the route is the
    chain of ``shortest_path`` segments origin -> first drop -> ... -> last drop ->
    destination; segments are joined without repeating the depot where they meet.
    Returns ``(total_km, path)`` for the cheapest visiting order, or None if no order
    gives a complete route. With no drops this is simply the shortest route from
    ``origin`` to ``destination``.

    Raises ValueError if ``drops`` contains duplicates or more than 6 depots, and
    KeyError if ``origin``, ``destination`` or any drop is not in ``adj``.

    Example:
        net = {"S": {"A": 1, "B": 5}, "A": {"S": 1, "B": 1}, "B": {"S": 5, "A": 1, "T": 1}, "T": {"B": 1}}
        plan_drop_route(net, "S", "T", ["B", "A"]) == (3, ["S", "A", "B", "T"])
    """
    raise NotImplementedError
