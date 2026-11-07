from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def table_of_contents(markdown: str, max_level: int = 3) -> str:
    """
    Build a Markdown table of contents for a document.

    Headings come from extract_headings(); headings deeper than `max_level` are not
    listed. Each listed heading becomes one line

        "<indent>- [<title>](#<anchor>)"

    where the anchor is slugify(title) and the indent is two spaces per level below
    the shallowest listed level (so the shallowest headings are not indented).
    Headings whose slug is empty are ignored entirely. Lines are joined with "\\n"
    (no trailing newline); returns "" when nothing is listed. Raises ValueError if
    max_level is not between 1 and 6.

    Example:
        table_of_contents("# Guide\\n## Install\\n## Use\\n### CLI\\n")
            == "- [Guide](#guide)\\n  - [Install](#install)\\n  - [Use](#use)\\n    - [CLI](#cli)"
    """
    raise NotImplementedError
