from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def validate_route(adj: Mapping[str, Mapping[str, int]], stops: Sequence[str], max_legs: Optional[int] = None) -> List[str]:
    """
    Check a planned route against the network and list its problems.

    Returns a list of messages (empty if the route is fine):

    * ``"empty route"`` if ``stops`` is empty (no other checks are made);
    * ``"unknown depot X"`` for a stop ``X`` that is not a key of ``adj``;
    * ``"no road A-B"`` when consecutive stops ``A`` and ``B`` are not joined by a road
      (``B`` not in ``adj[A]``);
    * finally ``"too many legs: N > M"`` if ``max_legs`` is given and the route has
      ``N = len(stops) - 1`` legs with ``N > M``.

    The route is walked stop by stop: for each stop the unknown-depot check comes
    first, then (from the second stop on) the road check for the leg arriving at it.
    A single stop is a valid route.

    Example:
        net = {"A": {"B": 4}, "B": {"A": 4, "C": 6}, "C": {"B": 6}}
        validate_route(net, ["A", "C", "B"]) == ["no road A-C"]
    """
    raise NotImplementedError
