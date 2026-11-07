from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def parse_shift(text: str) -> Tuple[int, int, int]:
    """
    Parse one rota entry of the form "<day> <range>", e.g. "Tue 09:00-17:00",
    into (day, start, end): `day` is the weekday index (0 = Monday ... 6 = Sunday)
    and (start, end) is the result of parse_range on the rest of the text.
    Leading/trailing whitespace is ignored and the day and the range may be
    separated by any amount of whitespace.

    Day names: Mon, Tue, Wed, Thu, Fri, Sat, Sun.
    Raise ValueError for an unknown day, a missing range or an invalid range.

    Example:
        parse_shift("Tue 09:00-17:00") == (1, 540, 1020)
    """
    raise NotImplementedError
