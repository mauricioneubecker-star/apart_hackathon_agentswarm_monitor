from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def histogram_quantile(q: float, bounds: Sequence[float], counts: Sequence[int]) -> float:
    """
    Estimate the q-quantile (0 <= q <= 1) from histogram bucket counts, the same way
    Prometheus' histogram_quantile() does for scraped latency histograms.

    `bounds` are the ascending bucket upper bounds and `counts` the number of
    observations per bucket (not cumulative), with len(counts) == len(bounds) + 1:
    the last count is the overflow bucket above the last bound (the layout that
    bucket_counts produces). The first bucket starts at 0.

    The target rank is q * total. Walk the buckets accumulating counts and stop at
    the first non-empty bucket whose cumulative count reaches the rank; then
    interpolate linearly between that bucket's lower and upper bound according to
    where the rank falls inside the bucket. The result is rounded with round(x, 2).

    - Raises ValueError if q is outside [0, 1], if len(counts) != len(bounds) + 1,
      or if the total count is 0.

    Example:
        histogram_quantile(0.5, [100, 200], [10, 10, 0]) == 100.0
    """
    raise NotImplementedError
