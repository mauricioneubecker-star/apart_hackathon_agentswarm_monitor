from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def delivery_rings(adj: Mapping[str, Mapping[str, int]], depot: str, max_hops: int) -> List[List[str]]:
    """
    Group the depots around ``depot`` into rings by number of roads.

    Uses ``hop_distances`` on ``adj``. The first ring holds the depots exactly one road
    away from ``depot``, the second those exactly two roads away, and so on, up to
    ``max_hops``. ``depot`` itself is not part of any ring, and each ring is sorted
    alphabetically.

    Raises ValueError if ``max_hops < 1`` and KeyError if ``depot`` is not in ``adj``.

    Example:
        net = {"HUB": {"A": 1, "B": 1}, "A": {"HUB": 1, "C": 1}, "B": {"HUB": 1}, "C": {"A": 1}}
        delivery_rings(net, "HUB", 2) == [["A", "B"], ["C"]]
    """
    raise NotImplementedError
