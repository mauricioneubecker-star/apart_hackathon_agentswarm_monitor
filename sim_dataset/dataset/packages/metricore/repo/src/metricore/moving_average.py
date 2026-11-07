from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def moving_average(values: Sequence[float], window: int) -> List[float]:
    """
    Return the trailing simple moving average of `values`.

    Each output point is the arithmetic mean of a window of `window` consecutive
    input values ending at the corresponding input position (a trailing window,
    so no future values are used). Results are floats rounded with round(x, 2).

    - window must be >= 1, otherwise ValueError is raised.
    - An empty input returns [].

    Example:
        moving_average([2, 4, 6, 8], 2)[-1] == 7.0
    """
    raise NotImplementedError
