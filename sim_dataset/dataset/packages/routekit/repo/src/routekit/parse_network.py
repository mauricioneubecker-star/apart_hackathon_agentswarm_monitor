from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def parse_network(text: str) -> List[Tuple[str, str, int]]:
    """
    Parse a whole network file into a list of roads.

    Each line holds one road record in the format accepted by ``parse_edge``
    (``<FROM>-<TO>:<KM>``) and is parsed with it. Blank lines (empty or whitespace only)
    and comment lines, whose first non-blank character is ``#``, are skipped. Roads are
    returned in file order; repeated records are kept as they are.

    Raises ValueError if a line cannot be parsed. The message must contain the 1-based
    physical line number in the form ``line N`` (blank and comment lines are counted).

    Example:
        parse_network("# north\\nBER-HAM:289\\n\\nHAM-KIE:96") == [("BER", "HAM", 289), ("HAM", "KIE", 96)]
    """
    raise NotImplementedError
