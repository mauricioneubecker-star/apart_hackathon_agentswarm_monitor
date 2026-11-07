from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def parse_edge(line: str) -> Tuple[str, str, int]:
    """
    Parse one road record from a network file.

    A record has the form ``<FROM>-<TO>:<KM>``: two depot codes separated by a hyphen,
    then a colon and the road length in whole kilometres. Whitespace around the record
    and around each of the three parts is ignored. Depot codes are non-empty and consist
    of letters and digits only; the length is a non-negative integer.

    Returns a tuple ``(from_code, to_code, km)``.

    Raises ValueError if the record does not have this shape (missing hyphen or colon,
    empty or non-alphanumeric code, non-integer or negative length).

    Examples:
        parse_edge("BER-HAM:289") == ("BER", "HAM", 289)
        parse_edge("  MUC - NUE : 170 ") == ("MUC", "NUE", 170)
    """
    raise NotImplementedError
