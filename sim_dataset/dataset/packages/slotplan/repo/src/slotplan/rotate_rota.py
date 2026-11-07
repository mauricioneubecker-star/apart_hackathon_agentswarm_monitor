from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def rotate_rota(staff: Sequence[str], n_days: int, per_day: int, first_day: int = 0) -> List[List[str]]:
    """
    Build a front-desk rota for `n_days` consecutive calendar days, the first of
    which has weekday index `first_day` (0 = Monday ... 6 = Sunday).

    Each day gets `per_day` people taken from `staff` in round-robin order: the
    first day starts with staff[0] and every following day continues with the
    person after the last one used, wrapping around to the start of the list.
    Returns one list of names per calendar day, in the order they were picked.

    Raise ValueError if staff is empty, per_day < 1, per_day > len(staff),
    n_days < 0 or first_day is not in 0..6.

    Example:
        rotate_rota(["ana", "ben", "cy"], 2, 2) == [["ana", "ben"], ["cy", "ana"]]
    """
    raise NotImplementedError
