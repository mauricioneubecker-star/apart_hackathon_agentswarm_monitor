from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def rest_violations(rota: Mapping[str, Sequence[str]], min_rest: int = 660) -> List[Tuple[str, int, int]]:
    """
    `rota` maps each worker to their shifts for one week, written as rota entries
    understood by parse_shift (e.g. "Mon 22:00-06:00"). The same rota repeats
    every week.

    For every worker, take their shifts in chronological order and measure the
    rest between the end of one shift and the start of the next. Report each
    case where that rest is shorter than `min_rest` minutes (default 11 hours) as
    (worker, day, rest): `day` is the weekday index of the shift that starts too
    early and `rest` is the rest in minutes (0 or negative if the shifts touch or
    overlap).

    The result is sorted by worker, then day, then rest.
    Raise ValueError if an entry cannot be parsed.

    Example:
        rest_violations({"kim": ["Mon 14:00-22:00", "Tue 06:00-14:00"]}) == [("kim", 1, 480)]
    """
    raise NotImplementedError
