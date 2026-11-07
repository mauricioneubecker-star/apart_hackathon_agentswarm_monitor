from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def normalize_whitespace(text: str) -> str:
    """
    Collapse every run of whitespace in `text` into a single ASCII space and
    strip leading and trailing whitespace.

    "Whitespace" means any character for which str.isspace() is true: spaces, tabs,
    newlines, non-breaking spaces (U+00A0), em spaces and so on. This is the first
    cleanup step applied to titles, excerpts and user-submitted copy.

    Examples:
        normalize_whitespace("  Hello \\t\\n world  ") == "Hello world"
        normalize_whitespace("") == ""
    """
    raise NotImplementedError
