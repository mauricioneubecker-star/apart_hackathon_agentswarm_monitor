from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def connected_components(edges: Iterable[Tuple[str, str, int]], depots: Iterable[str] = ()) -> List[List[str]]:
    """
    Split the network into regions of depots connected by roads.

    Roads are undirected and the network is built with ``build_adjacency``. ``depots``
    optionally lists depots that must be included even if they have no roads; each such
    depot forms a region of its own. A depot whose only road is a self-loop is a region
    of its own as well.

    Returns a list of regions; each region is a list of depot codes sorted
    alphabetically. The order of the regions is canonical: it depends only on the
    regions themselves, never on the order of ``edges`` or ``depots``.

    Example:
        connected_components([("B", "A", 1), ("C", "B", 2)]) == [["A", "B", "C"]]
    """
    raise NotImplementedError
