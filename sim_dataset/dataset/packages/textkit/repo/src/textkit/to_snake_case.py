from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def to_snake_case(name: str) -> str:
    """
    Convert an identifier written in any naming convention to snake_case.

    The words are obtained with split_identifier() and joined with "_" (so the
    result is all lowercase). Returns "" when the input has no words.

    Examples:
        to_snake_case("userAccountId") == "user_account_id"
        to_snake_case("Content-Type") == "content_type"
    """
    raise NotImplementedError
