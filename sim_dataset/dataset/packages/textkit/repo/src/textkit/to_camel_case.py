from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def to_camel_case(name: str, upper_first: bool = False) -> str:
    """
    Convert an identifier written in any naming convention to camelCase, or to
    PascalCase when `upper_first` is True.

    The words come from split_identifier(). The first word stays lowercase
    (capitalized when upper_first=True); every following word is capitalized
    (first character upper case, the rest lower case). Words are concatenated
    without separators. Returns "" when there are no words.

    Examples:
        to_camel_case("user_account_id") == "userAccountId"
        to_camel_case("user_account_id", upper_first=True) == "UserAccountId"
    """
    raise NotImplementedError
