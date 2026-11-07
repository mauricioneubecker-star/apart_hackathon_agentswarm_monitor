from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def count_transfers(legs: Sequence[Tuple[str, str, Optional[str]]]) -> int:
    """
    Count how often a shipment changes line along its journey.

    ``legs`` lists the journey in travel order as ``(from_stop, to_stop, line)`` tuples,
    where ``line`` is the id of the truck line operating the leg. Every leg must start
    where the previous one ended.

    A transfer is counted each time the shipment continues on a different line than the
    one it arrived on. An empty journey or a single leg has 0 transfers.

    Raises ValueError if two consecutive legs are not connected
    (``legs[i][1] != legs[i + 1][0]``).

    Example:
        count_transfers([("A", "B", "L1"), ("B", "C", "L1"), ("C", "D", "L4")]) == 1
    """
    raise NotImplementedError
