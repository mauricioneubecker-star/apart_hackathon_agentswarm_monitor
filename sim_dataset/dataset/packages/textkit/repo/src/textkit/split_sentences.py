from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def split_sentences(text: str) -> List[str]:
    """
    Split prose into sentences.

    The text is first cleaned with normalize_whitespace() and then split into
    space-separated words. A word ends a sentence when:
      * it ends with a terminator run of ".", "!" or "?" (e.g. "...", "?!"),
        optionally followed by closing quotes or brackets (" ' ) ]), and
      * the next word starts with an uppercase letter, a digit, or an opening
        quote/bracket (" ' ( [).
    Words that are one of these abbreviations never end a sentence (exact,
    case-sensitive match): Mr. Mrs. Ms. Dr. Prof. St. vs. e.g. i.e.
    Whatever follows the last boundary is the final sentence. Each sentence is
    its words joined by single spaces; sentences are returned in order, and empty
    input gives [].

    Examples:
        split_sentences("Hello there. How are you? Fine!") == ["Hello there.", "How are you?", "Fine!"]
        split_sentences("Ask Dr. Smith. He knows.") == ["Ask Dr. Smith.", "He knows."]
    """
    raise NotImplementedError
