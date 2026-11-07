from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def path_cost(adj: Mapping[str, Mapping[str, int]], path: Sequence[str], cents_per_km: int, tolls: Optional[Mapping[str, int]] = None) -> int:
    """
    Compute the transport cost of a given route in cents.

    ``path`` lists depot codes in travel order; each consecutive pair must be joined by
    a road in ``adj`` (``adj[a][b]``). The cost is the total road length times
    ``cents_per_km`` plus depot tolls: ``tolls`` maps depot codes to a fee in cents that
    is charged when a route passes through that depot (depots missing from ``tolls``
    are free). A single-depot path has no roads.

    Raises ValueError if ``path`` is empty or if two consecutive depots are not joined
    by a road (this includes unknown depot codes).

    Example:
        net = {"A": {"B": 4}, "B": {"A": 4, "C": 6}, "C": {"B": 6}}
        path_cost(net, ["A", "B", "C"], 100, {"B": 250}) == 1250
    """
    raise NotImplementedError
