from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def align_to_grid(minute: int, step: int = 15, mode: str = "nearest") -> int:
    """
    Snap `minute` onto the grid of multiples of `step` minutes.

    `mode` is one of:
        "floor"   - the closest grid point at or before `minute`
        "ceil"    - the closest grid point at or after `minute`
        "nearest" - whichever grid point is closer to `minute`

    Values already on the grid are returned unchanged. Negative minutes are allowed
    and follow the same rules. Raise ValueError if step <= 0 or mode is not one of
    the names above.

    Examples:
        align_to_grid(608) == 615
        align_to_grid(608, 15, "floor") == 600
    """
    raise NotImplementedError
