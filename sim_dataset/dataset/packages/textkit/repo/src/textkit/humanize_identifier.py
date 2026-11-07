from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def humanize_identifier(name: str) -> str:
    """
    Turn a field or column identifier into a human-readable label for admin
    screens and CSV headers.

    The words come from split_identifier(). The label is the words joined by single
    spaces, with the first word capitalized and the remaining words lowercase.
    Words in the acronym set {"api", "id", "url", "html", "http", "json", "sql",
    "uuid"} are written fully uppercase wherever they appear. Returns "" for an
    identifier without words.

    Examples:
        humanize_identifier("createdAt") == "Created at"
        humanize_identifier("api_key") == "API key"
    """
    raise NotImplementedError
