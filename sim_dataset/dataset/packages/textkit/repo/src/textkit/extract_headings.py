from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def extract_headings(markdown: str) -> List[Tuple[int, str]]:
    """
    List the ATX headings of a Markdown document as (level, title) pairs, in
    document order.

    A heading line has at most 3 leading spaces, then 1-6 "#" characters, then
    either the end of the line or at least one space/tab followed by the title.
    The title has surrounding whitespace removed, and an optional closing run of
    "#" characters is dropped when it is preceded by a space or is the whole title.
    "#hashtag" (no space) and "####### seven" are not headings; a bare "#" is a
    level-1 heading with an empty title. Lines are split with str.splitlines().

    Example:
        extract_headings("# Intro\\ntext\\n## Setup ##\\n") == [(1, "Intro"), (2, "Setup")]
    """
    raise NotImplementedError
