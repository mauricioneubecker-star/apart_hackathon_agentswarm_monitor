from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def apdex_score(latencies_ms: Sequence[float], target_ms: float) -> float:
    """
    Compute the Apdex score of a set of request latencies.

    Each request is classified against the target time T = target_ms:

    - satisfied:  the request completed within T
    - tolerating: slower than T, but completed within 4 * T
    - frustrated: everything slower than that

    Apdex = (satisfied + tolerating / 2) / total, rounded to 2 decimal places with
    metricore's round_half_up.

    - Raises ValueError if latencies_ms is empty or target_ms <= 0.

    Example:
        apdex_score([100, 200, 900, 3000], 250) == 0.63
    """
    raise NotImplementedError
