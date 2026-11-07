from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def subtract_intervals(base: Iterable[Tuple[int, int]], remove: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Return the parts of `base` that are not covered by any interval in `remove`,
    as (start, end) tuples sorted by start time.

    `remove` may be unsorted and overlapping (normalise it with merge_intervals);
    parts of `remove` that fall outside `base` have no effect. Removing everything
    yields an empty list. The inputs are not modified.

    Example:
        subtract_intervals([(540, 1020)], [(600, 660), (900, 960)])
            == [(540, 600), (660, 900), (960, 1020)]
    """
    raise NotImplementedError
