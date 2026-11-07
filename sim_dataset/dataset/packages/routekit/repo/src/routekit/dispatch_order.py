from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def dispatch_order(prereqs: Mapping[str, Iterable[str]]) -> List[str]:
    """
    Order loading jobs so that every job comes after its prerequisites.

    ``prereqs`` maps a job id to the ids of the jobs that must be dispatched before it.
    Ids that only appear as prerequisites are jobs as well (with no prerequisites of
    their own). Returns every job exactly once, each one after all of its
    prerequisites. When several jobs could go next, the choice must be deterministic:
    the result must not depend on dict insertion order.

    Raises ValueError if the prerequisites are circular (including a job that requires
    itself).

    Example:
        dispatch_order({"PACK": ["PICK"], "SHIP": ["PACK", "LABEL"]}) == ["LABEL", "PICK", "PACK", "SHIP"]
    """
    raise NotImplementedError
