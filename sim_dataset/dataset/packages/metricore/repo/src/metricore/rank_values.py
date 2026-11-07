from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def rank_values(values: Sequence[float]) -> List[int]:
    """
    Return the rank of each element of `values`, where rank 1 is the largest value.

    The result is aligned with the input: result[i] is the rank of values[i]. Equal
    values share the same rank. Used to rank services by error count or latency in
    the weekly reliability report.

    - An empty input returns [].

    Example:
        rank_values([30, 10, 20]) == [1, 3, 2]
    """
    raise NotImplementedError
