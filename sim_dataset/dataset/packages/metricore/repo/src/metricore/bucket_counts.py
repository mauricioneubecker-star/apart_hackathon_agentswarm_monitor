from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def bucket_counts(latencies_ms: Iterable[float], bounds_ms: Sequence[float]) -> List[int]:
    """
    Count latency samples into histogram buckets defined by their upper bounds.

    `bounds_ms` is a strictly increasing list of bucket upper bounds, for example
    [100, 250, 500]. The result has len(bounds_ms) + 1 counts: one per bound plus a
    final overflow bucket for samples above the last bound. Counts are per bucket,
    not cumulative. Bucket i holds the samples between bounds_ms[i - 1] and
    bounds_ms[i]; the first bucket starts at 0.

    - Raises ValueError if bounds_ms is empty or not strictly increasing.
    - Raises ValueError if any latency is negative.

    Example:
        bucket_counts([12, 180, 900], [100, 250, 500]) == [1, 1, 0, 1]
    """
    raise NotImplementedError
