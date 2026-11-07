from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def heaviest_route(limits: Mapping[str, Mapping[str, int]], src: str, dst: str) -> Optional[Tuple[int, List[str]]]:
    """
    Find the route that allows the heaviest truck from ``src`` to ``dst``.

    ``limits`` has the shape of an adjacency map, but each value is the weight limit of
    the road in tonnes (a positive integer). The load a route allows is the smallest
    limit along it. Returns ``(max_load, path)`` for a route whose allowed load is as
    large as possible, with ``path`` listing the depot codes from ``src`` to ``dst``.
    Returns None if ``dst`` cannot be reached. Several routes may allow the same load;
    the result must not depend on dict insertion order.

    Raises KeyError if ``src`` or ``dst`` is not in ``limits`` and ValueError if
    ``src == dst``.

    Example:
        limits = {"A": {"B": 40, "C": 12}, "B": {"A": 40, "C": 30}, "C": {"A": 12, "B": 30}}
        heaviest_route(limits, "A", "C") == (30, ["A", "B", "C"])
    """
    raise NotImplementedError
