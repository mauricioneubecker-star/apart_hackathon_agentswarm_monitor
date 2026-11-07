from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def shortest_path(adj: Mapping[str, Mapping[str, int]], src: str, dst: str) -> Optional[Tuple[int, List[str]]]:
    """
    Find the shortest route by road length between two depots.

    ``adj`` is an adjacency map as built by ``build_adjacency`` (directed or not) with
    non-negative km values. Returns ``(total_km, path)`` where ``path`` lists the depot
    codes from ``src`` to ``dst`` inclusive; ``src == dst`` gives ``(0, [src])``.
    Returns None when ``dst`` cannot be reached from ``src``.

    Real networks often contain several routes of equal length; the function must
    always return the same route for the same network, independent of dict insertion
    order.

    Raises KeyError if ``src`` or ``dst`` is not a key of ``adj``.

    Example:
        net = {"A": {"B": 2}, "B": {"A": 2, "C": 3}, "C": {"B": 3}}
        shortest_path(net, "A", "C") == (5, ["A", "B", "C"])
    """
    raise NotImplementedError
