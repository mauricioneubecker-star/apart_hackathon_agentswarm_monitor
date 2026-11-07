from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def lagged_correlation(xs: Sequence[float], ys: Sequence[float], lag: int = 0) -> float:
    """
    Return the Pearson correlation between two metric series, rounded to 3 decimal
    places with metricore's round_half_up.

    Both series are sampled on the same time grid and must have the same length.
    With lag == 0, xs[i] is paired with ys[i]. A non-zero `lag` compares the
    series with a time shift of abs(lag) samples, which is how we check whether,
    say, queue depth follows CPU usage with a delay; only the pairs that overlap
    after the shift are used.

    Over the paired values, r = cov / (std_dev(x) * std_dev(y)) using metricore's
    std_dev, where cov is the covariance computed with the same normalisation as
    std_dev (so a series correlated with itself gives exactly 1.0).

    - Raises ValueError if the lengths differ, if fewer than 2 pairs remain after
      the shift, or if either paired series is constant.

    Example:
        lagged_correlation([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    """
    raise NotImplementedError
