from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def depot_workload(adj: Mapping[str, Mapping[str, int]], depots: Sequence[str], customers: Sequence[str]) -> Dict[str, List[str]]:
    """
    Summarise which customers each depot serves.

    Customers are assigned with ``assign_depots``. Returns a dict mapping depot codes to
    the alphabetically sorted list of customers assigned to them. Customers that no
    depot can reach are left out of the result.

    Raises KeyError if any code is not in ``adj`` (as ``assign_depots`` does).

    Example:
        net = {"D1": {"C1": 3, "C2": 1}, "C1": {"D1": 3}, "C2": {"D1": 1}}
        depot_workload(net, ["D1"], ["C2", "C1"]) == {"D1": ["C1", "C2"]}
    """
    raise NotImplementedError
