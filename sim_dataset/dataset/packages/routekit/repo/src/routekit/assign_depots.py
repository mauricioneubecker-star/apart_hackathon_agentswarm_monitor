from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def assign_depots(adj: Mapping[str, Mapping[str, int]], depots: Sequence[str], customers: Sequence[str]) -> Dict[str, Optional[str]]:
    """
    Assign each customer location to its nearest depot.

    The distance between a depot and a customer is the road distance from the depot to
    the customer as computed by ``shortest_path``. Returns a dict that maps every
    customer code to the code of its nearest depot, or to None if no depot can reach the
    customer. A customer location that is itself a depot is served by that depot.

    Raises KeyError if any depot or customer code is not in ``adj``.

    Example:
        net = {"D1": {"C1": 3}, "C1": {"D1": 3, "D2": 5}, "D2": {"C1": 5}}
        assign_depots(net, ["D1", "D2"], ["C1"]) == {"C1": "D1"}
    """
    raise NotImplementedError
