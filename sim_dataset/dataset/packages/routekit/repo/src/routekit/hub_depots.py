from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def hub_depots(edges: Iterable[Tuple[str, str, int]], top_n: int) -> List[Tuple[str, int]]:
    """
    Rank depots by how many other depots they are directly connected to.

    The network is built with ``build_adjacency`` (undirected), so a depot's degree is
    the number of distinct neighbouring depots: repeated records of the same road and
    self-loops do not add to it. Returns ``(depot_code, degree)`` pairs sorted by degree
    (highest first) and then by depot code, cut to the ``top_n`` best-connected depots
    (fewer if the network has fewer depots).

    Raises ValueError if ``top_n < 1``.

    Example:
        hub_depots([("A", "B", 1), ("A", "C", 1), ("C", "D", 1)], 2) == [("A", 2), ("C", 2)]
    """
    raise NotImplementedError
