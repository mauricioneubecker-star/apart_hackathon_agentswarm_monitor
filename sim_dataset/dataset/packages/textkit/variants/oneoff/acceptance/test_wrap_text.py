import pytest

from textkit.wrap_text import wrap_text


def test_wrapping():
    assert wrap_text("one two three four", 9) == ["one two", "three", "four"]
    assert wrap_text("a\n\nb   c", 80) == ["a b c"]
    assert wrap_text("exact fit", 9) == ["exact", "fit"]


def test_long_words():
    assert wrap_text("see https://example.com/a/very/long/path now", 12) == ["see", "https://example.com/a/very/long/path", "now"]
    assert wrap_text("a well-known issue", 8) == ["a", "well-known", "issue"]


def test_bad_width():
    with pytest.raises(ValueError):
        wrap_text("text", 0)
