from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def critical_roads(edges: Iterable[Tuple[str, str, int]]) -> List[Tuple[str, str]]:
    """
    Find the roads whose closure would cut a region in two.

    Roads are undirected and the network is built with ``build_adjacency``. A road
    between depots ``a`` and ``b`` is critical if, once it is closed, ``b`` can no
    longer be reached from ``a``. Self-loops are never critical. Networks are small (a
    few dozen roads), so checking each road separately is fine.

    Returns the critical roads as ``(code_a, code_b)`` pairs with ``code_a < code_b``,
    sorted, each road listed once.

    Example:
        critical_roads([("A", "B", 1), ("B", "C", 1), ("C", "A", 1), ("C", "D", 4)]) == [("C", "D")]
    """
    raise NotImplementedError
