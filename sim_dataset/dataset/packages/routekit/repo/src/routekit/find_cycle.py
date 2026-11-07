from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def find_cycle(edges: Iterable[Tuple[str, str, int]]) -> Optional[List[str]]:
    """
    Detect a circular chain of transfers in a directed transfer network.

    The network is built with ``build_adjacency(edges, directed=True)``, so self-loops
    are ignored. The search is a depth-first search that starts from depots in
    alphabetical order and follows outgoing roads in alphabetical order of the target
    depot; the cycle reported is the first one closed by this search (the first road
    found that leads back to a depot on the current search path).

    Returns None if there is no cycle. Otherwise returns the cycle as a closed list of
    depot codes ``[c0, c1, ..., ck, c0]`` in which each consecutive pair is a road.

    Examples:
        find_cycle([("A", "B", 1), ("B", "C", 1), ("C", "A", 1)]) == ["A", "B", "C", "A"]
        find_cycle([("A", "B", 1), ("B", "C", 1)]) is None
    """
    raise NotImplementedError
