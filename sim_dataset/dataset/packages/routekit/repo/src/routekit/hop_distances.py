from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def hop_distances(adj: Mapping[str, Mapping[str, int]], source: str, max_hops: Optional[int] = None) -> Dict[str, int]:
    """
    Count the number of roads (hops) from ``source`` to every depot it can reach.

    ``adj`` is an adjacency map as built by ``build_adjacency`` (directed or not); road
    lengths are ignored. The result maps each reachable depot to its minimum hop count;
    ``source`` itself is included with 0. With ``max_hops`` set, only depots at most
    ``max_hops`` roads away are included.

    Raises KeyError if ``source`` is not a key of ``adj``.

    Example:
        hop_distances({"A": {"B": 3}, "B": {"A": 3, "C": 1}, "C": {"B": 1}}, "A") == {"A": 0, "B": 1, "C": 2}
    """
    raise NotImplementedError
