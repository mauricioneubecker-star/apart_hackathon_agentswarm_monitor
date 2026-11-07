from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def normalize_sku(code: str) -> str:
    """
    Validate a SKU code and return it in canonical form.

    Canonical SKUs look like "ABC-123456-1": a three-letter category prefix
    (A-Z), a hyphen, a six-digit item number, a hyphen and one check digit.
    Input may use any letter case and may carry surrounding whitespace.

    Check digit: weight the six item digits 3,1,3,1,3,1 from left to right,
    sum the products and take (10 - sum % 10) % 10.

    Args:
        code: SKU as typed or scanned.

    Returns:
        The canonical, upper-case SKU string.

    Raises:
        ValueError: if the code is malformed or the check digit is wrong.

    Examples:
        normalize_sku(" abc-123456-1 ") == "ABC-123456-1"
        normalize_sku("ABC-123456-2")   -> ValueError (check digit should be 1)
    """
    raise NotImplementedError
