from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def slugify(text: str, max_length: Optional[int] = None) -> str:
    """
    Build a URL slug from a title.

    The text is split into words with tokenize_words(). Each word is reduced to
    ASCII by stripping diacritics (Unicode NFKD decomposition, then dropping
    non-ASCII characters), after which any remaining character other than a-z and
    0-9 is removed; words that end up empty are discarded. The remaining words are
    joined with "-", so the slug only contains a-z, 0-9 and "-".

    If `max_length` is given, the slug is shortened to at most max_length
    characters and never ends with "-". Raises ValueError if max_length is given
    and is < 1.

    Examples:
        slugify("Hello, World!") == "hello-world"
        slugify("Crème Brûlée Recipes") == "creme-brulee-recipes"
        slugify("50% off: Summer Sale") == "50-off-summer-sale"
    """
    raise NotImplementedError
