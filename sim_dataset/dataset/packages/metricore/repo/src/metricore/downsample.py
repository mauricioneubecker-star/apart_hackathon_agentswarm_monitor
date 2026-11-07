from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def downsample(points: Sequence[Tuple[int, float]], bucket_seconds: int, agg: str = "mean") -> List[Tuple[int, float]]:
    """
    Downsample (timestamp, value) points into fixed-width time buckets.

    `points` are (epoch_seconds, value) pairs and are not necessarily sorted.
    Points are grouped into buckets that are `bucket_seconds` wide, and each
    bucket is reduced with `agg`:

    - "mean": arithmetic mean of the values, rounded with round(x, 2)
    - "max":  largest value
    - "sum":  sum of the values
    - "last": value of the point with the latest timestamp in the bucket

    Returns a list of (bucket_start, aggregated_value) tuples sorted by
    bucket_start, where bucket_start is the first second covered by the bucket.
    Buckets without points are omitted.

    - Raises ValueError if bucket_seconds < 1 or `agg` is not one of the above.
    - An empty input returns [].

    Example:
        downsample([(0, 1.0), (30, 3.0), (60, 5.0)], 60) == [(0, 2.0), (60, 5.0)]
    """
    raise NotImplementedError
