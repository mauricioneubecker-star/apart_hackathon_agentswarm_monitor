import pytest

from textkit.truncate_text import truncate_text


def test_word_boundaries():
    assert truncate_text("  Breaking   news from the\ncity council ", 20) == "Breaking news..."
    assert truncate_text("exactly ten", 11) == "exactly ten"
    assert truncate_text("Supercalifragilistic word", 10) == "Superca..."


def test_punctuation_at_cut():
    assert truncate_text("Hello, world and everyone else", 12) == "Hello..."
    assert truncate_text("Fast, cheap; reliable - pick two", 20, ellipsis=" [more]") == "Fast, cheap [more]"


def test_budget_too_small():
    with pytest.raises(ValueError):
        truncate_text("abc", 3)
