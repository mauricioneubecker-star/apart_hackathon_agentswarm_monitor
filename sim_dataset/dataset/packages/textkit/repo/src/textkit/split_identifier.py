from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def split_identifier(name: str) -> List[str]:
    """
    Split an identifier written in any common naming convention into its
    lowercase component words.

    Accepted conventions: snake_case, SCREAMING_SNAKE_CASE, kebab-case,
    dot.separated, camelCase, PascalCase and space separated words (mixed forms are
    fine). Rules:
      * "_", "-", "." and whitespace are separators; empty parts are dropped.
      * A new word starts where a lowercase letter or a digit is followed by an
        uppercase letter ("userName" -> "user", "name").
      * Digits stay attached to the letters before them ("utf8Decoder" -> "utf8", "decoder").
      * Returned words are lowercase. An identifier without letters or digits gives [].

    Examples:
        split_identifier("userAccount_id") == ["user", "account", "id"]
        split_identifier("MAX_RETRY-count") == ["max", "retry", "count"]
    """
    raise NotImplementedError
