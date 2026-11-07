from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def format_route(stops: Sequence[str], km: Optional[int] = None) -> str:
    """
    Render a route for dispatch sheets.

    The depot codes in ``stops`` are joined with ``" > "``. If ``km`` is given (it may
    be 0), ``" (<km> km)"`` is appended.

    Raises ValueError if ``stops`` is empty.

    Examples:
        format_route(["BER", "HAM", "KIE"]) == "BER > HAM > KIE"
        format_route(["BER", "HAM", "KIE"], 385) == "BER > HAM > KIE (385 km)"
    """
    raise NotImplementedError
