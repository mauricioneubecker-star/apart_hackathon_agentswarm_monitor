from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def paid_hours(rota: Mapping[str, Sequence[str]]) -> Dict[str, str]:
    """
    Compute each worker's paid working time for one week of rota entries
    (parsed with parse_shift) and return it formatted with format_duration, e.g.
    {"kim": "38h 30m"}. Every worker in `rota` appears in the result; a worker
    with no shifts gets "0m".

    Raise ValueError if an entry cannot be parsed.

    Example:
        paid_hours({"kim": ["Mon 09:00-13:00", "Tue 13:00-17:30"]}) == {"kim": "8h 30m"}
    """
    raise NotImplementedError
