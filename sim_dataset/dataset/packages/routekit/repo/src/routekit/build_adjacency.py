from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def build_adjacency(edges: Iterable[Tuple[str, str, int]], directed: bool = False) -> Dict[str, Dict[str, int]]:
    """
    Build an adjacency map from a list of roads.

    ``edges`` contains ``(from_code, to_code, km)`` tuples as returned by ``parse_edge``.
    The result maps every depot code to a dict ``{neighbour_code: km}``.

    * ``directed=False`` (default): every road can be used both ways and is entered
      under both of its depots.
    * ``directed=True``: a road is only entered under its ``from_code``; the ``to_code``
      still becomes a key (with an empty dict if it has no outgoing roads).

    Self-loops (``from_code == to_code``) are not entered as neighbours, but the depot
    still appears as a key. An empty edge list gives ``{}``. The input is not modified.

    Example:
        build_adjacency([("A", "B", 4), ("B", "C", 2)]) == {"A": {"B": 4}, "B": {"A": 4, "C": 2}, "C": {"B": 2}}
    """
    raise NotImplementedError
