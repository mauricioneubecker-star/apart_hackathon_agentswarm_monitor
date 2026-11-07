from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def extract_invoice_refs(memo: str) -> List[str]:
    """
    Find invoice references in a free-text bank memo and return them in canonical
    form.

    A reference is the letters "INV" (any case), optionally followed by one separator
    character ('-', '#' or a single space), followed by 1 to 6 digits. The "INV" must not be
    preceded by a letter or digit, and the digits must not be followed by another digit.
    The canonical form is "INV-" plus the number zero-padded to 6 digits.

    References are returned in the order they appear in the memo; [] if there are none.

    Example:
        extract_invoice_refs("Payment inv 42 and INV-000107") == ["INV-000042", "INV-000107"]
    """
    raise NotImplementedError
