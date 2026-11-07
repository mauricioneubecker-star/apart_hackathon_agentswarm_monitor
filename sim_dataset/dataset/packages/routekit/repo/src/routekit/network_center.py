from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def network_center(adj: Mapping[str, Mapping[str, int]]) -> str:
    """
    Pick the best location for a central depot.

    For every depot, ``hop_distances`` gives the number of roads needed to reach each
    other depot; the depot's eccentricity is the largest of these numbers. Only depots
    that can reach every depot of ``adj`` are candidates. Returns the candidate with the
    smallest eccentricity; ties must be resolved deterministically (independent of dict
    insertion order).

    Raises ValueError if ``adj`` is empty or if no depot can reach all the others.

    Example:
        net = {"A": {"B": 1}, "B": {"A": 1, "C": 1}, "C": {"B": 1, "D": 1}, "D": {"C": 1, "E": 1}, "E": {"D": 1}}
        network_center(net) == "C"
    """
    raise NotImplementedError
