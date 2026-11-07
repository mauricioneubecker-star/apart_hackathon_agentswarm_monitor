from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def next_credit_note_number(last_number: Optional[str], year: int) -> str:
    """
    Return the number for the next credit note issued in `year`.

    Credit note numbers look like "CN-2024-0042": the prefix "CN", the four-digit year of
    issue and a sequence number zero-padded to at least four digits (after 9999 the number
    simply gets longer, e.g. "CN-2024-10000"). `last_number` is the most recently issued
    credit note number, or None if none has been issued yet (the sequence then starts at 1).

    Raises ValueError if `last_number` is not of this form.

    Examples:
        next_credit_note_number(None, 2024) == "CN-2024-0001"
        next_credit_note_number("CN-2024-0041", 2024) == "CN-2024-0042"
    """
    raise NotImplementedError
