import pytest

from textkit.justify_text import justify_text


def test_gap_distribution():
    assert justify_text("aa bb cc dd ee", 9) == ["aa  bb cc", "dd ee    "]
    assert justify_text("one two three four five", 11)[:2] == ["one     two", "three  four"]


def test_left_aligned_lines():
    assert justify_text("short", 8) == ["short   "]
    assert justify_text("tiny unbelievably big", 8) == ["tiny    ", "unbelievably", "big     "]


def test_invalid_width():
    with pytest.raises(ValueError):
        justify_text("abc", 0)
