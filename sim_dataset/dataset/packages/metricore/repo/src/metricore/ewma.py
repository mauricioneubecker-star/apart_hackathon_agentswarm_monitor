from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def ewma(values: Sequence[float], span: int) -> List[float]:
    """
    Return the exponentially weighted moving average (EWMA) of `values`.

    The smoothing factor alpha (0 < alpha <= 1) is derived from `span`, the
    number of recent samples the average roughly reflects; a larger span reacts
    more slowly. The series is seeded with the first observation and then
    updated recursively:

        s[0] = values[0]
        s[t] = alpha * values[t] + (1 - alpha) * s[t - 1]

    The result has the same length as `values`; every element is a float rounded
    with round(x, 4).

    - span must be >= 1, otherwise ValueError is raised.
    - An empty input returns [].

    Example:
        ewma([10, 10, 10], 5) == [10.0, 10.0, 10.0]
    """
    raise NotImplementedError
