import pytest

from textkit.slugify import slugify


def test_words_and_symbols():
    assert slugify("  10 Tips & Tricks for C++  ") == "10-tips-tricks-for-c"
    assert slugify("Rock’n’Roll Hall of Fame") == "rocknroll-hall-of-fame"
    assert slugify("!!!") == ""


def test_max_length():
    assert slugify("The quick brown fox", max_length=12) == "the-quick"
    assert slugify("Internationalization guide", max_length=8) == "internationalization"
    assert slugify("a b c", max_length=3) == "a-b"


def test_invalid_length():
    with pytest.raises(ValueError):
        slugify("anything", max_length=0)
