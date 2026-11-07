from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def split_meeting(start: int, end: int, max_block: int, break_len: int = 0) -> List[Tuple[int, int]]:
    """
    Split the session [start, end) into consecutive working blocks of at most
    `max_block` minutes, separated by breaks of `break_len` minutes. The first
    block starts at `start` and the last block ends exactly at `end`: breaks are
    taken out of the session time, the session is never extended. The smallest
    possible number of blocks is used, and a session that fits in a single block
    is returned unchanged as [(start, end)].

    Returns the blocks as (start, end) tuples in order.
    Raise ValueError if end <= start, max_block <= 0 or break_len < 0.

    Examples:
        split_meeting(540, 720, 90) == [(540, 630), (630, 720)]
        split_meeting(540, 750, 60, 15) == [(540, 600), (615, 675), (690, 750)]
    """
    raise NotImplementedError
