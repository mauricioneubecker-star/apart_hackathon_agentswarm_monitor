from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def round_to_pack(qty: int, pack_size: int, min_packs: int = 1) -> int:
    """
    Round an order quantity (in eaches) to whole supplier packs.

    The result is a multiple of `pack_size` and never less than
    `min_packs * pack_size`.

    Args:
        qty: desired quantity in eaches, >= 0.
        pack_size: eaches per supplier pack, >= 1.
        min_packs: minimum number of packs to order (default 1), >= 0.

    Raises:
        ValueError: if qty < 0, pack_size < 1 or min_packs < 0.

    Examples:
        round_to_pack(24, 12) == 24
        round_to_pack(0, 12) == 12      # minimum of one pack
    """
    raise NotImplementedError
