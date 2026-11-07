from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


def readability_score(text: str) -> float:
    """
    Compute the Flesch reading-ease score of `text` for the editor sidebar:

        206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)

    where `words` is the number of tokens returned by tokenize_words(text),
    `sentences` is the number of sentences returned by split_sentences(text), and
    `syllables` is the sum of count_syllables() over all word tokens. The score is
    rounded to 2 decimal places with round(). Text without any word tokens scores 0.0.

    Example:
        readability_score("The committee reviewed the proposal. It approved the budget for next year.") == 59.75
    """
    raise NotImplementedError
