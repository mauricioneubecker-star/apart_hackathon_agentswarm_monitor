from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def min_spanning_tree(edges: Iterable[Tuple[str, str, int]]) -> List[Tuple[str, str, int]]:
    """
    Select the cheapest set of roads that keeps every region connected (Kruskal).

    Roads are undirected ``(from_code, to_code, km)`` tuples. Roads are considered in
    order of increasing km, and a road is kept if it joins two depots that are not yet
    connected by previously kept roads. For a disconnected network the result is a
    spanning forest (one tree per region). Self-loops are ignored.

    Every returned road is normalised so that its first code is alphabetically smaller
    than the second, and the result is sorted by ``(km, first_code, second_code)``.
    An empty input gives ``[]``.

    Example:
        min_spanning_tree([("HAM", "BER", 289), ("BER", "LEI", 190), ("HAM", "LEI", 395)])
            == [("BER", "LEI", 190), ("BER", "HAM", 289)]
    """
    raise NotImplementedError
