from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def join_human(items: Sequence[Any], conjunction: str = "and") -> str:
    """
    Join `items` into a human-readable English list for UI copy such as
    "Liked by Ana, Ben and 3 others".

      * no items -> ""
      * one item -> that item
      * two items -> "A and B"
      * three or more -> the items separated by ", ", with the conjunction placed
        before the last item

    Items are converted with str() and used as-is (no trimming). `conjunction`
    replaces "and", e.g. conjunction="or".

    Examples:
        join_human(["tea"]) == "tea"
        join_human(["tea", "coffee"], conjunction="or") == "tea or coffee"
    """
    raise NotImplementedError
