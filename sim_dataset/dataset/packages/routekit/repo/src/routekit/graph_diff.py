from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def graph_diff(old_lines: Sequence[str], new_lines: Sequence[str]) -> Dict[str, List[Tuple[str, str, int]]]:
    """
    Compare two versions of a road list.

    Both arguments are lists of road records in the ``parse_edge`` format and every
    record is parsed with ``parse_edge``. A road is identified by its pair of depots;
    each list mentions a road at most once. Returns a dict with three keys:

    * ``"added"``: roads present only in ``new_lines`` (with their new km),
    * ``"removed"``: roads present only in ``old_lines`` (with their old km),
    * ``"changed"``: roads present in both with a different km, reported with the new km.

    Each list holds ``(from_code, to_code, km)`` tuples sorted by ``(from_code, to_code)``.
    Raises ValueError (from ``parse_edge``) if a record is malformed.

    Example:
        graph_diff(["BER-HAM:289", "BER-LEI:190"], ["BER-HAM:289", "BER-LEI:185", "DRE-PRG:150"])
            == {"added": [("DRE", "PRG", 150)], "removed": [], "changed": [("BER", "LEI", 185)]}
    """
    raise NotImplementedError
