from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def isolated_by_closures(edges: Iterable[Tuple[str, str, int]], depot: str, closed: Iterable[Tuple[str, str]], directed: bool = False) -> List[str]:
    """
    List the depots that ``depot`` can no longer reach once some roads are closed.

    The network is built from ``edges`` with ``build_adjacency`` (``directed`` as given)
    and reachability is computed with ``hop_distances``. ``closed`` lists road closures
    as ``(from_code, to_code)`` pairs in the same notation as the road records; matching
    road records are removed before the reduced network is built. Closures that match no
    road are ignored.

    Returns the alphabetically sorted codes of the depots that are reachable from
    ``depot`` in the full network but not in the reduced one. ``depot`` always counts as
    reachable from itself, even if all of its roads are closed.

    Raises KeyError if ``depot`` does not appear in ``edges``.

    Example:
        roads = [("BER", "HAM", 289), ("HAM", "KIE", 96), ("BER", "LEI", 190)]
        isolated_by_closures(roads, "BER", [("BER", "HAM")]) == ["HAM", "KIE"]
    """
    raise NotImplementedError
